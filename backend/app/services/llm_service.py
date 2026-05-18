import logging
import re
from typing import Any

from google import genai

from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """Service for Gemini LLM API integration for text-to-SQL generation and result summarization."""

    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_MODEL_NAME

    def _get_schema_ddl(self) -> str:
        """Get the DDL for all tables to inject into the system prompt."""
        return """
CREATE TABLE campaigns (
    id TEXT PRIMARY KEY,
    name TEXT,
    status TEXT,
    objective TEXT,
    daily_budget NUMERIC,
    lifetime_budget NUMERIC,
    created_time TIMESTAMP,
    start_time TIMESTAMP,
    stop_time TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE ad_sets (
    id TEXT PRIMARY KEY,
    campaign_id TEXT REFERENCES campaigns(id),
    name TEXT,
    status TEXT,
    daily_budget NUMERIC,
    lifetime_budget NUMERIC,
    targeting JSONB,
    bid_strategy TEXT,
    created_time TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE ads (
    id TEXT PRIMARY KEY,
    ad_set_id TEXT REFERENCES ad_sets(id),
    name TEXT,
    status TEXT,
    creative JSONB,
    created_time TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE insights (
    id TEXT PRIMARY KEY,
    ad_id TEXT REFERENCES ads(id),
    date DATE NOT NULL,
    impressions INTEGER,
    clicks INTEGER,
    spend NUMERIC,
    reach INTEGER,
    frequency NUMERIC,
    ctr NUMERIC,
    cpc NUMERIC,
    cpm NUMERIC,
    conversions INTEGER,
    conversion_value NUMERIC,
    UNIQUE(ad_id, date),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
"""

    def _get_example_queries(self) -> str:
        """Get example queries for few-shot learning."""
        return """
Example 1:
User: "What was our total spend last month?"
SQL: SELECT SUM(spend) AS total_spend FROM insights WHERE date >= CURRENT_DATE - INTERVAL '1 month';

Example 2:
User: "Show me the top 5 campaigns by impressions this week"
SQL: SELECT c.name, SUM(i.impressions) AS total_impressions 
       FROM insights i 
       JOIN ads a ON i.ad_id = a.id 
       JOIN ad_sets ad ON a.ad_set_id = ad.id 
       JOIN campaigns c ON ad.campaign_id = c.id 
       WHERE i.date >= CURRENT_DATE - INTERVAL '1 week'
       GROUP BY c.name 
       ORDER BY total_impressions DESC 
       LIMIT 5;

Example 3:
User: "Which ad set has the highest CTR?"
SQL: SELECT ad.name AS ad_set_name, AVG(i.ctr) AS average_ctr 
       FROM insights i 
       JOIN ads a ON i.ad_id = a.id 
       JOIN ad_sets ad ON a.ad_set_id = ad.id 
       GROUP BY ad.name 
       ORDER BY average_ctr DESC 
       LIMIT 1;

Example 4:
User: "Get daily conversions for campaign 'Summer Sale' for the last 7 days"
SQL: SELECT i.date, SUM(i.conversions) AS daily_conversions 
       FROM insights i 
       JOIN ads a ON i.ad_id = a.id 
       JOIN ad_sets ad ON a.ad_set_id = ad.id 
       JOIN campaigns c ON ad.campaign_id = c.id 
       WHERE c.name = 'Summer Sale' 
         AND i.date >= CURRENT_DATE - INTERVAL '7 days'
       GROUP BY i.date 
       ORDER BY i.date;
"""

    def _build_system_prompt(self) -> str:
        """Build the system prompt with role definition, schema injection, and constraints."""
        role_definition = """You are a Meta Ads data analyst with PostgreSQL access to campaigns, ad_sets, ads, and insights tables. Your expertise is in converting natural language questions about advertising performance into accurate SQL queries."""

        schema_injection = f"""Database Schema:
{self._get_schema_ddl()}"""

        constraints = """Constraints:
1. Generate ONLY SELECT queries (WITH clauses allowed for CTEs)
2. Never generate DDL, DML, or transaction control statements
3. Use ONLY column names from the provided schema
4. Limit results to reasonable amounts (use LIMIT when appropriate)
5. If the question is ambiguous, ask for clarification rather than guessing
6. If data doesn't exist for the query, say so honestly
7. Summarize results in 1-2 sentences with proper currency formatting for monetary values
8. Focus on advertising metrics: spend, impressions, clicks, conversions, CTR, CPC, CPM, reach, frequency"""

        return f"""{role_definition}

{schema_injection}

{self._get_example_queries()}

{constraints}"""

    async def generate_sql(self, user_query: str) -> dict[str, Any]:
        """
        Generate SQL from user query using Gemini.
        
        Returns:
            Dict with keys: success (bool), sql (str), error (str)
        """
        try:
            system_prompt = self._build_system_prompt()

            # Combine system prompt and user query
            full_prompt = f"{system_prompt}\n\nUser Question: {user_query}\n\nSQL Query:"

            # Generate content
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
            )
            generated_text = response.text.strip()

            # Extract SQL from response (handle potential markdown formatting)
            sql_match = re.search(r'```sql\n(.*?)\n```', generated_text, re.DOTALL)
            if sql_match:
                sql = sql_match.group(1).strip()
            else:
                # Try to extract SQL without markdown
                lines = generated_text.split('\n')
                sql_lines = []
                in_sql = False
                for line in lines:
                    if line.strip().upper().startswith('SELECT') or line.strip().upper().startswith('WITH'):
                        in_sql = True
                    if in_sql:
                        sql_lines.append(line)
                        if line.strip().endswith(';') or line.strip() == '':
                            break
                sql = '\n'.join(sql_lines).strip()

                # Remove trailing semicolon if present
                if sql.endswith(';'):
                    sql = sql[:-1]

            # Basic validation - ensure it starts with SELECT or WITH
            sql_upper = sql.strip().upper()
            if not (sql_upper.startswith('SELECT') or sql_upper.startswith('WITH')):
                return {
                    "success": False,
                    "sql": "",
                    "error": "Generated SQL does not start with SELECT or WITH"
                }

            return {
                "success": True,
                "sql": sql,
                "error": ""
            }

        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}")
            return {
                "success": False,
                "sql": "",
                "error": f"Failed to generate SQL: {str(e)}"
            }

    async def summarize_results(self, user_query: str, sql: str, query_results: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Summarize query results using Gemini.
        
        Returns:
            Dict with keys: success (bool), summary (str), error (str)
        """
        try:
            if not query_results:
                return {
                    "success": True,
                    "summary": "No data found for your query. Try a different date range or campaign.",
                    "error": ""
                }

            # Format results for the prompt
            results_text = f"Query Results ({len(query_results)} rows):\n"
            for i, row in enumerate(query_results[:5]):  # Show first 5 rows
                results_text += f"Row {i+1}: {row}\n"

            if len(query_results) > 5:
                results_text += f"... and {len(query_results) - 5} more rows\n"

            system_prompt = """You are a Meta Ads data analyst. Your task is to convert query results into a clear, concise summary in 1-2 sentences. Focus on the key insights and use appropriate formatting (currency for monetary values, percentages for rates, etc.). Be honest about limitations in the data."""

            full_prompt = f"""{system_prompt}

User's Original Question: {user_query}

Generated SQL: {sql}

{results_text}

Provide a brief summary (1-2 sentences) of what the data shows in response to the user's question."""

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
            )
            summary = response.text.strip()

            return {
                "success": True,
                "summary": summary,
                "error": ""
            }

        except Exception as e:
            logger.error(f"Error summarizing results: {str(e)}")
            return {
                "success": False,
                "summary": "",
                "error": f"Failed to summarize results: {str(e)}"
            }


# Singleton instance
llm_service = LLMService()
