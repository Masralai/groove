import os

# Mock environment variables for testing
os.environ["META_ACCESS_TOKEN"] = "test_token"
os.environ["META_AD_ACCOUNT_ID"] = "act_123456"
os.environ["GEMINI_API_KEY"] = "test_key"
os.environ["POSTGRES_DSN"] = "postgresql+asyncpg://user:pass@localhost/db"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/db"

from unittest.mock import MagicMock, patch

import pytest

from app.services.meta_api_service import MetaAPIService


@pytest.fixture
def meta_api_service():
    return MetaAPIService()

@pytest.mark.asyncio
async def test_meta_api_service_initialization(meta_api_service):
    """Test that the MetaAPI service initializes correctly."""
    with patch('facebook_business.api.FacebookAdsApi.init') as mock_init:
        await meta_api_service.initialize()
        mock_init.assert_called_once()
        assert meta_api_service.api_initialized == True

@pytest.mark.asyncio
async def test_fetch_campaigns(meta_api_service):
    """Test fetching campaigns."""
    # Mock the Facebook Ads API response
    mock_campaign_data = [
        {'id': '123', 'name': 'Test Campaign', 'status': 'ACTIVE'},
        {'id': '456', 'name': 'Another Campaign', 'status': 'PAUSED'}
    ]

    with patch.object(meta_api_service, 'initialize'):
        # Manually set the ad_account since initialize is mocked
        meta_api_service.ad_account = MagicMock()
        with patch.object(meta_api_service.ad_account, 'get_campaigns') as mock_get_campaigns:
            # Mock the iterator returned by get_campaigns
            mock_iterator = MagicMock()
            mock_iterator.__iter__.return_value = iter(mock_campaign_data)
            mock_get_campaigns.return_value = mock_iterator

            # Collect results
            campaigns = []
            async for campaign in meta_api_service.fetch_campaigns():
                campaigns.append(campaign)

            assert len(campaigns) == 2
            assert campaigns[0]['id'] == '123'
            assert campaigns[1]['name'] == 'Another Campaign'

@pytest.mark.asyncio
async def test_fetch_ad_sets(meta_api_service):
    """Test fetching ad sets."""
    mock_ad_set_data = [
        {'id': '789', 'name': 'Test Ad Set', 'status': 'ACTIVE', 'campaign_id': '123'},
        {'id': '101', 'name': 'Another Ad Set', 'status': 'PAUSED', 'campaign_id': '123'}
    ]

    with patch.object(meta_api_service, 'initialize'):
        # Manually set the ad_account since initialize is mocked
        meta_api_service.ad_account = MagicMock()
        with patch.object(meta_api_service.ad_account, 'get_ad_sets') as mock_get_ad_sets:
            mock_iterator = MagicMock()
            mock_iterator.__iter__.return_value = iter(mock_ad_set_data)
            mock_get_ad_sets.return_value = mock_iterator

            ad_sets = []
            async for ad_set in meta_api_service.fetch_ad_sets():
                ad_sets.append(ad_set)

            assert len(ad_sets) == 2
            assert ad_sets[0]['id'] == '789'
            assert ad_sets[1]['campaign_id'] == '123'

@pytest.mark.asyncio
async def test_fetch_ads(meta_api_service):
    """Test fetching ads."""
    mock_ad_data = [
        {'id': '112', 'name': 'Test Ad', 'status': 'ACTIVE', 'ad_set_id': '789'},
        {'id': '113', 'name': 'Another Ad', 'status': 'PAUSED', 'ad_set_id': '789'}
    ]

    with patch.object(meta_api_service, 'initialize'):
        # Manually set the ad_account since initialize is mocked
        meta_api_service.ad_account = MagicMock()
        with patch.object(meta_api_service.ad_account, 'get_ads') as mock_get_ads:
            mock_iterator = MagicMock()
            mock_iterator.__iter__.return_value = iter(mock_ad_data)
            mock_get_ads.return_value = mock_iterator

            ads = []
            async for ad in meta_api_service.fetch_ads():
                ads.append(ad)

            assert len(ads) == 2
            assert ads[0]['id'] == '112'
            assert ads[1]['ad_set_id'] == '789'

@pytest.mark.asyncio
async def test_fetch_insights(meta_api_service):
    """Test fetching insights."""
    mock_insights_data = [
        {'id': '201', 'date_start': '2023-01-01', 'date_stop': '2023-01-01',
         'impressions': 1000, 'clicks': 50, 'spend': 10.50},
        {'id': '202', 'date_start': '2023-01-02', 'date_stop': '2023-01-02',
         'impressions': 1500, 'clicks': 75, 'spend': 15.75}
    ]

    with patch.object(meta_api_service, 'initialize'):
        # Manually set the ad_account since initialize is mocked
        meta_api_service.ad_account = MagicMock()
        with patch.object(meta_api_service.ad_account, 'get_insights') as mock_get_insights:
            mock_iterator = MagicMock()
            mock_iterator.__iter__.return_value = iter(mock_insights_data)
            mock_get_insights.return_value = mock_iterator

            insights = []
            async for insight in meta_api_service.fetch_insights():
                insights.append(insight)

            assert len(insights) == 2
            assert insights[0]['impressions'] == 1000
            assert insights[1]['spend'] == 15.75
