import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

# Set environment variables before any imports
os.environ["META_ACCESS_TOKEN"] = "test_token"
os.environ["META_AD_ACCOUNT_ID"] = "act_123456"
os.environ["GEMINI_API_KEY"] = "test_key"
os.environ["POSTGRES_DSN"] = "postgresql+asyncpg://user:pass@localhost/db"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/test_db"

@pytest.fixture
def mock_settings():
    """Mock settings to avoid validation errors."""
    with patch('app.core.config.Settings') as mock_settings_class:
        mock_settings = MagicMock()
        mock_settings_class.return_value = mock_settings
        
        # Mock the meta_ads configuration
        mock_settings.meta_ads = {
            'api_version': 'v22.0',
            'fields': {
                'campaigns': ['id', 'name', 'status', 'objective', 'daily_budget', 'lifetime_budget', 'created_time', 'start_time', 'stop_time'],
                'ad_sets': ['id', 'name', 'campaign_id', 'status', 'daily_budget', 'lifetime_budget', 'targeting', 'bid_strategy', 'created_time'],
                'ads': ['id', 'name', 'ad_set_id', 'status', 'creative', 'created_time'],
                'insights': ['impressions', 'clicks', 'spend', 'reach', 'frequency', 'ctr', 'cpc', 'cpm', 'conversions', 'conversion_value']
            },
            'insights_time_range_days': 30
        }
        
        yield mock_settings

@pytest.mark.asyncio
async def test_sync_service_import(mock_settings):
    """Test that the sync service can be imported."""
    # This test just verifies that imports work when settings are mocked
    from app.services.sync_service import data_sync_service
    assert data_sync_service is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])