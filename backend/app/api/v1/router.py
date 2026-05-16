from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.sync_service import data_sync_service
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict

api_router = APIRouter()

# Health check endpoint
@api_router.get("/health")
async def health_check():
    return {"status": "ok"}

# Data synchronization endpoints
@api_router.post("/fetch")
async def trigger_data_sync(
    full: bool = Query(False, description="Trigger full re-sync instead of incremental"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, int]:
    """Trigger manual data synchronization."""
    try:
        result = await data_sync_service.sync_all(full_sync=full)
        return {
            "status": "success",
            "data": result,
            "full_sync": full
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@api_router.get("/fetch/status")
async def get_sync_status() -> Dict:
    """Get last sync status and statistics."""
    # This would typically query a sync_status table or collection
    # For now, we'll return placeholder data
    return {
        "last_sync": None,
        "records_synced": {
            "campaigns": 0,
            "ad_sets": 0,
            "ads": 0,
            "insights": 0
        },
        "status": "idle"
    }