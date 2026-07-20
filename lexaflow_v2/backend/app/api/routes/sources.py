from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app import crud
from backend.app.db.database import get_db
from backend.app.schemas import SourceUpdateResponse
from backend.app.services.source_service import fetch_regulatory_sources

router = APIRouter(prefix="/sources", tags=["sources"])


@router.post("/fetch", response_model=list[SourceUpdateResponse])
def fetch_sources(
    limit_per_source: int = Query(default=2, ge=1, le=10),
    db: Session = Depends(get_db),
) -> list[SourceUpdateResponse]:
    updates = fetch_regulatory_sources(db, limit_per_source=limit_per_source)
    return [
        SourceUpdateResponse(
            update_id=item["update_id"],
            source=item["source"],
            jurisdiction=item["jurisdiction"],
            title=item["title"],
            link=item["link"],
            published=item["published"],
            is_new_update=bool(item["is_new_update"]),
            is_fallback=bool(item["is_fallback"]),
            fetched_at=item["fetched_at"],
        )
        for item in updates
    ]


@router.get("/recent", response_model=list[SourceUpdateResponse])
def list_recent_sources(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[SourceUpdateResponse]:
    rows = crud.get_recent_source_updates(db, limit=limit)
    return [
        SourceUpdateResponse(
            update_id=row.update_id,
            source=row.source,
            jurisdiction=row.jurisdiction,
            title=row.title,
            link=row.link,
            published=row.published,
            is_new_update=bool(row.is_new_update),
            is_fallback=bool(row.is_fallback),
            fetched_at=row.fetched_at,
        )
        for row in rows
    ]


