from fastapi import APIRouter, Query
from app.models.schemas import HistoryResponse
from app.services.storage import storage_service

router = APIRouter()

@router.get("/history", response_model=HistoryResponse)
async def get_scan_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    items = storage_service.get_history(limit=limit, offset=offset)
    total = storage_service.get_history_count()
    return HistoryResponse(total=total, items=items)
