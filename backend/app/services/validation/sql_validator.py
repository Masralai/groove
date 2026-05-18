import re

import sqlparse

from app.core.fd_logger import FdLogger

logger = FdLogger(__name__)

class SQLValidator:
    """Multi-layered SQL validation service for security and correctness."""

    # Patterns that indicate dangerous SQL operations
    DDL_DML_PATTERNS = [
        r'\bALTER\b', r'\bCREATE\b', r'\bDELETE\b', r'\bDROP\b',
        r'\bEXECUTE\b', r'\bINSERT\b', r'\bMERGE\b', r'\bTRUNCATE\b',
        r'\bUPDATE\b', r'\bRENAME\b', r'\bREVOKE\b', r'\bGRANT\b'
    ]

    # System table/schema patterns to block
    SYSTEM_TABLE_PATTERNS = [
        r'pg_', r'information_schema', r'sqlite_', r'pg_catalog',
        r'pg_type', r'pg_attribute', r'pg_class', r'pg_namespace',
        r'pg_depend', r'pg_constraint', r'pg_index', r'pg_proc'
    ]

    @classmethod
    def validate_sql(cls, sql: str) -> tuple[bool, str | None]:
        """
        Validate SQL query with multiple layers of protection.

        Args:
            sql: The SQL query to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not sql or not sql.strip():
            return False, "Empty SQL query"

        # Layer 1: Strip comments and whitespace
        try:
            parsed = sqlparse.parse(sql)[0]
            # Remove comments
            stripped_sql = ''.join([str(token) for token in parsed.tokens
                                  if not isinstance(token, sqlparse.sql.Comment)])
            stripped_sql = stripped_sql.strip()
        except Exception as e:
            logger.warning(f"Error parsing SQL with sqlparse: {e}")
            # Fallback: simple comment stripping
            stripped_sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
            stripped_sql = re.sub(r'/\*.*?\*/', '', stripped_sql, flags=re.DOTALL)
            stripped_sql = stripped_sql.strip()

        if not stripped_sql:
            return False, "SQL query is empty after removing comments"

        # Layer 2: Single-statement enforcement
        # Check for multiple statements (semicolons not in strings)
        # Simple approach: count semicolons outside of quotes
        semicolon_count = 0
        in_single_quote = False
        in_double_quote = False
        escape_next = False

        for char in stripped_sql:
            if escape_next:
                escape_next = False
                continue

            if char == '\\':
                escape_next = True
                continue

            if char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif char == ';' and not in_single_quote and not in_double_quote:
                semicolon_count += 1

        if semicolon_count > 0:
            return False, "Multi-statement queries are not allowed"

        # Layer 3: Must start with SELECT or WITH (CTE)
        upper_sql = stripped_sql.upper().strip()
        if not (upper_sql.startswith('SELECT') or upper_sql.startswith('WITH')):
            return False, "Query must start with SELECT or WITH"

        # Layer 4: Blacklist DDL/DML keywords
        for pattern in cls.DDL_DML_PATTERNS:
            if re.search(pattern, upper_sql, re.IGNORECASE):
                # Check if it's in a string literal (crude check)
                # For simplicity, we'll just block these keywords entirely
                # A more sophisticated approach would check context
                return False, f"DDL/DML operations are not allowed: {pattern.strip('\\b')}"

        # Layer 5: Blacklist system table references
        for pattern in cls.SYSTEM_TABLE_PATTERNS:
            if re.search(pattern, upper_sql, re.IGNORECASE):
                return False, f"Access to system tables is not allowed: {pattern.rstrip('_')}"

        # Additional safety: LIMIT clause encouragement (not enforced but noted)
        # In a production system, we might automatically add LIMIT if missing

        return True, None

    @classmethod
    def sanitize_error_message(cls, error: str) -> str:
        """
        Sanitize error messages to prevent information leakage.

        Args:
            error: Raw error message from database

        Returns:
            Sanitized error message safe to show to users/LLM
        """
        # Remove potential sensitive information
        sanitized = re.sub(r'\[.*?\]', '[REDACTED]', error)  # Remove bracketed info
        sanitized = re.sub(r'\"[^\"]*\"', '\"[REDACTED]\"', sanitized)  # Remove quoted strings
        sanitized = re.sub(
            r'\'[^\']*\'', '\'[REDACTED]\'', sanitized
        )  # Remove single-quoted strings

        # Limit length
        if len(sanitized) > 200:
            sanitized = sanitized[:200] + "... [TRUNCATED]"

        return sanitized


# Singleton instance
sql_validator = SQLValidator()
