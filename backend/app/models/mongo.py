from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# MongoDB client
mongo_client = AsyncIOMotorClient(settings.MONGODB_URI)
mongodb = mongo_client.get_database()  # Gets the database from URI

# Collections
campaigns_raw = mongodb.campaigns_raw
ad_sets_raw = mongodb.ad_sets_raw
ads_raw = mongodb.ads_raw
insights_raw = mongodb.insights_raw

async def close_mongo_connection():
    """Close MongoDB connection."""
    mongo_client.close()