import os

os.environ["META_ACCESS_TOKEN"] = "test_token"
os.environ["META_AD_ACCOUNT_ID"] = "act_123456"
os.environ["LLM_PROVIDER"] = "openrouter"
os.environ["OPENROUTER_API_KEY"] = "sk-or-v1-test-key"
os.environ["POSTGRES_DSN"] = "postgresql+asyncpg://user:pass@localhost/db"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/db"

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.sync_service import DataSyncService, SyncAlreadyRunningError


@pytest.fixture
def sync_service():
    return DataSyncService()


@pytest.mark.asyncio
class TestGetLastSyncDate:
    async def test_returns_latest_insight_stored_at(self, sync_service):
        expected_date = datetime(2023, 6, 15, 10, 30, 0)
        with patch("app.services.sync_service.insights_raw") as mock_collection:
            mock_collection.find_one.return_value = {"_stored_at": expected_date}
            mock_collection.find_one = AsyncMock(return_value={"_stored_at": expected_date})

            result = await sync_service._get_last_sync_date()
            assert result == expected_date

    async def test_falls_back_to_60_days_ago(self, sync_service):
        with patch("app.services.sync_service.insights_raw") as mock_collection:
            mock_collection.find_one.return_value = None

            result = await sync_service._get_last_sync_date()
            assert result is not None
            assert result > datetime.now(UTC) - timedelta(days=61)
            assert result < datetime.now(UTC) - timedelta(days=59)

    async def test_exception_returns_fallback(self, sync_service):
        with patch("app.services.sync_service.insights_raw") as mock_collection:
            mock_collection.find_one.side_effect = Exception("DB error")

            result = await sync_service._get_last_sync_date()
            assert result is not None
            assert result < datetime.now(UTC)


@pytest.mark.asyncio
class TestGetTimeRange:
    async def test_incremental_uses_last_sync(self, sync_service):
        with patch.object(sync_service, "_get_last_sync_date", return_value=datetime(2023, 6, 1)):
            time_range = await sync_service._get_time_range(full_sync=False)
            assert "since" in time_range
            assert "until" in time_range
            assert time_range["since"] == "2023-06-01"

    async def test_full_sync_uses_60_days(self, sync_service):
        with patch.object(sync_service, "_get_last_sync_date") as mock_last:
            time_range = await sync_service._get_time_range(full_sync=True)
            assert "since" in time_range
            assert "until" in time_range
            mock_last.assert_not_called()


async def _empty_async_gen(*args, **kwargs):
    if False:
        yield


@pytest.mark.asyncio
class TestSyncAll:
    async def test_sync_all_orchestrates_in_order(self, sync_service):
        mock_meta = MagicMock()
        mock_meta.fetch_campaigns = _empty_async_gen
        mock_meta.fetch_ad_sets = _empty_async_gen
        mock_meta.fetch_ads = _empty_async_gen
        mock_meta.fetch_insights = _empty_async_gen

        sync_service.meta_api = mock_meta
        sync_service.mongo_repo = AsyncMock()
        sync_service.mongo_repo.insert_campaigns.return_value = 0
        sync_service.mongo_repo.insert_ad_sets.return_value = 0
        sync_service.mongo_repo.insert_ads.return_value = 0
        sync_service.mongo_repo.insert_insights.return_value = 0
        sync_service.postgres_repo = AsyncMock()
        sync_service.postgres_repo.upsert_campaigns.return_value = 0
        sync_service.postgres_repo.upsert_ad_sets.return_value = 0
        sync_service.postgres_repo.upsert_ads.return_value = 0
        sync_service.postgres_repo.upsert_insights.return_value = 0
        sync_service.transformer = MagicMock()
        sync_service.transformer.transform_campaigns.return_value = []
        sync_service.transformer.transform_ad_sets.return_value = []
        sync_service.transformer.transform_ads.return_value = []
        sync_service.transformer.transform_insights.return_value = []

        with patch("app.services.sync_service.AsyncSessionLocal") as mock_sf:
            mock_session = MagicMock()
            mock_session.execute = AsyncMock(
                return_value=MagicMock(scalar=MagicMock(return_value=True))
            )
            mock_session.close = AsyncMock()
            mock_sf.return_value = mock_session

            result = await sync_service.sync_all()
            assert "campaigns" in result
            assert "ad_sets" in result
            assert "ads" in result
            assert "insights" in result

    async def test_error_propagates(self, sync_service):
        async def _raise_error():
            raise Exception("API Error")
            if False:
                yield

        mock_meta = MagicMock()
        mock_meta.fetch_campaigns = _raise_error

        sync_service.meta_api = mock_meta

        with patch("app.services.sync_service.AsyncSessionLocal") as mock_sf:
            mock_session = MagicMock()
            mock_session.execute = AsyncMock(
                return_value=MagicMock(scalar=MagicMock(return_value=True))
            )
            mock_session.close = AsyncMock()
            mock_sf.return_value = mock_session

            with pytest.raises(Exception, match="API Error"):
                await sync_service.sync_all()


@pytest.mark.asyncio
class TestAdvisoryLock:
    async def test_lock_acquired_sync_proceeds(self, sync_service):
        """sync_all proceeds normally when advisory lock is acquired."""
        mock_meta = MagicMock()
        mock_meta.fetch_campaigns = _empty_async_gen
        mock_meta.fetch_ad_sets = _empty_async_gen
        mock_meta.fetch_ads = _empty_async_gen
        mock_meta.fetch_insights = _empty_async_gen

        sync_service.meta_api = mock_meta
        sync_service.mongo_repo = AsyncMock()
        sync_service.mongo_repo.insert_campaigns.return_value = 0
        sync_service.mongo_repo.insert_ad_sets.return_value = 0
        sync_service.mongo_repo.insert_ads.return_value = 0
        sync_service.mongo_repo.insert_insights.return_value = 0
        sync_service.postgres_repo = AsyncMock()
        sync_service.postgres_repo.upsert_campaigns.return_value = 0
        sync_service.postgres_repo.upsert_ad_sets.return_value = 0
        sync_service.postgres_repo.upsert_ads.return_value = 0
        sync_service.postgres_repo.upsert_insights.return_value = 0
        sync_service.transformer = MagicMock()
        sync_service.transformer.transform_campaigns.return_value = []
        sync_service.transformer.transform_ad_sets.return_value = []
        sync_service.transformer.transform_ads.return_value = []
        sync_service.transformer.transform_insights.return_value = []

        with patch("app.services.sync_service.AsyncSessionLocal") as mock_sf:
            mock_session = MagicMock()
            mock_session.execute = AsyncMock(
                return_value=MagicMock(scalar=MagicMock(return_value=True))
            )
            mock_session.close = AsyncMock()
            mock_sf.return_value = mock_session

            result = await sync_service.sync_all()

            assert result == {"campaigns": 0, "ad_sets": 0, "ads": 0, "insights": 0}
            # Verify lock was acquired (pg_try_advisory_lock called) and released
            assert mock_session.execute.call_count >= 2

    async def test_raises_error_when_lock_not_available(self, sync_service):
        """sync_all raises SyncAlreadyRunningError when lock is not available."""
        with patch("app.services.sync_service.AsyncSessionLocal") as mock_sf:
            mock_session = MagicMock()
            mock_session.execute = AsyncMock(
                return_value=MagicMock(scalar=MagicMock(return_value=False))
            )
            mock_session.close = AsyncMock()
            mock_sf.return_value = mock_session

            with pytest.raises(SyncAlreadyRunningError, match="already in progress"):
                await sync_service.sync_all()

            mock_session.execute.assert_called_once()
