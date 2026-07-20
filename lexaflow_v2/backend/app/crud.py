import hashlib
import json
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.db.models import Action, Analysis, MonitorRun, Regulation, SourceUpdate, Version
from backend.app.schemas import AnalysisResult


def get_regulation(db: Session, regulation_id: str) -> Regulation | None:
    return db.get(Regulation, regulation_id)


def get_current_regulation_hash(db: Session, regulation_id: str) -> str | None:
    regulation = get_regulation(db, regulation_id)
    return regulation.current_hash if regulation else None


def upsert_regulation(
    db: Session,
    *,
    regulation_id: str,
    title: str,
    source: str,
    jurisdiction: str,
    current_version: int,
    current_hash: str,
    status: str,
) -> Regulation:
    regulation = get_regulation(db, regulation_id)
    if regulation is None:
        regulation = Regulation(
            regulation_id=regulation_id,
            title=title,
            source=source,
            jurisdiction=jurisdiction,
            current_version=current_version,
            current_hash=current_hash,
            status=status,
            last_updated_at=datetime.utcnow(),
        )
        db.add(regulation)
    else:
        regulation.current_version = current_version
        regulation.current_hash = current_hash
        regulation.status = status
        regulation.last_updated_at = datetime.utcnow()
    db.flush()
    return regulation


def get_version_by_hash(db: Session, regulation_id: str, content_hash: str) -> Version | None:
    stmt = select(Version).where(
        Version.regulation_id == regulation_id,
        Version.content_hash == content_hash,
    )
    return db.scalar(stmt)


def get_latest_version_number(db: Session, regulation_id: str) -> int:
    stmt = select(func.max(Version.version_number)).where(Version.regulation_id == regulation_id)
    latest = db.scalar(stmt)
    return int(latest or 0)


def ensure_version(
    db: Session,
    *,
    regulation_id: str,
    content_hash: str,
    blob_path: str,
    preferred_version_number: int | None = None,
) -> Version:
    existing = get_version_by_hash(db, regulation_id, content_hash)
    if existing:
        return existing

    if preferred_version_number is not None:
        version_number = preferred_version_number
    else:
        version_number = get_latest_version_number(db, regulation_id) + 1

    version = Version(
        regulation_id=regulation_id,
        version_number=version_number,
        content_hash=content_hash,
        blob_path=blob_path,
        detected_at=datetime.utcnow(),
    )
    db.add(version)
    db.flush()
    return version


def create_monitor_run(
    db: Session,
    *,
    regulation_id: str,
    old_hash: str,
    new_hash: str,
    change_detected: bool,
    status: str = "completed",
    error_message: str | None = None,
) -> MonitorRun:
    run = MonitorRun(
        regulation_id=regulation_id,
        old_hash=old_hash,
        new_hash=new_hash,
        change_detected=change_detected,
        status=status,
        error_message=error_message,
        created_at=datetime.utcnow(),
    )
    db.add(run)
    db.flush()
    return run


def get_analysis_by_hash(db: Session, regulation_id: str, content_hash: str) -> Analysis | None:
    stmt = select(Analysis).where(
        Analysis.regulation_id == regulation_id,
        Analysis.content_hash == content_hash,
    )
    return db.scalar(stmt)


