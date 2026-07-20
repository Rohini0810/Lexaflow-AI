from services.document_service import extract_text_from_pdf
from services.db_services import (
    get_current_regulation_hash,
    upsert_regulation,
    save_version
)
from utils.hashing import generate_hash


def process_pdf_versions():
    regulation_id = "RBI_KYC_001"

    old_pdf = "data/sample_docs/rbi_v1.pdf"
    new_pdf = "data/sample_docs/rbi_v2.pdf"

    old_text = extract_text_from_pdf(old_pdf)
    new_text = extract_text_from_pdf(new_pdf)

    old_hash = generate_hash(old_text)
    new_hash = generate_hash(new_text)

    previous_hash = get_current_regulation_hash(regulation_id)

    if previous_hash == new_hash:
        return {
            "regulation_id": regulation_id,
            "title": "RBI KYC Master Direction Update",
            "source": "RBI",
            "jurisdiction": "India",
            "old_text": old_text,
            "new_text": new_text,
            "old_hash": old_hash,
            "new_hash": new_hash,
            "current_hash": new_hash,
            "change_detected": False,
            "old_version": "v1",
            "new_version": "v2"
        }

    save_version(regulation_id, 1, old_hash, "local://data/sample_docs/rbi_v1.pdf")
    save_version(regulation_id, 2, new_hash, "local://data/sample_docs/rbi_v2.pdf")

    upsert_regulation(
        regulation_id=regulation_id,
        title="RBI KYC Master Direction Update",
        source="RBI",
        jurisdiction="India",
        current_version=2,
        current_hash=new_hash,
        status="Change Detected"
    )

    return {
        "regulation_id": regulation_id,
        "title": "RBI KYC Master Direction Update",
        "source": "RBI",
        "jurisdiction": "India",
        "old_text": old_text,
        "new_text": new_text,
        "old_hash": old_hash,
        "new_hash": new_hash,
        "current_hash": new_hash,
        "change_detected": True,
        "old_version": "v1",
        "new_version": "v2"
    }