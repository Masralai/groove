import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime, date
from app.repositories.postgres_repository import PostgresRepository
from app.models.postgres import Campaign, AdSet, Ad, Insight


@pytest.fixture
def repo():
    return PostgresRepository()


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.mark.asyncio
class TestUpsertCampaigns:
    async def test_upserts_campaigns(self, repo, mock_db):
        campaigns = [
            {
                "id": "1", "name": "C1", "status": "ACTIVE", "objective": "TRAFFIC",
                "daily_budget": 10000, "lifetime_budget": None,
                "created_time": datetime(2023, 1, 1), "start_time": None,
                "stop_time": None, "updated_at": datetime(2023, 1, 1),
            }
        ]
        count = await repo.upsert_campaigns(mock_db, campaigns)
        assert count == 1
        mock_db.execute.assert_awaited_once()
        mock_db.commit.assert_awaited_once()

    async def test_empty_list_returns_zero(self, repo, mock_db):
        count = await repo.upsert_campaigns(mock_db, [])
        assert count == 0
        mock_db.execute.assert_not_called()

    async def test_multiple_campaigns(self, repo, mock_db):
        campaigns = [
            {"id": "1", "name": "C1", "status": "ACTIVE", "objective": "TRAFFIC",
             "daily_budget": None, "lifetime_budget": None,
             "created_time": None, "start_time": None, "stop_time": None,
             "updated_at": datetime(2023, 1, 1)},
            {"id": "2", "name": "C2", "status": "PAUSED", "objective": "BRAND_AWARENESS",
             "daily_budget": None, "lifetime_budget": None,
             "created_time": None, "start_time": None, "stop_time": None,
             "updated_at": datetime(2023, 1, 1)},
        ]
        count = await repo.upsert_campaigns(mock_db, campaigns)
        assert count == 2
        assert mock_db.execute.await_count == 2
        mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
class TestUpsertAdSets:
    async def test_upserts_ad_sets(self, repo, mock_db):
        ad_sets = [{
            "id": "1", "campaign_id": "camp1", "name": "AS1", "status": "ACTIVE",
            "daily_budget": 5000, "lifetime_budget": None,
            "targeting": '{"countries": ["US"]}', "bid_strategy": "LOWEST_COST",
            "created_time": datetime(2023, 1, 1), "updated_at": datetime(2023, 1, 1),
        }]
        count = await repo.upsert_ad_sets(mock_db, ad_sets)
        assert count == 1
        mock_db.execute.assert_awaited_once()
        mock_db.commit.assert_awaited_once()

    async def test_empty_list(self, repo, mock_db):
        assert await repo.upsert_ad_sets(mock_db, []) == 0


@pytest.mark.asyncio
class TestUpsertAds:
    async def test_upserts_ads(self, repo, mock_db):
        ads = [{
            "id": "1", "ad_set_id": "adset1", "name": "Ad1", "status": "ACTIVE",
            "creative": '{"id": "cre1"}', "created_time": datetime(2023, 1, 1),
            "updated_at": datetime(2023, 1, 1),
        }]
        count = await repo.upsert_ads(mock_db, ads)
        assert count == 1
        mock_db.execute.assert_awaited_once()
        mock_db.commit.assert_awaited_once()

    async def test_empty_list(self, repo, mock_db):
        assert await repo.upsert_ads(mock_db, []) == 0


@pytest.mark.asyncio
class TestUpsertInsights:
    async def test_upserts_insights(self, repo, mock_db):
        insights = [{
            "ad_id": "ad1", "date": date(2023, 1, 15),
            "impressions": 1000, "clicks": 50, "spend": 25.50,
            "reach": 800, "frequency": 1.25, "ctr": 5.0, "cpc": 0.51,
            "cpm": 25.50, "conversions": 5, "conversion_value": 100.00,
            "updated_at": datetime(2023, 1, 15),
        }]
        count = await repo.upsert_insights(mock_db, insights)
        assert count == 1
        mock_db.execute.assert_awaited_once()
        mock_db.commit.assert_awaited_once()

    async def test_skips_insight_without_ad_id(self, repo, mock_db):
        insights = [{
            "ad_id": None, "date": date(2023, 1, 15),
            "impressions": 1000, "clicks": 50, "spend": 25.50,
            "reach": 800, "frequency": 1.25, "ctr": 5.0, "cpc": 0.51,
            "cpm": 25.50, "conversions": 5, "conversion_value": 100.00,
            "updated_at": datetime(2023, 1, 15),
        }]
        count = await repo.upsert_insights(mock_db, insights)
        assert count == 0
        mock_db.execute.assert_not_called()

    async def test_skips_insight_without_date(self, repo, mock_db):
        insights = [{
            "ad_id": "ad1", "date": None,
            "impressions": 1000, "clicks": 50, "spend": 25.50,
            "updated_at": datetime(2023, 1, 15),
        }]
        count = await repo.upsert_insights(mock_db, insights)
        assert count == 0
        mock_db.execute.assert_not_called()

    async def test_empty_list(self, repo, mock_db):
        assert await repo.upsert_insights(mock_db, []) == 0


@pytest.mark.asyncio
class TestGetCampaigns:
    async def test_returns_all_without_filter(self, repo, mock_db):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        results = await repo.get_campaigns(mock_db)
        assert results == []

    async def test_filters_by_status(self, repo, mock_db):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        await repo.get_campaigns(mock_db, status="ACTIVE")
        mock_db.execute.assert_awaited_once()


@pytest.mark.asyncio
class TestGetAds:
    async def test_returns_all_without_filter(self, repo, mock_db):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        results = await repo.get_ads(mock_db)
        assert results == []

    async def test_filters_by_campaign_id(self, repo, mock_db):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        await repo.get_ads(mock_db, campaign_id="camp1")
        mock_db.execute.assert_awaited_once()


@pytest.mark.asyncio
class TestGetInsights:
    async def test_returns_all_without_filter(self, repo, mock_db):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        results = await repo.get_insights(mock_db)
        assert results == []

    async def test_filters_by_date_range(self, repo, mock_db):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        await repo.get_insights(mock_db, date_from="2023-01-01", date_to="2023-01-31")
        mock_db.execute.assert_awaited_once()

    async def test_filters_by_campaign_id(self, repo, mock_db):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        await repo.get_insights(mock_db, campaign_id="camp1")
        mock_db.execute.assert_awaited_once()
