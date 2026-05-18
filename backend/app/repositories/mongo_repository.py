from typing import List, Dict, Any, Optional
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

    async def get_sync_status(self) -> Dict[str, Any]:
        """Get sync status with record counts and last sync time per collection."""
        collections = {
            "campaigns": campaigns_raw,
            "ad_sets": ad_sets_raw,
            "ads": ads_raw,
            "insights": insights_raw,
        }
        records_synced = {}
        last_sync: Optional[datetime] = None

        for name, col in collections.items():
            count = await col.count_documents({})
            latest = await col.find_one({}, sort=[("_stored_at", -1)])
            records_synced[name] = count
            if latest and "_stored_at" in latest:
                stored = latest["_stored_at"]
                if last_sync is None or stored > last_sync:
                    last_sync = stored

        return {
            "last_sync": last_sync.isoformat() if last_sync else None,
            "records_synced": records_synced,
            "status": "idle",
        }

# Global instance
mongo_repository = MongoRepository()