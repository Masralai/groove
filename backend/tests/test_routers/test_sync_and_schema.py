from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.sync_service import SyncAlreadyRunningError

client = TestClient(app)


class TestSyncEndpoints:
    @pytest.fixture(autouse=True)
    def mock_sync_service(self):
        with patch("app.api.v1.router.data_sync_service") as mock:
            mock.sync_all = AsyncMock()
            yield mock

    def test_trigger_data_sync_success(self, mock_sync_service):
        """POST /api/fetch returns success with sync counts."""
        mock_sync_service.sync_all.return_value = {
            "campaigns": 5, "ad_sets": 10, "ads": 15, "insights": 20
        }

        response = client.post("/api/fetch")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["campaigns"] == 5
        assert data["data"]["insights"] == 20
        assert data["full_sync"] is False
        mock_sync_service.sync_all.assert_called_once_with(full_sync=False)

    def test_trigger_data_sync_full(self, mock_sync_service):
        """POST /api/fetch?full=true triggers full re-sync."""
        mock_sync_service.sync_all.return_value = {
            "campaigns": 5, "ad_sets": 10, "ads": 15, "insights": 20
        }

        response = client.post("/api/fetch?full=true")

        assert response.status_code == 200
        assert response.json()["full_sync"] is True
        mock_sync_service.sync_all.assert_called_once_with(full_sync=True)

    def test_trigger_data_sync_error(self, mock_sync_service):
        """POST /api/fetch returns 500 on sync failure."""
        mock_sync_service.sync_all.side_effect = Exception("API Error")

        response = client.post("/api/fetch")

        assert response.status_code == 500
        assert "Sync failed" in response.json()["message"]

    def test_trigger_sync_conflict_when_already_running(self, mock_sync_service):
        """POST /api/fetch returns 409 when sync is already in progress."""
        mock_sync_service.sync_all.side_effect = SyncAlreadyRunningError()

        response = client.post("/api/fetch")

        assert response.status_code == 409
        assert "already in progress" in response.json()["message"].lower()

    def test_get_sync_status(self):
        """GET /api/fetch/status returns sync status."""
        mock_status = {
            "last_sync": "2023-06-15T10:30:00",
            "records_synced": {"campaigns": 5, "ad_sets": 10, "ads": 15, "insights": 20},
            "status": "idle",
        }

        with patch("app.api.v1.router.mongo_repository") as mock_mongo:
            mock_mongo.get_sync_status = AsyncMock(return_value=mock_status)

            response = client.get("/api/fetch/status")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "idle"
            assert data["records_synced"]["campaigns"] == 5


class TestSchemaEndpoint:
    def test_get_schema_returns_ddl(self):
        """GET /api/schema returns DDL string."""
        response = client.get("/api/schema")

        assert response.status_code == 200
        data = response.json()
        assert "schema" in data
        assert "CREATE TABLE campaigns" in data["schema"]
        assert "CREATE TABLE insights" in data["schema"]
