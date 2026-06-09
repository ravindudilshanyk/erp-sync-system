from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.schemas import SyncResult, SyncStateResponse
from app.services.sync_service import (
    run_full_sync,
    run_delta_sync,
    get_or_create_sync_state
)

router = APIRouter()

@router.post(
    "/full",
    response_model=SyncResult,
    summary="Run Full Synchronization",
    description="Imports ALL products from ERP regardless of revision. Use this for first run or to force a complete refresh."
)
def full_sync(db: Session = Depends(get_db)):
    try:
        result = run_full_sync(db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Full sync failed: {str(e)}"
        )


@router.post(
    "/delta",
    response_model=SyncResult,
    summary="Run Delta Synchronization",
    description="Imports only products changed since the last successful sync. Uses revision watermarks stored in sync state."
)
def delta_sync(db: Session = Depends(get_db)):
    try:
        result = run_delta_sync(db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delta sync failed: {str(e)}"
        )


@router.get(
    "/status",
    response_model=SyncStateResponse,
    summary="Get Sync Status",
    description="Returns the current synchronization state including last revision, record counts, and any errors."
)
def get_sync_status(db: Session = Depends(get_db)):
    state = get_or_create_sync_state(db)
    return state