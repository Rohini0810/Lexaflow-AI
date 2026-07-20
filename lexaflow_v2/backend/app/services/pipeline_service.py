from sqlalchemy.orm import Session

from backend.app import crud
from backend.app.core.config import settings
from backend.app.schemas import MonitorRunResponse
from backend.app.services.analysis_service import analyze_regulatory_change
from backend.app.services.document_service import extract_text
from backend.app.services.hashing import generate_hash


def process_monitor_run(db: Session) -> MonitorRunResponse:
    regulation_id = settings.monitored_regulation_id
    title = settings.monitored_regulation_title
    source = settings.monitored_source
    jurisdiction = settings.monitored_jurisdiction

    old_text = extract_text(settings.old_doc_path)
    new_text = extract_text(settings.new_doc_path)

    old_hash = generate_hash(old_text)
    new_hash = generate_hash(new_text)

    existing_regulation = crud.get_regulation(db, regulation_id)
    if existing_regulation is None:
        crud.upsert_regulation(
            db,
            regulation_id=regulation_id,
            title=title,
            source=source,
            jurisdiction=jurisdiction,
            current_version=1,
            current_hash=old_hash,
            status="Baseline Loaded",
        )
        db.flush()

    old_version = crud.ensure_version(
        db,
        regulation_id=regulation_id,
        content_hash=old_hash,
        blob_path=f"local://{settings.old_doc_path}",
        preferred_version_number=1,
    )

    previous_hash = crud.get_current_regulation_hash(db, regulation_id) or old_hash

    if previous_hash == new_hash:
        stable_version = crud.get_version_by_hash(db, regulation_id, new_hash) or old_version
        crud.upsert_regulation(
            db,
            regulation_id=regulation_id,
            title=title,
            source=source,
            jurisdiction=jurisdiction,
            current_version=stable_version.version_number,
            current_hash=new_hash,
            status="No New Change",
        )
        crud.create_monitor_run(
            db,
            regulation_id=regulation_id,
            old_hash=old_hash,
            new_hash=new_hash,
            change_detected=False,
            status="completed",
        )
        db.commit()

        return MonitorRunResponse(
            regulation_id=regulation_id,
            title=title,
            source=source,
            jurisdiction=jurisdiction,
            old_text=old_text,
            new_text=new_text,
            old_hash=old_hash,
            new_hash=new_hash,
            current_hash=new_hash,
            change_detected=False,
            old_version=f"v{old_version.version_number}",
            new_version=f"v{stable_version.version_number}",
            carryover_open_actions=len(crud.get_carryover_actions(db, regulation_id, new_hash)),
            analysis=None,
        )

    new_version = crud.ensure_version(
        db,
        regulation_id=regulation_id,
        content_hash=new_hash,
        blob_path=f"local://{settings.new_doc_path}",
    )

    crud.upsert_regulation(
        db,
        regulation_id=regulation_id,
        title=title,
        source=source,
        jurisdiction=jurisdiction,
        current_version=new_version.version_number,
        current_hash=new_hash,
        status="Change Detected",
    )

    analysis = analyze_regulatory_change(old_text, new_text)
    crud.save_analysis_and_actions(
        db,
        regulation_id=regulation_id,
        content_hash=new_hash,
        analysis_result=analysis,
    )

    crud.create_monitor_run(
        db,
        regulation_id=regulation_id,
        old_hash=old_hash,
        new_hash=new_hash,
        change_detected=True,
        status="completed",
    )

    carryover_count = len(crud.get_carryover_actions(db, regulation_id, new_hash))
    db.commit()

    return MonitorRunResponse(
        regulation_id=regulation_id,
        title=title,
        source=source,
        jurisdiction=jurisdiction,
        old_text=old_text,
        new_text=new_text,
        old_hash=old_hash,
        new_hash=new_hash,
        current_hash=new_hash,
        change_detected=True,
        old_version=f"v{old_version.version_number}",
        new_version=f"v{new_version.version_number}",
        carryover_open_actions=carryover_count,
        analysis=analysis,
    )


