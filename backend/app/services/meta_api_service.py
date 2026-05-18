import asyncio
import logging
from typing import AsyncGenerator, Dict, List, Optional
import time
import random
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.exceptions import FacebookRequestError
from app.core.config import settings

logger = logging.getLogger(__name__)

META_DEFAULT_FIELDS = {
    'campaigns': ['id', 'name', 'status', 'objective', 'daily_budget', 'lifetime_budget', 'created_time', 'start_time', 'stop_time'],
    'ad_sets': ['id', 'name', 'campaign_id', 'status', 'daily_budget', 'lifetime_budget', 'targeting', 'bid_strategy', 'created_time'],
    'ads': ['id', 'name', 'adset_id', 'status', 'creative', 'created_time'],
    'insights': ['impressions', 'clicks', 'spend', 'reach', 'frequency', 'ctr', 'cpc', 'cpm', 'conversions', 'date_start'],
}

class MetaAPIService:
    """Service for interacting with Meta Marketing API using facebook-business SDK."""
    
    def __init__(self):
        self.api_initialized = False
        self.ad_account = None
        
    def _meta_config(self, key: str, default: str | list[str] | dict | None = None):
        return settings.meta_ads.get(key, default) if isinstance(settings.meta_ads, dict) else default

    async def initialize(self):
        """Initialize the Facebook Ads API."""
        if not self.api_initialized:
            api_version = self._meta_config('api_version', 'v22.0')
            FacebookAdsApi.init(
                access_token=settings.META_ACCESS_TOKEN,
                api_version=api_version
            )
            self.ad_account = AdAccount(settings.META_AD_ACCOUNT_ID)
            self.api_initialized = True
            logger.info("Facebook Ads API initialized")
    
    async def _handle_rate_limit(self, attempt: int):
        """Handle rate limiting with exponential backoff."""
        if attempt > 0:
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            logger.warning(f"Rate limit hit, waiting {wait_time:.2f}s before retry {attempt}")
            await asyncio.sleep(wait_time)
    
    async def fetch_campaigns(self, fields: Optional[List[str]] = None) -> AsyncGenerator[Dict, None]:
        """Fetch campaigns with pagination and rate limit handling."""
        await self.initialize()
        
        if fields is None:
            fields = self._meta_config('fields', {}).get('campaigns', META_DEFAULT_FIELDS['campaigns'])
            
        params = {
            'limit': 100
        }

        attempt = 0
        max_retries = 5

        while attempt <= max_retries:
            try:
                campaigns = self.ad_account.get_campaigns(
                    fields=fields,
                    params=params
                )
                
                for campaign in campaigns:
                    yield dict(campaign)
                
                # Reset attempt counter on successful fetch
                attempt = 0
                
                # Check if there are more pages
                # Note: facebook-business SDK handles pagination internally in the iterator
                # For manual cursor handling, we would need to use the RawApiRequest
                break  # Exit retry loop on success
                
            except FacebookRequestError as e:
                if e.api_error_code() == 80003:  # Rate limit error
                    attempt += 1
                    if attempt > max_retries:
                        logger.error(f"Max retries exceeded for campaigns fetch: {e}")
                        raise
                    await self._handle_rate_limit(attempt)
                else:
                    logger.error(f"Facebook API error fetching campaigns: {e}")
                    raise
            except Exception as e:
                logger.error(f"Unexpected error fetching campaigns: {e}")
                raise
    
    async def fetch_ad_sets(self, fields: Optional[List[str]] = None) -> AsyncGenerator[Dict, None]:
        """Fetch ad sets with pagination and rate limit handling."""
        await self.initialize()
        
        if fields is None:
            fields = self._meta_config('fields', {}).get('ad_sets', META_DEFAULT_FIELDS['ad_sets'])
            
        params = {
            'limit': 100
        }

        attempt = 0
        max_retries = 5

        while attempt <= max_retries:
            try:
                ad_sets = self.ad_account.get_ad_sets(
                    fields=fields,
                    params=params
                )
                
                for ad_set in ad_sets:
                    yield dict(ad_set)
                
                attempt = 0
                break
                
            except FacebookRequestError as e:
                if e.api_error_code() == 80003:  # Rate limit error
                    attempt += 1
                    if attempt > max_retries:
                        logger.error(f"Max retries exceeded for ad sets fetch: {e}")
                        raise
                    await self._handle_rate_limit(attempt)
                else:
                    logger.error(f"Facebook API error fetching ad sets: {e}")
                    raise
            except Exception as e:
                logger.error(f"Unexpected error fetching ad sets: {e}")
                raise
    
    async def fetch_ads(self, fields: Optional[List[str]] = None) -> AsyncGenerator[Dict, None]:
        """Fetch ads with pagination and rate limit handling."""
        await self.initialize()
        
        if fields is None:
            fields = self._meta_config('fields', {}).get('ads', META_DEFAULT_FIELDS['ads'])
            
        params = {
            'limit': 100
        }

        attempt = 0
        max_retries = 5

        while attempt <= max_retries:
            try:
                ads = self.ad_account.get_ads(
                    fields=fields,
                    params=params
                )
                
                for ad in ads:
                    yield dict(ad)
                
                attempt = 0
                break
                
            except FacebookRequestError as e:
                if e.api_error_code() == 80003:  # Rate limit error
                    attempt += 1
                    if attempt > max_retries:
                        logger.error(f"Max retries exceeded for ads fetch: {e}")
                        raise
                    await self._handle_rate_limit(attempt)
                else:
                    logger.error(f"Facebook API error fetching ads: {e}")
                    raise
            except Exception as e:
                logger.error(f"Unexpected error fetching ads: {e}")
                raise
    
    async def fetch_insights(
        self, 
        fields: Optional[List[str]] = None,
        time_range: Optional[Dict[str, str]] = None,
        level: str = 'ad'
    ) -> AsyncGenerator[Dict, None]:
        """Fetch insights with pagination, rate limit handling, and time-range filtering."""
        await self.initialize()
        
        if fields is None:
            fields = self._meta_config('fields', {}).get('insights', META_DEFAULT_FIELDS['insights'])
            
        params = {
            'limit': 100,
            'level': level
        }
        
        if time_range:
            params['time_range'] = time_range
        
        attempt = 0
        max_retries = 5
        
        while attempt <= max_retries:
            try:
                insights = self.ad_account.get_insights(
                    fields=fields,
                    params=params
                )
                
                for insight in insights:
                    yield dict(insight)
                
                attempt = 0
                break
                
            except FacebookRequestError as e:
                if e.api_error_code() == 80003:  # Rate limit error
                    attempt += 1
                    if attempt > max_retries:
                        logger.error(f"Max retries exceeded for insights fetch: {e}")
                        raise
                    await self._handle_rate_limit(attempt)
                else:
                    logger.error(f"Facebook API error fetching insights: {e}")
                    raise
            except Exception as e:
                logger.error(f"Unexpected error fetching insights: {e}")
                raise

# Global service instance
meta_api_service = MetaAPIService()