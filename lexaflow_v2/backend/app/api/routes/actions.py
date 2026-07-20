from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app import crud
from backend.app.db.database import get_db
from backend.app.schemas import ActionItemResponse, ActionUpdateRequest

router = APIRouter(prefix="/actions", tags=["actions"])


@router.get("", response_model=list[ActionItemResponse])
def list_actions(
    status: str = Query(default="all", pattern="^(all|open|completed)$"),
    db: Session = Depends(get_db),
) -> list[ActionItemResponse]:
    status_filter = None if status == "all" else status
    rows = crud.get_actions(db, status_filter=status_filter)

    response: list[ActionItemResponse] = []
    for action, regulation in rows:
        response.append(
            ActionItemResponse(
                action_id=action.action_id,
                regulation_id=action.regulation_id,
                action_text=action.action_text,
                owner=action.owner,
                priority=action.priority,
                status=action.status,
                due_date=action.due_date,
                source=regulation.source if regulation else None,
                last_updated_at=regulation.last_updated_at if regulation else None,
                created_at=action.created_at,
            )
        )
    return response


@router.patch("/{action_id}", response_model=ActionItemResponse)
def update_action(
    action_id: int,
    payload: ActionUpdateRequest,
    db: Session = Depends(get_db),
) -> ActionItemResponse:
    action = crud.update_action(db, action_id, payload.status, payload.due_date)
    if action is None:
        raise HTTPException(status_code=404, detail=f"Action {action_id} not found")
    db.commit()

    regulation = crud.get_regulation(db, action.regulation_id)
    return ActionItemResponse(
        action_id=action.action_id,
        regulation_id=action.regulation_id,
        action_text=action.action_text,
        owner=action.owner,
        priority=action.priority,
        status=action.status,
        due_date=action.due_date,
        source=regulation.source if regulation else None,
        last_updated_at=regulation.last_updated_at if regulation else None,
        created_at=action.created_at,
    )


