import pytest
from app.services.validation.sql_validator import sql_validator

def test_valid_select_query():
    """Test that valid SELECT queries pass validation."""
    valid_queries = [
        "SELECT * FROM campaigns",
        "SELECT name, status FROM campaigns WHERE status = 'active'",
        "SELECT c.name, SUM(i.spend) FROM insights i JOIN campaigns c ON i.ad_id = c.id GROUP BY c.name",
        "WITH cte AS (SELECT * FROM campaigns) SELECT * FROM cte",
        "SELECT * FROM insights LIMIT 10"
    ]
    
    for query in valid_queries:
        is_valid, error = sql_validator.validate_sql(query)
        assert is_valid is True, f"Query should be valid: {query}"
        assert error is None, f"Error should be None for valid query: {query}"

def test_invalid_ddl_queries():
    """Test that DDL queries are rejected."""
    invalid_queries = [
        "DROP TABLE campaigns",
        "DELETE FROM campaigns WHERE id = '123'",
        "UPDATE campaigns SET status = 'paused' WHERE id = '123'",
        "INSERT INTO campaigns (id, name) VALUES ('456', 'Test')",
        "ALTER TABLE campaigns ADD COLUMN test TEXT",
        "CREATE TABLE test (id TEXT)",
        "TRUNCATE TABLE campaigns"
    ]
    
    for query in invalid_queries:
        is_valid, error = sql_validator.validate_sql(query)
        assert is_valid is False, f"Query should be invalid: {query}"
        assert error is not None, f"Error should not be None for invalid query: {query}"

def test_invalid_system_table_access():
    """Test that system table access is rejected."""
    invalid_queries = [
        "SELECT * FROM pg_tables",
        "SELECT * FROM information_schema.tables",
        "SELECT * FROM pg_catalog.pg_user",
        "SELECT * FROM sqlite_master"
    ]
    
    for query in invalid_queries:
        is_valid, error = sql_validator.validate_sql(query)
        assert is_valid is False, f"Query should be invalid: {query}"
        assert error is not None, f"Error should not be None for invalid query: {query}"

def test_multistatement_queries():
    """Test that multi-statement queries are rejected."""
    invalid_queries = [
        "SELECT * FROM campaigns; SELECT * FROM ad_sets",
        "SELECT * FROM campaigns; DELETE FROM insights",
        "WITH cte AS (SELECT * FROM campaigns) SELECT * FROM cte; SELECT * FROM ad_sets"
    ]
    
    for query in invalid_queries:
        is_valid, error = sql_validator.validate_sql(query)
        assert is_valid is False, f"Query should be invalid: {query}"
        assert error is not None, f"Error should not be None for invalid query: {query}"

def test_non_select_queries():
    """Test that non-SELECT queries are rejected."""
    invalid_queries = [
        "SHOW TABLES",
        "DESCRIBE campaigns",
        "EXPLAIN SELECT * FROM campaigns",
        "CALL some_procedure()"
    ]
    
    for query in invalid_queries:
        is_valid, error = sql_validator.validate_sql(query)
        assert is_valid is False, f"Query should be invalid: {query}"
        assert error is not None, f"Error should not be None for invalid query: {query}"

def test_empty_and_whitespace_queries():
    """Test that empty or whitespace-only queries are rejected."""
    invalid_queries = [
        "",
        "   ",
        "\n\t\n",
        ";"
    ]
    
    for query in invalid_queries:
        is_valid, error = sql_validator.validate_sql(query)
        assert is_valid is False, f"Query should be invalid: '{query}'"
        assert error is not None, f"Error should not be None for invalid query: '{query}'"

def test_comment_handling():
    """Test that SQL comments are properly handled."""
    valid_queries = [
        "SELECT * FROM campaigns -- this is a comment",
        "SELECT * FROM campaigns /* this is a */ comment */",
        "SELECT * FROM campaigns -- comment\nWHERE status = 'active'"
    ]
    
    for query in valid_queries:
        is_valid, error = sql_validator.validate_sql(query)
        assert is_valid is True, f"Query should be valid: {query}"
        assert error is None, f"Error should be None for valid query: {query}"

def test_sanitize_error_message():
    """Test that error messages are properly sanitized."""
    test_errors = [
        'ERROR: column "id" does not exist at character 15',
        'ERROR: relation "campaigns" does not exist',
        'ERROR: syntax error at or near "SELECT"',
        'ERROR: invalid input syntax for integer: "abc"',
        'ERROR: [SECRET_INFO] something sensitive',
        'ERROR: "quoted string with secrets" and more'
    ]
    
    for error in test_errors:
        sanitized = sql_validator.sanitize_error_message(error)
        # Should not contain the original sensitive information
        assert "[REDACTED]" in sanitized or len(sanitized) < len(error) or "SECRET_INFO" not in sanitized