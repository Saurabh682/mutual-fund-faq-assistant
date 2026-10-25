"""Structured Fact Path for Mutual Fund FAQ Assistant.

Provides O(1) deterministic retrieval directly from the SQLite fact store (facts.db),
completely bypassing the LLM for canonical metrics:
- TER (Expense Ratio)
- Exit Load
- Minimum SIP
- Minimum Lumpsum
- Minimum Additional
- Lock-in Period
- Riskometer
- Benchmark Index
- NAV
- AUM
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, Optional

from app.core.config import settings
from app.guardrails.refusal import get_default_corpus_date
from app.rag.entities import SCHEME_REGISTRY, resolve_entities

FACT_TEMPLATES: Dict[str, str] = {
    "ter_direct": "The Total Expense Ratio (TER) of {scheme_name} (Direct Plan) is {value}.",
    "exit_load": "The exit load for {scheme_name} is {value}",
    "min_sip": "The minimum SIP investment for {scheme_name} is {value} per installment.",
    "min_lumpsum": "The minimum initial lumpsum investment for {scheme_name} is {value}.",
    "min_additional": "The minimum additional purchase amount for {scheme_name} is {value}.",
    "lock_in": "The lock-in period for {scheme_name} is {value}.",
    "riskometer": "The riskometer classification for {scheme_name} is {value}.",
    "benchmark": "The benchmark index for {scheme_name} is {value}.",
    "nav": "The Net Asset Value (NAV) of {scheme_name} is {value}.",
    "aum": "The Assets Under Management (AUM) of {scheme_name} is {value}.",
}


def normalize_iso_date(date_str: str) -> str:
    """Normalizes various date formats to ISO YYYY-MM-DD."""
    if not date_str:
        return get_default_corpus_date()
    try:
        # Matches 23-Oct-2026
        return datetime.strptime(date_str.strip(), "%d-%b-%Y").strftime("%Y-%m-%d")
    except Exception:
        pass
    try:
        # Matches YYYY-MM-DD
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").strftime("%Y-%m-%d")
    except Exception:
        pass
    return get_default_corpus_date()


def get_fact_from_db(
    scheme_id: str, field: str, db_path: str = settings.FACTS_DB_PATH
) -> Optional[Dict[str, Any]]:
    """Fetches a canonical verified fact row from SQLite facts.db."""
    if not os.path.exists(db_path):
        return None

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM facts WHERE scheme_id = ? AND field = ? LIMIT 1",
            (scheme_id, field),
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
    except Exception:
        return None
    return None


def format_fact_response(fact: Dict[str, Any]) -> Dict[str, Any]:
    """Formats a verified fact row into a response complying with the Response Contract."""
    scheme_id = fact["scheme_id"]
    field = fact["field"]
    raw_val = fact["value"]
    scheme_meta = SCHEME_REGISTRY.get(scheme_id, {})
    scheme_name = scheme_meta.get("name", scheme_id)
    citation_url = fact.get("citation_url") or scheme_meta.get("url", "")

    template = FACT_TEMPLATES.get(field, "{scheme_name} {field} is {value}.")
    body = template.format(scheme_name=scheme_name, value=raw_val, field=field)

    # Ensure clean single-sentence punctuation
    body = body.strip()
    if not body.endswith("."):
        body += "."

    doc_date = normalize_iso_date(fact.get("doc_date", ""))
    rendered = f"{body}\n\nSource: {citation_url}\nLast updated from sources: {doc_date}"

    return {
        "text": body,
        "citation_url": citation_url,
        "last_updated": doc_date,
        "rendered": rendered,
        "source": "fact_store",
        "scheme_id": scheme_id,
        "field": field,
        "raw_value": raw_val,
    }


def lookup_fact(
    query: str, session_scheme_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """End-to-end fact path lookup.

    Resolves scheme and field entities from query, queries facts.db, and formats
    a 100% deterministic response if hit. Returns None if query requires RAG retrieval.
    """
    entity_res = resolve_entities(query, session_scheme_id=session_scheme_id)

    if entity_res.is_ambiguous or not entity_res.scheme_id or not entity_res.field:
        return None

    fact_row = get_fact_from_db(entity_res.scheme_id, entity_res.field)
    if fact_row:
        return format_fact_response(fact_row)

    return None
