import os
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from app.repositories.mongo_repository import MongoRepository

# Mock environment variables for testing
os.environ["META_ACCESS_TOKEN"] = "test_token"
os.environ["META_AD_ACCOUNT_ID"] = "act_123456"
os.environ["GEMINI_API_KEY"] = "test_key"
os.environ["POSTGRES_DSN"] = "postgresql+asyncpg://user:pass@localhost/db"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/test_db"

@pytest.fixture
def mock_mongo_client():
    """Patch collection references directly at the repository module level."""
    mock_result = MagicMock()
    mock_result.inserted_ids = ['id1', 'id2', 'id3']

    with patch('app.repositories.mongo_repository.campaigns_raw') as mock_campaigns, \
         patch('app.repositories.mongo_repository.ad_sets_raw') as mock_ad_sets, \
         patch('app.repositories.mongo_repository.ads_raw') as mock_ads, \
         patch('app.repositories.mongo_repository.insights_raw') as mock_insights:

        async def insert_many_side_effect(docs):
            mock_result.inserted_ids = [f'id{i}' for i in range(len(docs))]
            return mock_result

        mock_campaigns.insert_many = AsyncMock(side_effect=insert_many_side_effect)
        mock_ad_sets.insert_many = AsyncMock(side_effect=insert_many_side_effect)
        mock_ads.insert_many = AsyncMock(side_effect=insert_many_side_effect)
        mock_insights.insert_many = AsyncMock(side_effect=insert_many_side_effect)

        yield {
            'campaigns': mock_campaigns,
            'ad_sets': mock_ad_sets,
            'ads': mock_ads,
            'insights': mock_insights,
        }

@pytest.fixture
def mongo_repository():
    """Create a MongoRepository instance."""
    return MongoRepository()

@pytest.mark.asyncio
async def test_insert_campaigns(mongo_repository, mock_mongo_client):
    """Test inserting campaigns into MongoDB."""
    # Arrange
    test_campaigns = [
        {'id': '1', 'name': 'Campaign 1', 'status': 'ACTIVE'},
        {'id': '2', 'name': 'Campaign 2', 'status': 'PAUSED'},
        {'id': '3', 'name': 'Campaign 3', 'status': 'ACTIVE'}
    ]
    
    # Act
    result = await mongo_repository.insert_campaigns(test_campaigns)
    
    # Assert
    assert result == 3
    mock_mongo_client['campaigns'].insert_many.assert_called_once()
    
    # Check that _stored_at field was added
    call_args = mock_mongo_client['campaigns'].insert_many.call_args[0][0]
    assert len(call_args) == 3
    for campaign in call_args:
        assert '_stored_at' in campaign
        assert isinstance(campaign['_stored_at'], datetime)

@pytest.mark.asyncio
async def test_insert_ad_sets(mongo_repository, mock_mongo_client):
    """Test inserting ad sets into MongoDB."""
    # Arrange
    test_ad_sets = [
        {'id': '1', 'name': 'Ad Set 1', 'status': 'ACTIVE', 'campaign_id': '1'},
        {'id': '2', 'name': 'Ad Set 2', 'status': 'PAUSED', 'campaign_id': '1'}
    ]
    
    # Act
    result = await mongo_repository.insert_ad_sets(test_ad_sets)
    
    # Assert
    assert result == 2
    mock_mongo_client['ad_sets'].insert_many.assert_called_once()
    
    # Check that _stored_at field was added
    call_args = mock_mongo_client['ad_sets'].insert_many.call_args[0][0]
    assert len(call_args) == 2
    for ad_set in call_args:
        assert '_stored_at' in ad_set
        assert isinstance(ad_set['_stored_at'], datetime)

@pytest.mark.asyncio
async def test_insert_ads(mongo_repository, mock_mongo_client):
    """Test inserting ads into MongoDB."""
    # Arrange
    test_ads = [
        {'id': '1', 'name': 'Ad 1', 'status': 'ACTIVE', 'ad_set_id': '1'},
        {'id': '2', 'name': 'Ad 2', 'status': 'PAUSED', 'ad_set_id': '1'}
    ]
    
    # Act
    result = await mongo_repository.insert_ads(test_ads)
    
    # Assert
    assert result == 2
    mock_mongo_client['ads'].insert_many.assert_called_once()
    
    # Check that _stored_at field was added
    call_args = mock_mongo_client['ads'].insert_many.call_args[0][0]
    assert len(call_args) == 2
    for ad in call_args:
        assert '_stored_at' in ad
        assert isinstance(ad['_stored_at'], datetime)

@pytest.mark.asyncio
async def test_insert_insights(mongo_repository, mock_mongo_client):
    """Test inserting insights into MongoDB."""
    # Arrange
    test_insights = [
        {'id': '1', 'impressions': 100, 'clicks': 10, 'spend': 5.0},
        {'id': '2', 'impressions': 200, 'clicks': 20, 'spend': 10.0}
    ]
    
    # Act
    result = await mongo_repository.insert_insights(test_insights)
    
    # Assert
    assert result == 2
    mock_mongo_client['insights'].insert_many.assert_called_once()
    
    # Check that _stored_at field was added
    call_args = mock_mongo_client['insights'].insert_many.call_args[0][0]
    assert len(call_args) == 2
    for insight in call_args:
        assert '_stored_at' in insight
        assert isinstance(insight['_stored_at'], datetime)

@pytest.mark.asyncio
async def test_insert_empty_lists(mongo_repository, mock_mongo_client):
    """Test inserting empty lists returns 0."""
    # Act
    result_campaigns = await mongo_repository.insert_campaigns([])
    result_ad_sets = await mongo_repository.insert_ad_sets([])
    result_ads = await mongo_repository.insert_ads([])
    result_insights = await mongo_repository.insert_insights([])
    
    # Assert
    assert result_campaigns == 0
    assert result_ad_sets == 0
    assert result_ads == 0
    assert result_insights == 0
    
    # Verify insert_many was not called
    mock_mongo_client['campaigns'].insert_many.assert_not_called()
    mock_mongo_client['ad_sets'].insert_many.assert_not_called()
    mock_mongo_client['ads'].insert_many.assert_not_called()
    mock_mongo_client['insights'].insert_many.assert_not_called()