def save_analysis_and_actions(
    db: Session,
    *,
    regulation_id: str,
    content_hash: str,
    analysis_result: AnalysisResult,
) -> dict:
    existing_analysis = get_analysis_by_hash(db, regulation_id, content_hash)
    if existing_analysis is not None:
        return {
            "analysis_id": existing_analysis.analysis_id,
            "inserted_actions": 0,
            "skipped_duplicates": 0,
            "already_analyzed": True,
        }

    analysis = Analysis(
        regulation_id=regulation_id,
        content_hash=content_hash,
        what_changed=json.dumps(analysis_result.what_changed),
        business_impact=json.dumps(analysis_result.business_impact),
        risk_level=str(analysis_result.risk_level).lower(),
        affected_teams=json.dumps(analysis_result.affected_teams),
        recommended_actions=json.dumps([item.model_dump() for item in analysis_result.recommended_actions]),
        confidence_score=float(analysis_result.confidence_score),
        created_at=datetime.utcnow(),
    )
    db.add(analysis)
    db.flush()

    inserted_count = 0
    skipped_count = 0

    for recommendation in analysis_result.recommended_actions:
        action_text = recommendation.action.strip()
        owner = recommendation.owner.strip() or "Unassigned"
        priority = recommendation.priority.strip().title() or "Medium"
        due_days = max(1, int(recommendation.due_days))

        signature_seed = f"{regulation_id}|{content_hash}|{action_text.lower()}"
        signature = hashlib.sha256(signature_seed.encode("utf-8")).hexdigest()

        exists_stmt = select(Action.action_id).where(Action.action_signature == signature)
        if db.scalar(exists_stmt) is not None:
            skipped_count += 1
            continue

        action = Action(
            regulation_id=regulation_id,
            content_hash=content_hash,
            action_signature=signature,
            action_text=action_text,
            owner=owner,
            priority=priority,
            status="Not Started",
            due_date=f"{due_days} days",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(action)
        inserted_count += 1

    db.flush()

    return {
        "analysis_id": analysis.analysis_id,
        "inserted_actions": inserted_count,
        "skipped_duplicates": skipped_count,
        "already_analyzed": False,
    }


def get_pending_actions_for_regulation(db: Session, regulation_id: str) -> list[Action]:
    stmt = (
        select(Action)
        .where(Action.regulation_id == regulation_id, Action.status != "Completed")
        .order_by(Action.action_id.desc())
    )
    return list(db.scalars(stmt).all())


def get_carryover_actions(db: Session, regulation_id: str, current_hash: str) -> list[Action]:
    stmt = (
        select(Action)
        .where(
            Action.regulation_id == regulation_id,
            Action.content_hash != current_hash,
            Action.status != "Completed",
        )
        .order_by(Action.action_id.desc())
    )
    return list(db.scalars(stmt).all())


def get_actions(db: Session, status_filter: str | None = None) -> list[tuple[Action, Regulation | None]]:
    stmt = select(Action, Regulation).join(
        Regulation, Action.regulation_id == Regulation.regulation_id, isouter=True
    )

    if status_filter == "open":
        stmt = stmt.where(Action.status != "Completed")
    elif status_filter == "completed":
        stmt = stmt.where(Action.status == "Completed")

    stmt = stmt.order_by(Action.action_id.desc())
    return list(db.execute(stmt).all())


def update_action(db: Session, action_id: int, status: str | None, due_date: str | None) -> Action | None:
    action = db.get(Action, action_id)
    if action is None:
        return None

    if status is not None:
        action.status = status
    if due_date is not None:
        action.due_date = due_date
    action.updated_at = datetime.utcnow()
    db.flush()
    return action


def get_versions_for_regulation(db: Session, regulation_id: str) -> list[Version]:
    stmt = (
        select(Version)
        .where(Version.regulation_id == regulation_id)
        .order_by(Version.version_number.asc())
    )
    return list(db.scalars(stmt).all())


def _source_content_hash(update: dict) -> str:
    raw = f"{update['source']}|{update['title']}|{update['link']}|{update['published']}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def save_source_update(db: Session, update: dict) -> SourceUpdate:
    content_hash = _source_content_hash(update)

    exists_stmt = select(SourceUpdate.update_id).where(
        SourceUpdate.source == update["source"],
        SourceUpdate.content_hash == content_hash,
    )
    already_seen = db.scalar(exists_stmt) is not None

    source_update = SourceUpdate(
        source=update["source"],
        jurisdiction=update["jurisdiction"],
        title=update["title"],
        link=update["link"],
        published=update["published"],
        content_hash=content_hash,
        is_new_update=not already_seen,
        is_fallback=bool(update.get("is_fallback", False)),
        fetched_at=datetime.utcnow(),
    )
    db.add(source_update)
    db.flush()
    return source_update


def get_recent_source_updates(db: Session, limit: int = 20) -> list[SourceUpdate]:
    stmt = select(SourceUpdate).order_by(SourceUpdate.fetched_at.desc()).limit(limit)
    return list(db.scalars(stmt).all())


def get_dashboard_summary(db: Session) -> dict:
    regulations_monitored = db.scalar(select(func.count()).select_from(Regulation)) or 0
    source_updates = (
        db.scalar(
            select(func.count()).select_from(SourceUpdate).where(SourceUpdate.is_new_update.is_(True))
        )
        or 0
    )
    high_risk_count = (
        db.scalar(
            select(func.count()).select_from(Analysis).where(func.lower(Analysis.risk_level) == "high")
        )
        or 0
    )
    pending_actions = (
        db.scalar(select(func.count()).select_from(Action).where(Action.status != "Completed"))
        or 0
    )
    return {
        "regulations_monitored": int(regulations_monitored),
        "source_updates": int(source_updates),
        "high_risk_count": int(high_risk_count),
        "pending_actions": int(pending_actions),
    }


def reset_demo_database(db: Session) -> None:
    db.query(Action).delete()
    db.query(Analysis).delete()
    db.query(Version).delete()
    db.query(Regulation).delete()
    db.query(SourceUpdate).delete()
    db.query(MonitorRun).delete()
    db.flush()

