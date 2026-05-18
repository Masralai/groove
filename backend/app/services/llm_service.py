import hashlib
import re
from typing import Any

import httpx

from app.core.config import settings
from app.core.fd_logger import FdLogger

logger = FdLogger("app.services.llm_service")

_CACHE_MAX_SIZE = 50


class LLMService:
    """LLM API service for text-to-SQL and result summarization.

    Supports OpenRouter (remote) and LM Studio (local) via
    the ``LLM_PROVIDER`` setting.
    """

    def __init__(self):
        self._sql_cache: dict[str, dict[str, Any]] = {}

    # ── Provider helpers ────────────────────────────────────────────────

    @staticmethod
    def _provider_label() -> str:
        return "LM Studio" if settings.LLM_PROVIDER == "lmstudio" else "OpenRouter"

    @staticmethod
    def _provider_config() -> dict[str, str]:
        """Return ``{base_url, model_name, auth_header}`` for the active provider."""
        if settings.LLM_PROVIDER == "lmstudio":
            return {
                "base_url": settings.LMSTUDIO_BASE_URL,
                "model_name": settings.LMSTUDIO_MODEL,
                "auth_header": "",
            }
        return {
            "base_url": settings.OPENROUTER_BASE_URL,
            "model_name": settings.OPENROUTER_MODEL,
            "auth_header": f"Bearer {settings.OPENROUTER_API_KEY}",
        }

    # ── Cache helpers ───────────────────────────────────────────────────

    def _cache_key(self, user_query: str) -> str:
        normalized = user_query.strip().lower()
        normalized = re.sub(r'\s+', ' ', normalized)
        return hashlib.sha256(normalized.encode()).hexdigest()

    def _cache_get(self, user_query: str) -> dict[str, Any] | None:
        key = self._cache_key(user_query)
        return self._sql_cache.get(key)

    def _cache_set(self, user_query: str, result: dict[str, Any]):
        key = self._cache_key(user_query)
        self._sql_cache[key] = result
        if len(self._sql_cache) > _CACHE_MAX_SIZE:
            oldest = next(iter(self._sql_cache))
            del self._sql_cache[oldest]

    # ── LLM call ────────────────────────────────────────────────────────

    @staticmethod
    def _is_quota_error(status_code: int, body: dict) -> tuple[bool, int]:
        if status_code == 429:
            return True, 60
        error_str = str(body).lower()
        if "quota" in error_str or "rate limit" in error_str or "429" in error_str:
            return True, 60
        return False, 0

    async def _call_llm(
        self, user_query: str, system_prompt: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Make a request to the configured LLM provider's chat completions endpoint."""
        cfg = self._provider_config()
        provider = self._provider_label()
        model_name = model or cfg["model_name"]

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_query})

        headers = {"Content-Type": "application/json"}
        if cfg["auth_header"]:
            headers["Authorization"] = cfg["auth_header"]

        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.1,
        }

        logger.info(
            f"Calling {provider} model={model_name}"
            f" system={len(system_prompt or '')} chars query={len(user_query)} chars"
        )

        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{cfg['base_url']}/chat/completions",
                headers=headers,
                json=payload,
            )

        if response.status_code != 200:
            try:
                body = response.json()
            except Exception:
                body = {}

            _body_str = str(body)[:300]
            logger.warning(
                f"{provider} API error: status={response.status_code} body={_body_str}"
            )

            # Only OpenRouter has quota/rate-limit errors
            if provider == "OpenRouter":
                is_quota, retry_after = self._is_quota_error(response.status_code, body)
                if is_quota:
                    return {
                        "success": False,
                        "error_type": "quota_exceeded",
                        "retry_after": retry_after,
                        "error": (
                            f"AI service rate limited (HTTP {response.status_code})."
                            " Try again later."
                        ),
                    }

            return {
                "success": False,
                "error_type": "api_error",
                "retry_after": 0,
                "error": (
                    f"API returned HTTP {response.status_code}:"
                    f" {body.get('error', {}).get('message', 'unknown error')}"
                ),
            }

        data = response.json()
        try:
            text = data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, AttributeError) as e:
            logger.error(f"Unexpected {provider} response format: {e} data={str(data)[:200]}")
            return {"success": False, "error_type": "api_error", "retry_after": 0,
                    "error": f"Unexpected API response format: {e}"}

        logger.info(
            f"{provider} response: status={response.status_code}"
            f" len={len(text)} preview={text[:200]}"
        )

        return {"success": True, "text": text}

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
        role_definition = (
            "You are a Meta Ads data analyst with PostgreSQL access to campaigns,"
            " ad_sets, ads, and insights tables. Your expertise is in converting"
            " natural language questions about advertising performance into"
            " accurate SQL queries."
        )

        schema_injection = f"""Database Schema:
{self._get_schema_ddl()}"""

        constraints = (
            "Constraints:\n"
            "1. Generate ONLY SELECT queries (WITH clauses allowed for CTEs)\n"
            "2. Never generate DDL, DML, or transaction control statements\n"
            "3. Use ONLY column names from the provided schema\n"
            "4. Limit results to reasonable amounts (use LIMIT when appropriate)\n"
            "5. If the question is ambiguous, ask for clarification rather than guessing\n"
            "6. If data doesn't exist for the query, say so honestly\n"
            "7. Summarize results in 1-2 sentences with proper currency"
            " formatting for monetary values\n"
            "8. Focus on advertising metrics: spend, impressions, clicks,"
            " conversions, CTR, CPC, CPM, reach, frequency\n"
            "9. The schema has NO platform/positioning column. You MUST still"
            " generate a SQL query even for impossible questions."
            " For 'Facebook vs Instagram'-like questions return:"
            " SELECT 'Schema has no platform column — cannot compare platforms.' AS message"
        )

        return f"""{role_definition}

{schema_injection}

{self._get_example_queries()}

{constraints}"""

    async def generate_sql(self, user_query: str, use_cache: bool = True) -> dict[str, Any]:
        """
        Generate SQL from user query using LLM.

        Results are cached by normalized query to avoid redundant API calls.

        Args:
            user_query: The natural language query.
            use_cache: Whether to check/write the cache. Set to ``False`` for
                       repair/retry prompts so the LLM is called fresh.

        Returns:
            Dict with keys: success (bool), sql (str), error (str),
            error_type (str), retry_after (int)
        """
        if use_cache:
            cached = self._cache_get(user_query)
            if cached is not None:
                logger.info(f"SQL cache hit for query: {user_query[:60]}")
                return dict(cached)

        system_prompt = self._build_system_prompt()

        result = await self._call_llm(user_query, system_prompt=system_prompt)
        if not result["success"]:
            return result

        generated_text = result["text"]

        # Extract SQL from response (handle potential markdown formatting)
        sql_match = re.search(r'```sql\n(.*?)\n```', generated_text, re.DOTALL)
        if sql_match:
            sql = sql_match.group(1).strip().rstrip(';').strip()
        else:
            lines = generated_text.split('\n')
            sql_lines = []
            in_sql = False
            for line in lines:
                stripped = line.strip().upper()
                if stripped.startswith('SELECT') or stripped.startswith('WITH'):
                    in_sql = True
                if in_sql:
                    sql_lines.append(line)
                    if line.strip().endswith(';'):
                        break
            sql = '\n'.join(sql_lines).strip()
            if sql.endswith(';'):
                sql = sql[:-1]

        sql_upper = sql.strip().upper()
        if not (sql_upper.startswith('SELECT') or sql_upper.startswith('WITH')):
            logger.warning(
                f"LLM response did not contain SELECT/WITH."
                f" Raw response (first 500 chars): {generated_text[:500]}"
            )
            output = {
                "success": False,
                "sql": "",
                "error": "Generated SQL does not start with SELECT or WITH",
                "error_type": "invalid_sql",
                "retry_after": 0,
            }
            return output

        output = {
            "success": True,
            "sql": sql,
            "error": "",
            "error_type": "",
            "retry_after": 0,
        }
        if use_cache:
            self._cache_set(user_query, output)
        return output

    async def summarize_results(
        self, user_query: str, sql: str, query_results: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Summarize query results using LLM.

        Falls back to a template summary if the API call fails.

        Returns:
            Dict with keys: success (bool), summary (str), error (str),
            error_type (str), retry_after (int)
        """
        if not query_results:
            return {
                "success": True,
                "summary": "No data found for your query.",
                "error": "",
                "error_type": "",
                "retry_after": 0,
            }

        results_text = f"Query Results ({len(query_results)} rows):\n"
        for i, row in enumerate(query_results[:5]):
            results_text += f"Row {i+1}: {row}\n"
        if len(query_results) > 5:
            results_text += f"... and {len(query_results) - 5} more rows\n"

        system_prompt = (
            "You are a Meta Ads data analyst. Summarize the query results"
            " in 1-2 sentences."
        )
        user_prompt = (
            f"User's Question: {user_query}\nSQL:"
            f" {sql}\n{results_text}\nSummary:"
        )

        result = await self._call_llm(user_prompt, system_prompt=system_prompt)
        if not result["success"]:
            return {
                "success": False,
                "summary": f"Found {len(query_results)} results. See data below.",
                "error": result.get("error", "Summary generation failed"),
                "error_type": result.get("error_type", "api_error"),
                "retry_after": result.get("retry_after", 0),
            }

        return {
            "success": True,
            "summary": result["text"],
            "error": "",
            "error_type": "",
            "retry_after": 0,
        }


llm_service = LLMService()
