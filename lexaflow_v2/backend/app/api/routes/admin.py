from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app import crud
from backend.app.db.database import get_db

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/reset")
def reset_demo(db: Session = Depends(get_db)) -> dict:
    crud.reset_demo_database(db)
    db.commit()
    return {"message": "Demo database reset complete"}


