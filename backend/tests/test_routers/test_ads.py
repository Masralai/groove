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
        # Make the get_ads method an AsyncMock
        mock_repo.get_ads = AsyncMock()
        yield mock_repo

def test_get_ads_success(mock_get_db, mock_postgres_repo):
    """Test successful retrieval of ads."""
    # Mock repo response
    mock_ads = [
        {
            "id": "456",
            "ad_set_id": "789",
            "name": "Test Ad",
            "status": "ACTIVE",
            "creative": {"image_hash": "abc123"},
            "created_time": "2023-01-01T00:00:00",
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
    ]
    mock_postgres_repo.get_ads.return_value = mock_ads
    
    response = client.get("/api/ads")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "456"
    assert data[0]["name"] == "Test Ad"
    mock_postgres_repo.get_ads.assert_called_once()

def test_get_ads_with_campaign_filter(mock_get_db, mock_postgres_repo):
    """Test ads retrieval with campaign filter."""
    mock_postgres_repo.get_ads.return_value = []
    
    response = client.get("/api/ads?campaign_id=123")
    
    assert response.status_code == 200
    mock_postgres_repo.get_ads.assert_called_once()
    # Check that campaign_id parameter was passed
    args, kwargs = mock_postgres_repo.get_ads.call_args
    assert kwargs.get('campaign_id') == "123"

def test_get_ads_pagination(mock_get_db, mock_postgres_repo):
    """Test ads retrieval with pagination."""
    mock_postgres_repo.get_ads.return_value = []
    
    response = client.get("/api/ads?limit=5&offset=0")
    
    assert response.status_code == 200
    mock_postgres_repo.get_ads.assert_called_once()
    # Check that limit and offset parameters were passed
    args, kwargs = mock_postgres_repo.get_ads.call_args
    assert kwargs.get('limit') == 5
    assert kwargs.get('offset') == 0