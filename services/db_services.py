import sqlite3
import json
import hashlib
from pathlib import Path
from datetime import datetime

DB_PATH = Path("data/lexaflow.db")


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def _column_exists(cur, table, column):
    cur.execute(f"PRAGMA table_info({table})")
    return column in [row[1] for row in cur.fetchall()]


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS source_updates (
        update_id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        jurisdiction TEXT,
        title TEXT,
        link TEXT,
        published TEXT,
        content_hash TEXT,
        is_new_update INTEGER,
        is_fallback INTEGER,
        fetched_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS regulations (
        regulation_id TEXT PRIMARY KEY,
        title TEXT,
        source TEXT,
        jurisdiction TEXT,
        current_version INTEGER,
        current_hash TEXT,
        status TEXT,
        last_updated_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS versions (
        version_id INTEGER PRIMARY KEY AUTOINCREMENT,
        regulation_id TEXT,
        version_number INTEGER,
        blob_path TEXT,
        content_hash TEXT,
        detected_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS analysis (
        analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
        regulation_id TEXT,
        content_hash TEXT,
        what_changed TEXT,
        business_impact TEXT,
        risk_level TEXT,
        affected_teams TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS actions (
        action_id INTEGER PRIMARY KEY AUTOINCREMENT,
        regulation_id TEXT,
        content_hash TEXT,
        action_signature TEXT,
        action_text TEXT,
        owner TEXT,
        priority TEXT,
        status TEXT,
        due_date TEXT,
        created_at TEXT
    )
    """)

    # Safe migrations for old DB
    if not _column_exists(cur, "analysis", "content_hash"):
        cur.execute("ALTER TABLE analysis ADD COLUMN content_hash TEXT")

    if not _column_exists(cur, "actions", "content_hash"):
        cur.execute("ALTER TABLE actions ADD COLUMN content_hash TEXT")

    if not _column_exists(cur, "actions", "action_signature"):
        cur.execute("ALTER TABLE actions ADD COLUMN action_signature TEXT")

    conn.commit()
    conn.close()


def save_source_update(update):
    conn = get_connection()
    cur = conn.cursor()

    raw = f"{update['source']}|{update['title']}|{update['link']}|{update['published']}"
    content_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    cur.execute("""
        SELECT update_id
        FROM source_updates
        WHERE source = ?
        AND content_hash = ?
        LIMIT 1
    """, (update["source"], content_hash))

    already_seen = cur.fetchone()
    is_new_update = 0 if already_seen else 1

    cur.execute("""
        INSERT INTO source_updates (
            source, jurisdiction, title, link, published,
            content_hash, is_new_update, is_fallback, fetched_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        update["source"],
        update["jurisdiction"],
        update["title"],
        update["link"],
        update["published"],
        content_hash,
        is_new_update,
        1 if update.get("is_fallback") else 0,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    update["is_new_update"] = is_new_update
    update["content_hash"] = content_hash
    return update


def get_current_regulation_hash(regulation_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT current_hash
        FROM regulations
        WHERE regulation_id = ?
    """, (regulation_id,))

    row = cur.fetchone()
    conn.close()

    return row[0] if row else None


def upsert_regulation(regulation_id, title, source, jurisdiction, current_version, current_hash, status):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO regulations (
            regulation_id, title, source, jurisdiction,
            current_version, current_hash, status, last_updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(regulation_id) DO UPDATE SET
            current_version = excluded.current_version,
            current_hash = excluded.current_hash,
            status = excluded.status,
            last_updated_at = excluded.last_updated_at
    """, (
        regulation_id,
        title,
        source,
        jurisdiction,
        current_version,
        current_hash,
        status,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def save_version(regulation_id, version_number, content_hash, blob_path):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT version_id
        FROM versions
        WHERE regulation_id = ?
        AND content_hash = ?
        LIMIT 1
    """, (regulation_id, content_hash))

    exists = cur.fetchone()

    if not exists:
        cur.execute("""
            INSERT INTO versions (
                regulation_id, version_number, blob_path, content_hash, detected_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            regulation_id,
            version_number,
            blob_path,
            content_hash,
            datetime.now().isoformat()
        ))

    conn.commit()
    conn.close()


def get_pending_actions_for_regulation(regulation_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT action_id, action_text, owner, priority, status, due_date, created_at
        FROM actions
        WHERE regulation_id = ?
        AND status != 'Completed'
        ORDER BY action_id DESC
    """, (regulation_id,))

    rows = cur.fetchall()
    conn.close()
    return rows


def save_analysis_and_actions(regulation_id, ai_result, content_hash):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT analysis_id
        FROM analysis
        WHERE regulation_id = ?
        AND content_hash = ?
        LIMIT 1
    """, (regulation_id, content_hash))

    existing_analysis = cur.fetchone()

    if existing_analysis:
        conn.close()
        return {
            "analysis_id": existing_analysis[0],
            "inserted_actions": 0,
            "skipped_duplicates": 0,
            "already_analyzed": True
        }

    what_changed = ai_result.get("what_changed", [])
    business_impact = ai_result.get("business_impact", "")
    risk_level = ai_result.get("risk_level", "")
    affected_teams = ai_result.get("affected_teams", [])
    actions = ai_result.get("recommended_actions", [])

    cur.execute("""
        INSERT INTO analysis (
            regulation_id, content_hash, what_changed, business_impact,
            risk_level, affected_teams, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        regulation_id,
        content_hash,
        json.dumps(what_changed),
        str(business_impact),
        str(risk_level),
        json.dumps(affected_teams),
        datetime.now().isoformat()
    ))

    analysis_id = cur.lastrowid
    inserted_count = 0
    skipped_count = 0

    for action in actions:
        action_text = str(action.get("action", ""))
        owner = str(action.get("owner", "Unassigned"))
        priority = str(action.get("priority", "Medium"))
        due_days = action.get("due_days", 7)

        normalized = action_text.strip().lower()
        action_signature = hashlib.sha256(
            f"{regulation_id}|{content_hash}|{normalized}".encode("utf-8")
        ).hexdigest()

        cur.execute("""
            SELECT action_id
            FROM actions
            WHERE action_signature = ?
            LIMIT 1
        """, (action_signature,))

        if cur.fetchone():
            skipped_count += 1
            continue

        cur.execute("""
            INSERT INTO actions (
                regulation_id, content_hash, action_signature, action_text,
                owner, priority, status, due_date, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            regulation_id,
            content_hash,
            action_signature,
            action_text,
            owner,
            priority,
            "Not Started",
            f"{due_days} days",
            datetime.now().isoformat()
        ))

        inserted_count += 1

    conn.commit()
    conn.close()

    return {
        "analysis_id": analysis_id,
        "inserted_actions": inserted_count,
        "skipped_duplicates": skipped_count,
        "already_analyzed": False
    }


def get_actions():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            a.action_id,
            a.regulation_id,
            a.action_text,
            a.owner,
            a.priority,
            a.status,
            a.due_date,
            a.created_at,
            r.source,
            r.last_updated_at
        FROM actions a
        LEFT JOIN regulations r
        ON a.regulation_id = r.regulation_id
        ORDER BY a.action_id DESC
    """)

    rows = cur.fetchall()
    conn.close()
    return rows


def update_action_status(action_id, status):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE actions
        SET status = ?
        WHERE action_id = ?
    """, (status, action_id))

    conn.commit()
    conn.close()


def get_kpis():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM regulations")
    regulations_monitored = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM source_updates WHERE is_new_update = 1")
    source_updates = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM analysis WHERE LOWER(risk_level) = 'high'")
    high_risk_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM actions WHERE status != 'Completed'")
    pending_actions = cur.fetchone()[0]

    conn.close()

    return {
        "regulations_monitored": regulations_monitored,
        "source_updates": source_updates,
        "high_risk_count": high_risk_count,
        "pending_actions": pending_actions
    }

def get_carryover_actions(regulation_id, current_hash):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT action_id, action_text, owner, priority, status, due_date, created_at
        FROM actions
        WHERE regulation_id = ?
        AND content_hash != ?
        AND status != 'Completed'
        ORDER BY action_id DESC
    """, (regulation_id, current_hash))

    rows = cur.fetchall()
    conn.close()
    return rows

def get_versions_for_regulation(regulation_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT version_number, content_hash, detected_at
        FROM versions
        WHERE regulation_id = ?
        ORDER BY version_number ASC
    """, (regulation_id,))

    rows = cur.fetchall()
    conn.close()
    return rows

def reset_demo_database():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM actions")
    cur.execute("DELETE FROM analysis")
    cur.execute("DELETE FROM versions")
    cur.execute("DELETE FROM regulations")
    cur.execute("DELETE FROM source_updates")

    conn.commit()
    conn.close()
    
def update_action_due_date(action_id, due_date):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE actions
        SET due_date = ?
        WHERE action_id = ?
    """, (due_date, action_id))

    conn.commit()
    conn.close()