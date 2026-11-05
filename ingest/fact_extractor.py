import sqlite3
import os

def init_fact_store(db_path: str):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS facts (
        fact_id TEXT PRIMARY KEY,
        scheme_id TEXT NOT NULL,
        field TEXT NOT NULL,
        value TEXT NOT NULL,
        unit TEXT,
        citation_url TEXT NOT NULL,
        doc_date TEXT NOT NULL,
        source_url TEXT,
        as_of TEXT,
        human_verified BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scheme_field ON facts(scheme_id, field)")
    # Migration if columns missing
    cols = [c[1] for c in cursor.execute("PRAGMA table_info(facts)").fetchall()]
    if "as_of" not in cols:
        cursor.execute("ALTER TABLE facts ADD COLUMN as_of TEXT")
    if "source_url" not in cols:
        cursor.execute("ALTER TABLE facts ADD COLUMN source_url TEXT")
    cursor.execute("UPDATE facts SET as_of = doc_date WHERE as_of IS NULL")
    cursor.execute("UPDATE facts SET source_url = citation_url WHERE source_url IS NULL")
    conn.commit()
    conn.close()

def store_scheme_facts(db_path: str, scheme_id: str, canonical_facts: dict, citation_url: str, doc_date: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for field, val in canonical_facts.items():
        if val is None or val == "":
            continue
        fact_id = f"{scheme_id}::{field}"
        cursor.execute("""
        INSERT OR REPLACE INTO facts (fact_id, scheme_id, field, value, unit, citation_url, doc_date, source_url, as_of, human_verified)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (fact_id, scheme_id, field, str(val), "", citation_url, str(doc_date), citation_url, str(doc_date), 1))

    conn.commit()
    conn.close()

def get_fact(db_path: str, scheme_id: str, field: str) -> dict | None:
    if not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM facts WHERE scheme_id = ? AND field = ?", (scheme_id, field))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None
