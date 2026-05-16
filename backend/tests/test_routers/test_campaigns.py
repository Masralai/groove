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
def mock_postgres_repo():
    """Mock postgres repository."""
    with patch('app.api.v1.router.postgres_repository') as mock_repo:
        # Make the get_campaigns method an AsyncMock
        mock_repo.get_campaigns = AsyncMock()
        yield mock_repo

def test_get_campaigns_success(mock_get_db, mock_postgres_repo):
    """Test successful retrieval of campaigns."""
    # Mock repo response
    mock_campaigns = [
        {
            "id": "123",
            "name": "Test Campaign",
            "status": "ACTIVE",
            "objective": "CONVERSIONS",
            "daily_budget": 100.0,
            "lifetime_budget": None,
            "created_time": "2023-01-01T00:00:00",
            "start_time": None,
            "stop_time": None,
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
    ]
    mock_postgres_repo.get_campaigns.return_value = mock_campaigns
    
    response = client.get("/api/campaigns")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "123"
    assert data[0]["name"] == "Test Campaign"
    mock_postgres_repo.get_campaigns.assert_called_once()

def test_get_campaigns_with_status_filter(mock_get_db, mock_postgres_repo):
    """Test campaigns retrieval with status filter."""
    mock_postgres_repo.get_campaigns.return_value = []
    
    response = client.get("/api/campaigns?status=ACTIVE")
    
    assert response.status_code == 200
    mock_postgres_repo.get_campaigns.assert_called_once()
    # Check that status parameter was passed
    args, kwargs = mock_postgres_repo.get_campaigns.call_args
    assert kwargs.get('status') == "ACTIVE"

def test_get_campaigns_pagination(mock_get_db, mock_postgres_repo):
    """Test campaigns retrieval with pagination."""
    mock_postgres_repo.get_campaigns.return_value = []
    
    response = client.get("/api/campaigns?limit=10&offset=20")
    
    assert response.status_code == 200
    mock_postgres_repo.get_campaigns.assert_called_once()
    # Check that limit and offset parameters were passed
    args, kwargs = mock_postgres_repo.get_campaigns.call_args
    assert kwargs.get('limit') == 10
    assert kwargs.get('offset') == 20