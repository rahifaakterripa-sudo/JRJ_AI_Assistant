from fastapi import APIRouter
from app.models.schemas import UsageStats
from app.services.storage import storage_service

router = APIRouter()

@router.get("/usage", response_model=UsageStats)
async def get_usage_statistics():
    return storage_service.get_usage_stats()
