from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app import crud
from backend.app.core.config import settings
from backend.app.db.database import get_db

router = APIRouter(prefix="/regulations", tags=["regulations"])


class RegulationResponse(BaseModel):
    regulation_id: str
    title: str
    source: str
    jurisdiction: str
    current_version: int
    current_hash: str
    status: str
    last_updated_at: datetime | None = None


@router.get("/current", response_model=RegulationResponse)
def get_current_regulation(db: Session = Depends(get_db)) -> RegulationResponse:
    row = crud.get_regulation(db, settings.monitored_regulation_id)
    if row is None:
        return RegulationResponse(
            regulation_id=settings.monitored_regulation_id,
            title=settings.monitored_regulation_title,
            source=settings.monitored_source,
            jurisdiction=settings.monitored_jurisdiction,
            current_version=0,
            current_hash="",
            status="Not Initialized",
            last_updated_at=None,
        )

    return RegulationResponse(
        regulation_id=row.regulation_id,
        title=row.title,
        source=row.source,
        jurisdiction=row.jurisdiction,
        current_version=row.current_version,
        current_hash=row.current_hash,
        status=row.status,
        last_updated_at=row.last_updated_at,
    )


