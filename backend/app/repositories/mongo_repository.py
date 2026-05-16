from typing import List, Dict, Any
from app.models.mongo import (
    campaigns_raw, 
    ad_sets_raw, 
    ads_raw, 
    insights_raw
)
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class MongoRepository:
    """Repository for MongoDB raw data operations."""
    
    async def insert_campaigns(self, campaigns: List[Dict[str, Any]]) -> int:
        """Insert campaigns into MongoDB."""
        if not campaigns:
            return 0
            
        # Add metadata
        for campaign in campaigns:
            campaign['_stored_at'] = datetime.now(timezone.utc)
            
        result = await campaigns_raw.insert_many(campaigns)
        logger.info(f"Inserted {len(result.inserted_ids)} campaigns into MongoDB")
        return len(result.inserted_ids)
    
    async def insert_ad_sets(self, ad_sets: List[Dict[str, Any]]) -> int:
        """Insert ad sets into MongoDB."""
        if not ad_sets:
            return 0
            
        # Add metadata
        for ad_set in ad_sets:
            ad_set['_stored_at'] = datetime.now(timezone.utc)
            
        result = await ad_sets_raw.insert_many(ad_sets)
        logger.info(f"Inserted {len(result.inserted_ids)} ad sets into MongoDB")
        return len(result.inserted_ids)
    
    async def insert_ads(self, ads: List[Dict[str, Any]]) -> int:
        """Insert ads into MongoDB."""
        if not ads:
            return 0
            
        # Add metadata
        for ad in ads:
            ad['_stored_at'] = datetime.now(timezone.utc)
            
        result = await ads_raw.insert_many(ads)
        logger.info(f"Inserted {len(result.inserted_ids)} ads into MongoDB")
        return len(result.inserted_ids)
    
    async def insert_insights(self, insights: List[Dict[str, Any]]) -> int:
        """Insert insights into MongoDB."""
        if not insights:
            return 0
            
        # Add metadata
        for insight in insights:
            insight['_stored_at'] = datetime.now(timezone.utc)
            
        result = await insights_raw.insert_many(insights)
        logger.info(f"Inserted {len(result.inserted_ids)} insights into MongoDB")
        return len(result.inserted_ids)