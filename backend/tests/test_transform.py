from datetime import date, datetime
from unittest.mock import MagicMock

from app.transform.pipeline import (
    TransformPipeline,
    _parse_datetime,
    _prepare_record,
    _serialize,
    transform_ad,
    transform_ad_set,
    transform_campaign,
    transform_insight,
)


class TestParseDatetime:
    def test_iso_format_with_timezone(self):
        result = _parse_datetime("2023-01-15T10:30:00+00:00")
        assert result is not None
        assert result.year == 2023
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30
        assert result.tzinfo is None

    def test_iso_format_with_ms(self):
        result = _parse_datetime("2023-01-15T10:30:00.123+00:00")
        assert result is not None
        assert result.year == 2023

    def test_iso_format_zulu(self):
        result = _parse_datetime("2023-01-15T10:30:00Z")
        assert result is not None
        assert result.year == 2023

    def test_none_returns_none(self):
        assert _parse_datetime(None) is None

    def test_datetime_passthrough(self):
        dt = datetime(2023, 1, 15, 10, 30)
        result = _parse_datetime(dt)
        assert result == dt

    def test_malformed_string_returns_none(self):
        assert _parse_datetime("not-a-date") is None

    def test_empty_string_returns_none(self):
        assert _parse_datetime("") is None


class TestSerialize:
    def test_none(self):
        assert _serialize(None) is None

    def test_primitives(self):
        assert _serialize("hello") == "hello"
        assert _serialize(42) == 42
        assert _serialize(3.14) == 3.14
        assert _serialize(True) is True

    def test_datetime_serializes_to_iso(self):
        dt = datetime(2023, 1, 15, 10, 30, 0)
        assert _serialize(dt) == "2023-01-15T10:30:00"

    def test_dict_serializes_recursively(self):
        val = {"a": 1, "b": {"c": datetime(2023, 1, 1, 0, 0)}}
        result = _serialize(val)
        assert result == {"a": 1, "b": {"c": "2023-01-01T00:00:00"}}

    def test_list_serializes_recursively(self):
        val = [1, "two", datetime(2023, 1, 1, 0, 0)]
        result = _serialize(val)
        assert result == [1, "two", "2023-01-01T00:00:00"]

    def test_object_with_export_all_data(self):
        obj = MagicMock()
        obj.export_all_data.return_value = {"key": "value"}
        result = _serialize(obj)
        assert result == {"key": "value"}

    def test_object_with_dict(self):
        obj = MagicMock()
        obj.__dict__ = {"name": "test"}
        result = _serialize(obj)
        assert result == {"name": "test"}

    def test_fallback_to_string(self):
        class CustomObj:
            __slots__ = ()
            def __str__(self):
                return "custom"
        assert _serialize(CustomObj()) == "custom"


class TestTransformCampaign:
    def test_transforms_all_fields(self):
        raw = {
            "id": "123",
            "name": "Test Campaign",
            "status": "ACTIVE",
            "objective": "OUTCOME_TRAFFIC",
            "daily_budget": 10000,
            "lifetime_budget": 100000,
            "created_time": "2023-01-01T00:00:00+00:00",
            "start_time": "2023-01-15T00:00:00+00:00",
            "stop_time": None,
        }
        result = transform_campaign(raw)
        assert result["id"] == "123"
        assert result["name"] == "Test Campaign"
        assert result["status"] == "ACTIVE"
        assert result["objective"] == "OUTCOME_TRAFFIC"
        assert result["daily_budget"] == 10000
        assert result["lifetime_budget"] == 100000
        assert result["created_time"] is not None
        assert result["start_time"] is not None
        assert result["stop_time"] is None
        assert "updated_at" in result

    def test_handles_missing_fields_gracefully(self):
        result = transform_campaign({"id": "123"})
        assert result["id"] == "123"
        assert result["name"] is None
        assert result["objective"] is None


class TestTransformAdSet:
    def test_transforms_all_fields(self):
        raw = {
            "id": "adset1",
            "campaign_id": "camp1",
            "name": "Test Ad Set",
            "status": "ACTIVE",
            "daily_budget": 5000,
            "lifetime_budget": 50000,
            "targeting": {"geo_locations": {"countries": ["US"]}},
            "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
            "created_time": "2023-01-01T00:00:00+00:00",
        }
        result = transform_ad_set(raw)
        assert result["id"] == "adset1"
        assert result["campaign_id"] == "camp1"
        assert result["targeting"] is not None
        assert result["bid_strategy"] == "LOWEST_COST_WITHOUT_CAP"
        assert "updated_at" in result

    def test_serializes_targeting_to_json(self):
        raw = {"id": "1", "targeting": {"countries": ["US"]}}
        result = transform_ad_set(raw)
        assert result["targeting"] == '{"countries": ["US"]}'


