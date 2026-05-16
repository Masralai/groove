from fastapi import APIRouter

api_router = APIRouter()

# Health check endpoint (already in main.py, but can be moved here)
@api_router.get("/health")
async def health_check():
    return {"status": "ok"}