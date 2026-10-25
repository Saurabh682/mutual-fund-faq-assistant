"""Thread-Safe Session Store backed by SQLite with per-thread concurrency locks."""

from __future__ import annotations

import asyncio
import os
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.core.config import settings
from app.schemas.chat import MessageDTO, ThreadDTO, ThreadSummaryDTO

# In-memory dictionary of asyncio Locks to serialize turn execution per thread (EC-SES-01)
_THREAD_LOCKS: Dict[str, asyncio.Lock] = {}
_GLOBAL_LOCK = asyncio.Lock()


def get_sessions_db_path() -> str:
    """Returns absolute path to sessions.db."""
    return os.path.join(settings.DATA_DIR, "sessions.db")


def init_session_db(db_path: Optional[str] = None) -> None:
    """Initializes the SQLite sessions schema."""
    path = db_path or get_sessions_db_path()
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    with sqlite3.connect(path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS threads (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                title TEXT NOT NULL,
                last_scheme_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                thread_id TEXT NOT NULL,
                role TEXT NOT NULL,
                type TEXT NOT NULL,
                text TEXT NOT NULL,
                sentence_count INTEGER,
                citation_url TEXT,
                last_updated TEXT,
                rendered TEXT,
                timestamp TEXT NOT NULL,
                latency_ms REAL,
                FOREIGN KEY (thread_id) REFERENCES threads(id) ON DELETE CASCADE
            );
            """
        )

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_threads_client ON threads(client_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_thread ON messages(thread_id);")
        conn.commit()


async def get_thread_lock(thread_id: str) -> asyncio.Lock:
    """Retrieves or creates a dedicated asyncio.Lock for the specified thread."""
    async with _GLOBAL_LOCK:
        if thread_id not in _THREAD_LOCKS:
            _THREAD_LOCKS[thread_id] = asyncio.Lock()
        return _THREAD_LOCKS[thread_id]


class SessionStore:
    """CRUD interface for threads and messages."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_sessions_db_path()
        init_session_db(self.db_path)

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def create_thread(
        self, client_id: str = "default_client", title: str = "New Conversation"
    ) -> ThreadDTO:
        thread_id = f"th_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO threads (id, client_id, title, last_scheme_id, created_at, updated_at)
                VALUES (?, ?, ?, NULL, ?, ?);
                """,
                (thread_id, client_id, title, now, now),
            )
            conn.commit()

        return ThreadDTO(
            id=thread_id,
            client_id=client_id,
            title=title,
            last_scheme_id=None,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
            messages=[],
        )

    def get_thread(self, thread_id: str) -> Optional[ThreadDTO]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM threads WHERE id = ?;", (thread_id,))
            t_row = cursor.fetchone()
            if not t_row:
                return None

            cursor.execute(
                "SELECT * FROM messages WHERE thread_id = ? ORDER BY timestamp ASC;",
                (thread_id,),
            )
            m_rows = cursor.fetchall()

        messages = [
            MessageDTO(
                id=m["id"],
                role=m["role"],
                type=m["type"],
                text=m["text"],
                sentence_count=m["sentence_count"],
                citation_url=m["citation_url"],
                last_updated=m["last_updated"],
                rendered=m["rendered"],
                timestamp=datetime.fromisoformat(m["timestamp"]),
                latency_ms=m["latency_ms"],
            )
            for m in m_rows
        ]

        return ThreadDTO(
            id=t_row["id"],
            client_id=t_row["client_id"],
            title=t_row["title"],
            last_scheme_id=t_row["last_scheme_id"],
            created_at=datetime.fromisoformat(t_row["created_at"]),
            updated_at=datetime.fromisoformat(t_row["updated_at"]),
            messages=messages,
        )

    def list_threads(self, client_id: str = "default_client") -> List[ThreadSummaryDTO]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT t.id, t.client_id, t.title, t.last_scheme_id, t.created_at, t.updated_at,
                       COUNT(m.id) as message_count
                FROM threads t
                LEFT JOIN messages m ON t.id = m.thread_id
                WHERE t.client_id = ?
                GROUP BY t.id
                ORDER BY t.updated_at DESC;
                """,
                (client_id,),
            )
            rows = cursor.fetchall()

        return [
            ThreadSummaryDTO(
                id=r["id"],
                client_id=r["client_id"],
                title=r["title"],
                last_scheme_id=r["last_scheme_id"],
                created_at=datetime.fromisoformat(r["created_at"]),
                updated_at=datetime.fromisoformat(r["updated_at"]),
                message_count=r["message_count"],
            )
            for r in rows
        ]

    def delete_thread(self, thread_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM threads WHERE id = ?;", (thread_id,))
            conn.commit()
            return cursor.rowcount > 0

    def update_thread_scheme(self, thread_id: str, scheme_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE threads SET last_scheme_id = ?, updated_at = ? WHERE id = ?;",
                (scheme_id, now, thread_id),
            )
            conn.commit()

    def update_thread_title(self, thread_id: str, title: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE threads SET title = ?, updated_at = ? WHERE id = ?;",
                (title, now, thread_id),
            )
            conn.commit()

    def append_message(self, thread_id: str, message: MessageDTO) -> MessageDTO:
        now = message.timestamp.isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO messages (
                    id, thread_id, role, type, text, sentence_count, citation_url,
                    last_updated, rendered, timestamp, latency_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    message.id,
                    thread_id,
                    message.role,
                    message.type,
                    message.text,
                    message.sentence_count,
                    message.citation_url,
                    message.last_updated,
                    message.rendered,
                    now,
                    message.latency_ms,
                ),
            )
            cursor.execute(
                "UPDATE threads SET updated_at = ? WHERE id = ?;", (now, thread_id)
            )
            conn.commit()

        return message

    def prune_expired_sessions(self, days: int = settings.SESSION_TTL_DAYS) -> int:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM threads WHERE updated_at < ?;", (cutoff,))
            conn.commit()
            return cursor.rowcount
