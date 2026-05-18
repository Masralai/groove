from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_db_session():
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock()

    def override_get_db():
        return mock_db

    app.dependency_overrides[get_db] = override_get_db
    yield mock_db
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture
def mock_llm_service():
    with patch('app.api.v1.router.llm_service') as mock_llm:
        yield mock_llm

@pytest.fixture
def mock_sql_validator():
    with patch('app.api.v1.router.sql_validator') as mock_validator:
        mock_validator.validate_sql.return_value = (True, None)
        mock_validator.sanitize_error_message.return_value = "Sanitized error"
        yield mock_validator

def _make_db_result(keys, rows):
    mock_result = MagicMock()
    mock_result.keys.return_value = keys
    mock_result.fetchall.return_value = rows
    return mock_result

def test_chat_endpoint_success(mock_db_session, mock_llm_service, mock_sql_validator):
    mock_llm_service.generate_sql = AsyncMock(return_value={
        "success": True,
        "sql": "SELECT c.id, c.name, SUM(i.spend) as total_spend FROM insights i JOIN ads a ON i.ad_id = a.id JOIN ad_sets ad ON a.ad_set_id = ad.id JOIN campaigns c ON ad.campaign_id = c.id GROUP BY c.id, c.name",
        "error": ""
    })
    mock_llm_service.summarize_results = AsyncMock(return_value={
        "success": True,
        "summary": "The test campaign had the highest spend.",
        "error": ""
    })

    mock_db_session.execute.return_value = _make_db_result(
        ["id", "name", "total_spend"],
        [("123", "Test Campaign", 100.50), ("456", "Another Campaign", 200.75)]
    )

    response = client.post("/api/chat", json={"query": "Which campaign had the highest spend?"})

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sql" in data
    assert "data" in data
    assert len(data["data"]) == 2
    mock_llm_service.generate_sql.assert_called_once()
    mock_llm_service.summarize_results.assert_called_once()

def test_chat_endpoint_empty_query():
    response = client.post("/api/chat", json={"query": ""})
    assert response.status_code == 400
    assert "Query cannot be empty" in response.json()["detail"]

def test_chat_endpoint_sql_generation_failure(mock_db_session, mock_llm_service):
    mock_llm_service.generate_sql = AsyncMock(return_value={
        "success": False,
        "sql": "",
        "error": "Failed to generate SQL"
    })

    response = client.post("/api/chat", json={"query": "Invalid question"})
    assert response.status_code == 400
    assert "I couldn't generate a valid query" in response.json()["detail"]

def test_chat_endpoint_sql_validation_failure(mock_db_session, mock_llm_service, mock_sql_validator):
    mock_llm_service.generate_sql = AsyncMock(side_effect=[
        {"success": True, "sql": "DROP TABLE campaigns", "error": ""},
        {"success": False, "sql": "", "error": "Still invalid"}
    ])

    mock_sql_validator.validate_sql.return_value = (False, "DDL operations are not allowed")

    response = client.post("/api/chat", json={"query": "Delete all campaigns"})
    assert response.status_code == 400
    assert "I couldn't generate a valid query after multiple attempts" in response.json()["detail"]

def test_chat_endpoint_sql_execution_failure(mock_db_session, mock_llm_service, mock_sql_validator):
    mock_llm_service.generate_sql = AsyncMock(side_effect=[
        {"success": True, "sql": "SELECT * FROM nonexistent_table", "error": ""},
        {"success": True, "sql": "SELECT * FROM another_table", "error": ""},
    ])

    mock_db_session.execute.side_effect = [
        Exception("Table doesn't exist"),
        Exception("Repair also failed"),
    ]

    response = client.post("/api/chat", json={"query": "Show me nonexistent data"})
    assert response.status_code == 400
    assert "I couldn't execute a valid query" in response.json()["detail"]

def test_chat_endpoint_no_data_found(mock_db_session, mock_llm_service, mock_sql_validator):
    mock_llm_service.generate_sql = AsyncMock(return_value={
        "success": True,
        "sql": "SELECT * FROM campaigns WHERE status = 'nonexistent'",
        "error": ""
    })
    mock_llm_service.summarize_results = AsyncMock(return_value={
        "success": True,
        "summary": "No data found for your query. Try a different date range or campaign.",
        "error": ""
    })

    mock_db_session.execute.return_value = _make_db_result(
        ["id", "name", "status"],
        []
    )

    response = client.post("/api/chat", json={"query": "Show me nonexistent campaigns"})
    assert response.status_code == 200
    data = response.json()
    assert "No data found" in data["answer"]
    assert data["data"] == []
