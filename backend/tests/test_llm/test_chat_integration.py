import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture
def mock_get_db():
    """Mock database session."""
    with patch('app.core.database.get_db') as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        yield mock_db

@pytest.fixture
def mock_llm_agent():
    """Mock LLM agent service."""
    with patch('app.api.v1.router.llm_agent_service') as mock_llm:
        yield mock_llm

@pytest.fixture
def mock_sql_validator():
    """Mock SQL validator."""
    with patch('app.api.v1.router.sql_validator') as mock_validator:
        # Default to valid SQL
        mock_validator.validate_sql.return_value = (True, None)
        mock_validator.sanitize_error_message.return_value = "Sanitized error"
        yield mock_validator

@pytest.fixture
def mock_postgres_repo():
    """Mock postgres repository for executing SQL."""
    with patch('app.api.v1.router.postgres_repository') as mock_repo:
        # Mock the database execute method
        mock_result = MagicMock()
        mock_result.keys.return_value = ["id", "name", "spend"]
        mock_result.fetchall.return_value = [
            ("123", "Test Campaign", 100.50),
            ("456", "Another Campaign", 200.75)
        ]
        mock_repo.__class__ = MagicMock  # Prevent actual repository calls
        yield mock_repo

def test_chat_endpoint_success(mock_get_db, mock_llm_agent, mock_sql_validator, mock_postgres_repo):
    """Test successful chat interaction."""
    # Mock LLM SQL generation
    mock_llm_agent.generate_sql = AsyncMock()
    mock_llm_agent.generate_sql.return_value = {
        "success": True,
        "sql": "SELECT c.id, c.name, SUM(i.spend) as total_spend FROM insights i JOIN ads a ON i.ad_id = a.id JOIN ad_sets ad ON a.ad_set_id = ad.id JOIN campaigns c ON ad.campaign_id = c.id GROUP BY c.id, c.name",
        "error": ""
    }
    
    # Mock LLM summarization
    mock_llm_agent.summarize_results = AsyncMock()
    mock_llm_agent.summarize_results.return_value = {
        "success": True,
        "summary": "The test campaign had the highest spend.",
        "error": ""
    }
    
    # Mock database execution
    with patch('app.core.database.get_db') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.keys.return_value = ["id", "name", "total_spend"]
        mock_result.fetchall.return_value = [
            ("123", "Test Campaign", 100.50),
            ("456", "Another Campaign", 200.75)
        ]
        mock_db.execute.return_value = mock_result
        mock_get_db.return_value = mock_db
        
        response = client.post(
            "/api/chat",
            json={"query": "Which campaign had the highest spend?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sql" in data
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 2
        mock_llm_agent.generate_sql.assert_called_once()
        mock_llm_agent.summarize_results.assert_called_once()

def test_chat_endpoint_empty_query():
    """Test chat endpoint with empty query."""
    response = client.post("/api/chat", json={"query": ""})
    assert response.status_code == 400
    assert "Query cannot be empty" in response.json()["detail"]

def test_chat_endpoint_sql_generation_failure(mock_get_db, mock_llm_agent):
    """Test chat endpoint when SQL generation fails."""
    mock_llm_agent.generate_sql = AsyncMock()
    mock_llm_agent.generate_sql.return_value = {
        "success": False,
        "sql": "",
        "error": "Failed to generate SQL"
    }
    
    response = client.post("/api/chat", json={"query": "Invalid question"})
    assert response.status_code == 400
    assert "I couldn't generate a valid query" in response.json()["detail"]

def test_chat_endpoint_sql_validation_failure(mock_get_db, mock_llm_agent, mock_sql_validator):
    """Test chat endpoint when SQL validation fails."""
    mock_llm_agent.generate_sql = AsyncMock()
    mock_llm_agent.generate_sql.return_value = {
        "success": True,
        "sql": "DROP TABLE campaigns",
        "error": ""
    }
    
    mock_sql_validator.validate_sql.return_value = (False, "DDL operations are not allowed")
    
    # Mock retry attempt
    mock_llm_agent.generate_sql.side_effect = [
        {
            "success": True,
            "sql": "DROP TABLE campaigns",
            "error": ""
        },
        {
            "success": False,
            "sql": "",
            "error": "Still invalid"
        }
    ]
    
    response = client.post("/api/chat", json={"query": "Delete all campaigns"})
    assert response.status_code == 400
    assert "I couldn't generate a valid query after multiple attempts" in response.json()["detail"]

def test_chat_endpoint_sql_execution_failure(mock_get_db, mock_llm_agent, mock_sql_validator):
    """Test chat endpoint when SQL execution fails."""
    mock_llm_agent.generate_sql = AsyncMock()
    mock_llm_agent.generate_sql.return_value = {
        "success": True,
        "sql": "SELECT * FROM nonexistent_table",
        "error": ""
    }
    
    mock_sql_validator.validate_sql.return_value = (True, None)
    
    # Mock database execution failure
    with patch('app.core.database.get_db') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=Exception("Table doesn't exist"))
        mock_get_db.return_value = mock_db
        
        # Mock LLM repair attempt
        mock_llm_agent.generate_sql.side_effect = [
            {
                "success": True,
                "sql": "SELECT * FROM nonexistent_table",
                "error": ""
            },  # Initial generation
            {
                "success": False,
                "sql": "",
                "error": "Could not repair"
            }   # Repair attempt
        ]
        
        response = client.post("/api/chat", json={"query": "Show me nonexistent data"})
        assert response.status_code == 400
        assert "I couldn't execute a valid query" in response.json()["detail"]

def test_chat_endpoint_no_data_found(mock_get_db, mock_llm_agent, mock_sql_validator):
    """Test chat endpoint when query returns no data."""
    mock_llm_agent.generate_sql = AsyncMock()
    mock_llm_agent.generate_sql.return_value = {
        "success": True,
        "sql": "SELECT * FROM campaigns WHERE status = 'nonexistent'",
        "error": ""
    }
    
    mock_sql_validator.validate_sql.return_value = (True, None)
    
    # Mock database execution returning empty results
    with patch('app.core.database.get_db') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.keys.return_value = ["id", "name", "status"]
        mock_result.fetchall.return_value = []  # Empty results
        mock_db.execute.return_value = mock_result
        mock_get_db.return_value = mock_db
        
        # Mock LLM summarization for empty results
        mock_llm_agent.summarize_results = AsyncMock()
        mock_llm_agent.summarize_results.return_value = {
            "success": True,
            "summary": "No data found for your query. Try a different date range or campaign.",
            "error": ""
        }
        
        response = client.post("/api/chat", json={"query": "Show me nonexistent campaigns"})
        assert response.status_code == 200
        data = response.json()
        assert "No data found" in data["answer"]
        assert data["data"] == []