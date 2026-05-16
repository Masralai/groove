from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def transform_campaign(raw_campaign: Dict[str, Any]) -> Dict[str, Any]:
    """Transform raw campaign data to normalized record."""
    return {
        'id': raw_campaign.get('id'),
        'name': raw_campaign.get('name'),
        'status': raw_campaign.get('status'),
        'objective': raw_campaign.get('objective'),
        'daily_budget': raw_campaign.get('daily_budget'),
        'lifetime_budget': raw_campaign.get('lifetime_budget'),
        'created_time': raw_campaign.get('created_time'),
        'start_time': raw_campaign.get('start_time'),
        'stop_time': raw_campaign.get('stop_time'),
        'updated_at': datetime.utcnow()
    }

def transform_ad_set(raw_ad_set: Dict[str, Any]) -> Dict[str, Any]:
    """Transform raw ad set data to normalized record."""
    return {
        'id': raw_ad_set.get('id'),
        'campaign_id': raw_ad_set.get('campaign_id'),
        'name': raw_ad_set.get('name'),
        'status': raw_ad_set.get('status'),
        'daily_budget': raw_ad_set.get('daily_budget'),
        'lifetime_budget': raw_ad_set.get('lifetime_budget'),
        'targeting': raw_ad_set.get('targeting'),
        'bid_strategy': raw_ad_set.get('bid_strategy'),
        'created_time': raw_ad_set.get('created_time'),
        'updated_at': datetime.utcnow()
    }

def transform_ad(raw_ad: Dict[str, Any]) -> Dict[str, Any]:
    """Transform raw ad data to normalized record."""
    return {
        'id': raw_ad.get('id'),
        'ad_set_id': raw_ad.get('ad_set_id'),
        'name': raw_ad.get('name'),
        'status': raw_ad.get('status'),
        'creative': raw_ad.get('creative'),
        'created_time': raw_ad.get('created_time'),
        'updated_at': datetime.utcnow()
    }

def transform_insight(raw_insight: Dict[str, Any]) -> Dict[str, Any]:
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
    
    return {
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
        'updated_at': datetime.utcnow()
    }

class TransformPipeline:
    """Pipeline for transforming raw API data to normalized records."""
    
    @staticmethod
    def transform_campaigns(raw_campaigns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform multiple campaigns."""
        return [transform_campaign(campaign) for campaign in raw_campaigns]
    
    @staticmethod
    def transform_ad_sets(raw_ad_sets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform multiple ad sets."""
        return [transform_ad_set(ad_set) for ad_set in raw_ad_sets]
    
    @staticmethod
    def transform_ads(raw_ads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform multiple ads."""
        return [transform_ad(ad) for ad in raw_ads]
    
    @staticmethod
    def transform_insights(raw_insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform multiple insights."""
        return [transform_insight(insight) for insight in raw_insights]

# Global instance
transform_pipeline = TransformPipeline()