from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.schemas import MonitorRunResponse
from backend.app.services.pipeline_service import process_monitor_run

router = APIRouter(prefix="/monitor", tags=["monitor"])


@router.post("/run", response_model=MonitorRunResponse)
def run_monitor(db: Session = Depends(get_db)) -> MonitorRunResponse:
    try:
        return process_monitor_run(db)
    except FileNotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Monitor run failed: {exc}") from exc


