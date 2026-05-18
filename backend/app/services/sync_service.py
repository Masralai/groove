import asyncio
import logging
from typing import AsyncGenerator, Dict, List, Optional
from datetime import datetime, timedelta, timezone
from app.services.meta_api_service import meta_api_service
from app.models.mongo import campaigns_raw, ad_sets_raw, ads_raw, insights_raw
from app.repositories.mongo_repository import mongo_repository
from app.repositories.postgres_repository import postgres_repository
from app.transform.pipeline import transform_pipeline
from app.core.database import AsyncSessionLocal
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)

class DataSyncService:
    """Service for orchestrating data synchronization from Meta API to MongoDB and PostgreSQL."""
    
    def __init__(self):
        self.meta_api = meta_api_service
        self.mongo_repo = mongo_repository
        self.postgres_repo = postgres_repository
        self.transformer = transform_pipeline
    
    async def _get_last_sync_date(self) -> Optional[datetime]:
        """Get the date of the last successful sync."""
        try:
            # Try to get from a sync_status collection or use default
            # For now, we'll use a simple approach - check the insights_raw collection
            latest_insight = await insights_raw.find_one(
                {},
                sort=[('_stored_at', -1)]
            )
            
            if latest_insight and '_stored_at' in latest_insight:
                return latest_insight['_stored_at']
            
            # Default to 60 days ago for first sync
            return datetime.now(timezone.utc) - timedelta(days=60)
        except Exception as e:
            logger.warning(f"Could not determine last sync date: {e}")
            # Default to 60 days ago
            return datetime.now(timezone.utc) - timedelta(days=60)
    
    async def _get_time_range(self, full_sync: bool = False) -> Dict[str, str]:
        """Get time range for insights fetching."""
        if full_sync:
            # Full sync: last 60 days to today
            since = datetime.now(timezone.utc) - timedelta(days=60)
            until = datetime.now(timezone.utc)
        else:
            # Incremental sync: since last sync to today
            since = await self._get_last_sync_date()
            until = datetime.now(timezone.utc)
        
        # Format for Meta API
        return {
            'since': since.strftime('%Y-%m-%d'),
            'until': until.strftime('%Y-%m-%d')
        }
    
    async def sync_campaigns(self) -> int:
        """Sync campaigns from Meta API to MongoDB and PostgreSQL."""
        logger.info("Starting campaigns sync...")
        
        # Fetch from Meta API
        campaigns = []
        async for campaign in self.meta_api.fetch_campaigns():
            campaigns.append(campaign)
        
        logger.info(f"Fetched {len(campaigns)} campaigns from Meta API")
        
        # Store raw data in MongoDB
        mongo_count = await self.mongo_repo.insert_campaigns(campaigns)
        
        # Transform data
        transformed_campaigns = self.transformer.transform_campaigns(campaigns)
        
        # Upsert to PostgreSQL
        async with AsyncSessionLocal() as db:
            postgres_count = await self.postgres_repo.upsert_campaigns(db, transformed_campaigns)
        
        logger.info(f"Completed campaigns sync: {mongo_count} raw, {postgres_count} transformed")
        return postgres_count
    
    async def sync_ad_sets(self) -> int:
        """Sync ad sets from Meta API to MongoDB and PostgreSQL."""
        logger.info("Starting ad sets sync...")
        
        # Fetch from Meta API
        ad_sets = []
        async for ad_set in self.meta_api.fetch_ad_sets():
            ad_sets.append(ad_set)
        
        logger.info(f"Fetched {len(ad_sets)} ad sets from Meta API")
        
        # Store raw data in MongoDB
        mongo_count = await self.mongo_repo.insert_ad_sets(ad_sets)
        
        # Transform data
        transformed_ad_sets = self.transformer.transform_ad_sets(ad_sets)
        
        # Upsert to PostgreSQL
        async with AsyncSessionLocal() as db:
            postgres_count = await self.postgres_repo.upsert_ad_sets(db, transformed_ad_sets)
        
        logger.info(f"Completed ad sets sync: {mongo_count} raw, {postgres_count} transformed")
        return postgres_count
    
    async def sync_ads(self) -> int:
        """Sync ads from Meta API to MongoDB and PostgreSQL."""
        logger.info("Starting ads sync...")
        
        # Fetch from Meta API
        ads = []
        async for ad in self.meta_api.fetch_ads():
            ads.append(ad)
        
        logger.info(f"Fetched {len(ads)} ads from Meta API")
        
        # Store raw data in MongoDB
        mongo_count = await self.mongo_repo.insert_ads(ads)
        
        # Transform data
        transformed_ads = self.transformer.transform_ads(ads)
        
        # Upsert to PostgreSQL
        async with AsyncSessionLocal() as db:
            postgres_count = await self.postgres_repo.upsert_ads(db, transformed_ads)
        
        logger.info(f"Completed ads sync: {mongo_count} raw, {postgres_count} transformed")
        return postgres_count
    
    async def sync_insights(self, full_sync: bool = False) -> int:
        """Sync insights from Meta API to MongoDB and PostgreSQL."""
        logger.info("Starting insights sync...")
        
        # Get time range
        time_range = await self._get_time_range(full_sync)
        logger.info(f"Fetching insights for time range: {time_range}")
        
        # Fetch from Meta API
        insights = []
        async for insight in self.meta_api.fetch_insights(time_range=time_range):
            insights.append(insight)
        
        logger.info(f"Fetched {len(insights)} insights from Meta API")
        
        # Store raw data in MongoDB
        mongo_count = await self.mongo_repo.insert_insights(insights)
        
        # Transform data
        transformed_insights = self.transformer.transform_insights(insights)
        
        # Upsert to PostgreSQL
        async with AsyncSessionLocal() as db:
            postgres_count = await self.postgres_repo.upsert_insights(db, transformed_insights)
        
        logger.info(f"Completed insights sync: {mongo_count} raw, {postgres_count} transformed")
        return postgres_count
    
    async def sync_all(self, full_sync: bool = False) -> Dict[str, int]:
        """Perform full data synchronization."""
        logger.info(f"Starting full data sync (full_sync={full_sync})")
        
        try:
            # Sync in dependency order: campaigns -> ad_sets -> ads -> insights
            campaigns_count = await self.sync_campaigns()
            ad_sets_count = await self.sync_ad_sets()
            ads_count = await self.sync_ads()
            insights_count = await self.sync_insights(full_sync=full_sync)
            
            result = {
                'campaigns': campaigns_count,
                'ad_sets': ad_sets_count,
                'ads': ads_count,
                'insights': insights_count
            }
            
            logger.info(f"Completed full data sync: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during data sync: {e}")
            raise

# Global service instance
data_sync_service = DataSyncService()