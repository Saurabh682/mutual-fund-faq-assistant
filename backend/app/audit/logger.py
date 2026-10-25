"""Audit Logger for Mutual Fund FAQ Assistant.

Persists a complete, tamper-evident audit trace for every conversation turn
to `data/audit.jsonl`. Guarantees that ZERO raw PII is ever recorded.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.config import settings


def get_audit_log_path() -> str:
    """Returns absolute path to audit.jsonl."""
    return os.path.join(settings.DATA_DIR, "audit.jsonl")


def record_audit_entry(
    thread_id: str,
    client_id: str,
    redacted_query: str,
    resolution_type: str,
    intent: Optional[str] = None,
    scheme_id: Optional[str] = None,
    field: Optional[str] = None,
    retrieved_chunk_ids: Optional[List[str]] = None,
    sentence_count: Optional[int] = None,
    citation_url: Optional[str] = None,
    latency_ms: Optional[float] = None,
    repaired: bool = False,
    repair_count: int = 0,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Appends an immutable audit event to audit.jsonl."""
    log_path = get_audit_log_path()
    os.makedirs(os.path.dirname(os.path.abspath(log_path)), exist_ok=True)

    entry = {
        "turn_id": f"aud_{uuid.uuid4().hex[:12]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "thread_id": thread_id,
        "client_id": client_id,
        "redacted_query": redacted_query,
        "resolution_type": resolution_type,
        "intent": intent,
        "scheme_id": scheme_id,
        "field": field,
        "retrieved_chunk_ids": retrieved_chunk_ids or [],
        "sentence_count": sentence_count,
        "citation_url": citation_url,
        "latency_ms": round(latency_ms, 2) if latency_ms is not None else None,
        "repaired": repaired,
        "repair_count": repair_count,
        "metadata": metadata or {},
    }

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return entry


def read_audit_logs(limit: int = 100) -> List[Dict[str, Any]]:
    """Reads recent audit logs."""
    log_path = get_audit_log_path()
    if not os.path.exists(log_path):
        return []

    entries = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    return entries[-limit:]
