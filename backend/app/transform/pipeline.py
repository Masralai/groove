import json
import logging
import re
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

def _parse_datetime(val: Any) -> datetime | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if not isinstance(val, str):
        return None
    cleaned = val.strip()
    cleaned = re.sub(r'(\+\d{2}):(\d{2})$', r'\1\2', cleaned)
    cleaned = re.sub(r'\+00:?00$', 'Z', cleaned)
    if cleaned.endswith('Z'):
        cleaned = cleaned[:-1] + '+0000'
    for fmt in ['%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%S.%f%z']:
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.astimezone(UTC).replace(tzinfo=None)
        except (ValueError, OverflowError):
            continue
    logger.warning(f"Could not parse datetime: {val}")
    return None

def transform_campaign(raw_campaign: dict[str, Any]) -> dict[str, Any]:
    """Transform raw campaign data to normalized record."""
    return {
        'id': raw_campaign.get('id'),
        'name': raw_campaign.get('name'),
        'status': raw_campaign.get('status'),
        'objective': raw_campaign.get('objective'),
        'daily_budget': raw_campaign.get('daily_budget'),
        'lifetime_budget': raw_campaign.get('lifetime_budget'),
        'created_time': _parse_datetime(raw_campaign.get('created_time')),
        'start_time': _parse_datetime(raw_campaign.get('start_time')),
        'stop_time': _parse_datetime(raw_campaign.get('stop_time')),
        'updated_at': datetime.now(UTC)
    }

def _serialize(val: Any) -> Any:
    if val is None:
        return None
    if isinstance(val, (str, int, float, bool)):
        return val
    if isinstance(val, datetime):
        return val.isoformat()
    if hasattr(val, 'export_all_data'):
        return _serialize(val.export_all_data())
    if isinstance(val, dict):
        return {k: _serialize(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [_serialize(v) for v in val]
    if hasattr(val, '__dict__'):
        return _serialize(val.__dict__)
    try:
        return str(val)
    except Exception:
        return None

_JSON_DUMP_FIELDS = {'targeting', 'creative'}

def _prepare_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        k: json.dumps(v) if k in _JSON_DUMP_FIELDS and not isinstance(v, str) else v
        for k, v in record.items()
    }

def transform_ad_set(raw_ad_set: dict[str, Any]) -> dict[str, Any]:
    """Transform raw ad set data to normalized record."""
    return _prepare_record({
        'id': raw_ad_set.get('id'),
        'campaign_id': raw_ad_set.get('campaign_id'),
        'name': raw_ad_set.get('name'),
        'status': raw_ad_set.get('status'),
        'daily_budget': raw_ad_set.get('daily_budget'),
        'lifetime_budget': raw_ad_set.get('lifetime_budget'),
        'targeting': _serialize(raw_ad_set.get('targeting')),
        'bid_strategy': raw_ad_set.get('bid_strategy'),
        'created_time': _parse_datetime(raw_ad_set.get('created_time')),
        'updated_at': datetime.now(UTC)
    })

def transform_ad(raw_ad: dict[str, Any]) -> dict[str, Any]:
    """Transform raw ad data to normalized record."""
    return _prepare_record({
        'id': raw_ad.get('id'),
        'ad_set_id': raw_ad.get('adset_id') or raw_ad.get('ad_set_id'),
        'name': raw_ad.get('name'),
        'status': raw_ad.get('status'),
        'creative': _serialize(raw_ad.get('creative')),
        'created_time': _parse_datetime(raw_ad.get('created_time')),
        'updated_at': datetime.now(UTC)
    })

def transform_insight(raw_insight: dict[str, Any]) -> dict[str, Any]:
    """Transform raw insight data to normalized record."""
    # Handle date field - Meta API might return date_start/date_stop
    date_val = raw_insight.get('date_start') or raw_insight.get('date')
    if date_val:
        # Convert to date object if it's a string
        if isinstance(date_val, str):
            try:
                date_val = datetime.strptime(date_val, '%Y-%m-%d').date()
            except ValueError:
                # If parsing fails, keep as string
                pass

    ad_id = raw_insight.get('ad_id')

    return {
        'ad_id': ad_id,
        'date': date_val,
        'impressions': raw_insight.get('impressions'),
        'clicks': raw_insight.get('clicks'),
        'spend': raw_insight.get('spend'),
        'reach': raw_insight.get('reach'),
        'frequency': raw_insight.get('frequency'),
        'ctr': raw_insight.get('ctr'),
        'cpc': raw_insight.get('cpc'),
        'cpm': raw_insight.get('cpm'),
        'conversions': raw_insight.get('conversions'),
        'conversion_value': raw_insight.get('conversion_value'),
        'updated_at': datetime.now(UTC)
    }

class TransformPipeline:
    """Pipeline for transforming raw API data to normalized records."""

    @staticmethod
    def transform_campaigns(raw_campaigns: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Transform multiple campaigns."""
        return [transform_campaign(campaign) for campaign in raw_campaigns]

    @staticmethod
    def transform_ad_sets(raw_ad_sets: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Transform multiple ad sets."""
        return [transform_ad_set(ad_set) for ad_set in raw_ad_sets]

    @staticmethod
    def transform_ads(raw_ads: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Transform multiple ads."""
        return [transform_ad(ad) for ad in raw_ads]

    @staticmethod
    def transform_insights(raw_insights: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Transform multiple insights."""
        return [transform_insight(insight) for insight in raw_insights]

# Global instance
transform_pipeline = TransformPipeline()
