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
        # Make the get_insights method an AsyncMock
        mock_repo.get_insights = AsyncMock()
        yield mock_repo

def test_get_insights_success(mock_get_db, mock_postgres_repo):
    """Test successful retrieval of insights."""
    # Mock repo response
    mock_insights = [
        {
            "id": "789",
            "ad_id": "456",
            "date": "2023-06-01",
            "impressions": 1000,
            "clicks": 50,
            "spend": 25.50,
            "reach": 800,
            "frequency": 1.25,
            "ctr": 0.05,
            "cpc": 0.51,
            "cpm": 25.50,
            "conversions": 5,
            "conversion_value": 100.00,
            "created_at": "2023-06-01T00:00:00",
            "updated_at": "2023-06-01T00:00:00"
        }
    ]
    mock_postgres_repo.get_insights.return_value = mock_insights
    
    response = client.get("/api/insights")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "789"
    assert data[0]["impressions"] == 1000
    mock_postgres_repo.get_insights.assert_called_once()

def test_get_insights_with_date_filters(mock_get_db, mock_postgres_repo):
    """Test insights retrieval with date filters."""
    mock_postgres_repo.get_insights.return_value = []
    
    response = client.get("/api/insights?date_from=2023-06-01&date_to=2023-06-30")
    
    assert response.status_code == 200
    mock_postgres_repo.get_insights.assert_called_once()
    # Check that date parameters were passed
    args, kwargs = mock_postgres_repo.get_insights.call_args
    assert kwargs.get('date_from') == "2023-06-01"
    assert kwargs.get('date_to') == "2023-06-30"

def test_get_insights_with_campaign_filter(mock_get_db, mock_postgres_repo):
    """Test insights retrieval with campaign filter."""
    mock_postgres_repo.get_insights.return_value = []
    
    response = client.get("/api/insights?campaign_id=123")
    
    assert response.status_code == 200
    mock_postgres_repo.get_insights.assert_called_once()
    # Check that campaign_id parameter was passed
    args, kwargs = mock_postgres_repo.get_insights.call_args
    assert kwargs.get('campaign_id') == "123"

def test_get_insights_pagination(mock_get_db, mock_postgres_repo):
    """Test insights retrieval with pagination."""
    mock_postgres_repo.get_insights.return_value = []
    
    response = client.get("/api/insights?limit=10&offset=5")
    
    assert response.status_code == 200
    mock_postgres_repo.get_insights.assert_called_once()
    # Check that limit and offset parameters were passed
    args, kwargs = mock_postgres_repo.get_insights.call_args
    assert kwargs.get('limit') == 10
    assert kwargs.get('offset') == 5