class TestTransformAd:
    def test_transforms_all_fields(self):
        raw = {
            "id": "ad1",
            "adset_id": "adset1",
            "name": "Test Ad",
            "status": "ACTIVE",
            "creative": {"id": "cre1", "title": "Hello"},
            "created_time": "2023-01-01T00:00:00+00:00",
        }
        result = transform_ad(raw)
        assert result["id"] == "ad1"
        assert result["ad_set_id"] == "adset1"
        assert result["name"] == "Test Ad"
        assert result["creative"] is not None
        assert "updated_at" in result

    def test_handles_ad_set_id_field_variants(self):
        raw_with_adset_id = {"id": "1", "adset_id": "adset1"}
        assert transform_ad(raw_with_adset_id)["ad_set_id"] == "adset1"

        raw_with_ad_set_id = {"id": "1", "ad_set_id": "adset2"}
        assert transform_ad(raw_with_ad_set_id)["ad_set_id"] == "adset2"

    def test_serializes_creative_to_json(self):
        raw = {"id": "1", "creative": {"id": "cre1"}}
        result = transform_ad(raw)
        assert result["creative"] == '{"id": "cre1"}'


class TestTransformInsight:
    def test_transforms_all_fields(self):
        raw = {
            "ad_id": "ad1",
            "date_start": "2023-01-15",
            "impressions": 1000,
            "clicks": 50,
            "spend": 25.50,
            "reach": 800,
            "frequency": 1.25,
            "ctr": 5.0,
            "cpc": 0.51,
            "cpm": 25.50,
            "conversions": 5,
            "conversion_value": 100.00,
        }
        result = transform_insight(raw)
        assert result["ad_id"] == "ad1"
        assert result["date"] == date(2023, 1, 15)
        assert result["impressions"] == 1000
        assert result["clicks"] == 50
        assert result["spend"] == 25.50
        assert "updated_at" in result

    def test_includes_ad_id(self):
        result = transform_insight({"ad_id": "ad1", "date_start": "2023-01-15"})
        assert result["ad_id"] == "ad1"

    def test_no_ad_id_returns_none(self):
        result = transform_insight({"date_start": "2023-01-15"})
        assert result["ad_id"] is None

    def test_handles_date_field_variants(self):
        r1 = transform_insight({"ad_id": "1", "date_start": "2023-01-15"})
        assert r1["date"] == date(2023, 1, 15)

        r2 = transform_insight({"ad_id": "1", "date": "2023-01-20"})
        assert r2["date"] == date(2023, 1, 20)

    def test_missing_date_returns_none(self):
        result = transform_insight({"ad_id": "1"})
        assert result["date"] is None

    def test_empty_fields(self):
        result = transform_insight({"ad_id": "1", "date_start": "2023-01-15"})
        assert result["impressions"] is None
        assert result["clicks"] is None


class TestPrepareRecord:
    def test_json_dumps_targeting_field(self):
        record = {"targeting": {"countries": ["US"]}, "name": "test"}
        result = _prepare_record(record)
        assert result["targeting"] == '{"countries": ["US"]}'
        assert result["name"] == "test"

    def test_json_dumps_creative_field(self):
        record = {"creative": {"id": "1"}, "name": "test"}
        result = _prepare_record(record)
        assert result["creative"] == '{"id": "1"}'
        assert result["name"] == "test"

    def test_passthrough_for_non_json_fields(self):
        record = {"id": "1", "name": "test", "status": "ACTIVE"}
        result = _prepare_record(record)
        assert result == record


class TestTransformPipeline:
    def test_transform_campaigns_batch(self):
        raw = [{"id": "1", "name": "C1"}, {"id": "2", "name": "C2"}]
        results = TransformPipeline.transform_campaigns(raw)
        assert len(results) == 2
        assert results[0]["id"] == "1"
        assert results[1]["id"] == "2"

    def test_transform_ad_sets_batch(self):
        raw = [{"id": "1"}, {"id": "2"}]
        results = TransformPipeline.transform_ad_sets(raw)
        assert len(results) == 2

    def test_transform_ads_batch(self):
        raw = [{"id": "1"}, {"id": "2"}]
        results = TransformPipeline.transform_ads(raw)
        assert len(results) == 2

    def test_transform_insights_batch(self):
        raw = [
            {"ad_id": "1", "date_start": "2023-01-15"},
            {"ad_id": "2", "date_start": "2023-01-16"},
        ]
        results = TransformPipeline.transform_insights(raw)
        assert len(results) == 2
        assert results[0]["ad_id"] == "1"
        assert results[1]["ad_id"] == "2"
