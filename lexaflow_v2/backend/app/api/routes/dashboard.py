from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app import crud
from backend.app.db.database import get_db
from backend.app.schemas import DashboardSummaryResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummaryResponse:
    return DashboardSummaryResponse(**crud.get_dashboard_summary(db))


