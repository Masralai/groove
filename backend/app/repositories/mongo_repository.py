import logging
from datetime import UTC, datetime
from typing import Any

from app.models.mongo import ad_sets_raw, ads_raw, campaigns_raw, insights_raw

logger = logging.getLogger(__name__)

class MongoRepository:
    """Repository for MongoDB raw data operations."""

    async def insert_campaigns(self, campaigns: list[dict[str, Any]]) -> int:
        """Insert campaigns into MongoDB."""
        if not campaigns:
            return 0

        # Add metadata
        for campaign in campaigns:
            campaign['_stored_at'] = datetime.now(UTC)

        result = await campaigns_raw.insert_many(campaigns)
        logger.info(f"Inserted {len(result.inserted_ids)} campaigns into MongoDB")
        return len(result.inserted_ids)

    async def insert_ad_sets(self, ad_sets: list[dict[str, Any]]) -> int:
        """Insert ad sets into MongoDB."""
        if not ad_sets:
            return 0

        # Add metadata
        for ad_set in ad_sets:
            ad_set['_stored_at'] = datetime.now(UTC)

        result = await ad_sets_raw.insert_many(ad_sets)
        logger.info(f"Inserted {len(result.inserted_ids)} ad sets into MongoDB")
        return len(result.inserted_ids)

    async def insert_ads(self, ads: list[dict[str, Any]]) -> int:
        """Insert ads into MongoDB."""
        if not ads:
            return 0

        # Add metadata
        for ad in ads:
            ad['_stored_at'] = datetime.now(UTC)

        result = await ads_raw.insert_many(ads)
        logger.info(f"Inserted {len(result.inserted_ids)} ads into MongoDB")
        return len(result.inserted_ids)

    async def insert_insights(self, insights: list[dict[str, Any]]) -> int:
        """Insert insights into MongoDB."""
        if not insights:
            return 0

        # Add metadata
        for insight in insights:
            insight['_stored_at'] = datetime.now(UTC)

        result = await insights_raw.insert_many(insights)
        logger.info(f"Inserted {len(result.inserted_ids)} insights into MongoDB")
        return len(result.inserted_ids)

    async def get_sync_status(self) -> dict[str, Any]:
        """Get sync status with record counts and last sync time per collection."""
        collections = {
            "campaigns": campaigns_raw,
            "ad_sets": ad_sets_raw,
            "ads": ads_raw,
            "insights": insights_raw,
        }
        records_synced = {}
        last_sync: datetime | None = None

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
