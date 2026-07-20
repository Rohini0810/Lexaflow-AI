from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app import crud
from backend.app.db.database import get_db
from backend.app.schemas import VersionResponse

router = APIRouter(prefix="/versions", tags=["versions"])


@router.get("/{regulation_id}", response_model=list[VersionResponse])
def list_versions(regulation_id: str, db: Session = Depends(get_db)) -> list[VersionResponse]:
    versions = crud.get_versions_for_regulation(db, regulation_id)
    return [
        VersionResponse(
            version_number=version.version_number,
            content_hash=version.content_hash,
            detected_at=version.detected_at,
        )
        for version in versions
    ]


