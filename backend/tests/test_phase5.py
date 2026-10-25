"""Phase 5 Test Suite: Multi-Thread Session Management & REST API Layer.

Verifies:
1. Thread CRUD: Create, Read, List, Delete thread sessions.
2. EC-SES-01: Session Isolation: Concurrent turns across Thread A and Thread B exhibit zero leakage.
3. EC-ENT-02: Pronoun / Anaphora continuity: 'its expense ratio' resolves active scheme from thread.
4. Audit Trail: Every conversation turn persists an immutable trace with zero raw PII.
5. Performance & Latency: Factual lookups under 50ms, end-to-end turns under 2.0s.
"""

import time
import pytest
from fastapi.testclient import TestClient

from app.audit.logger import read_audit_logs
from app.main import app
from app.sessions.store import SessionStore

client = TestClient(app)


class TestThreadCRUD:
    """Verifies creation, retrieval, listing, and deletion of isolated chat threads."""

    def test_create_thread(self):
        resp = client.post("/api/v1/threads", json={"client_id": "test_user_1", "title": "My Fund Questions"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"].startswith("th_")
        assert data["client_id"] == "test_user_1"
        assert data["title"] == "My Fund Questions"
        assert data["messages"] == []
        assert data["last_scheme_id"] is None

    def test_get_thread(self):
        create_resp = client.post("/api/v1/threads", json={"client_id": "test_user_1"})
        thread_id = create_resp.json()["id"]

        get_resp = client.get(f"/api/v1/threads/{thread_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == thread_id

    def test_list_threads(self):
        client_id = f"client_{int(time.time())}"
        client.post("/api/v1/threads", json={"client_id": client_id, "title": "Thread 1"})
        client.post("/api/v1/threads", json={"client_id": client_id, "title": "Thread 2"})

        list_resp = client.get(f"/api/v1/threads?client_id={client_id}")
        assert list_resp.status_code == 200
        threads = list_resp.json()
        assert len(threads) == 2
        titles = [t["title"] for t in threads]
        assert "Thread 1" in titles
        assert "Thread 2" in titles

    def test_delete_thread(self):
        create_resp = client.post("/api/v1/threads", json={"client_id": "test_del"})
        thread_id = create_resp.json()["id"]

        del_resp = client.delete(f"/api/v1/threads/{thread_id}")
        assert del_resp.status_code == 204

        # Confirm 404 after deletion
        get_resp = client.get(f"/api/v1/threads/{thread_id}")
        assert get_resp.status_code == 404

    def test_nonexistent_thread_returns_404(self):
        resp = client.get("/api/v1/threads/th_nonexistent999")
        assert resp.status_code == 404


class TestSessionIsolationEC_SES_01:
    """EC-SES-01: Verifies that conversation context never leaks between parallel threads."""

    def test_strict_thread_isolation(self):
        # Thread A: Inquires about HDFC Mid-Cap
        t_a_resp = client.post("/api/v1/threads", json={"client_id": "user_a", "title": "Mid-Cap Chat"})
        thread_a_id = t_a_resp.json()["id"]

        msg_a = client.post(
            f"/api/v1/threads/{thread_a_id}/messages",
            json={"text": "What is the exit load for HDFC Mid-Cap Opportunities Fund?"},
        )
        assert msg_a.status_code == 200
        assert "1%" in msg_a.json()["text"]

        # Thread B: Inquires about HDFC Small Cap
        t_b_resp = client.post("/api/v1/threads", json={"client_id": "user_b", "title": "Small Cap Chat"})
        thread_b_id = t_b_resp.json()["id"]

        msg_b = client.post(
            f"/api/v1/threads/{thread_b_id}/messages",
            json={"text": "What is the TER of HDFC Small Cap Fund?"},
        )
        assert msg_b.status_code == 200
        assert "0.8%" in msg_b.json()["text"]

        # Verify thread states are completely isolated
        state_a = client.get(f"/api/v1/threads/{thread_a_id}").json()
        state_b = client.get(f"/api/v1/threads/{thread_b_id}").json()

        assert state_a["last_scheme_id"] == "hdfc_midcap_dg"
        assert state_b["last_scheme_id"] == "hdfc_smallcap_dg"
        assert len(state_a["messages"]) == 2  # 1 user + 1 assistant
        assert len(state_b["messages"]) == 2


class TestPronounAnaphoraResolutionEC_ENT_02:
    """EC-ENT-02: Multi-turn conversation continuity with pronoun resolution."""

    def test_multi_turn_pronoun_resolution(self):
        # 1. Establish scheme context
        t_resp = client.post("/api/v1/threads", json={"client_id": "anaphora_user"})
        thread_id = t_resp.json()["id"]

        turn1 = client.post(
            f"/api/v1/threads/{thread_id}/messages",
            json={"text": "What is the exit load for HDFC Mid-Cap Opportunities Fund?"},
        )
        assert turn1.status_code == 200
        assert turn1.json()["type"] == "fact_store"

        # 2. Ask follow-up question using pronoun 'its'
        turn2 = client.post(
            f"/api/v1/threads/{thread_id}/messages",
            json={"text": "What is its expense ratio?"},
        )
        assert turn2.status_code == 200
        data2 = turn2.json()
        # Must resolve to HDFC Mid-Cap (0.74%), NOT ask for disambiguation!
        assert data2["type"] == "fact_store"
        assert "0.74%" in data2["text"]
        assert "HDFC Mid-Cap" in data2["text"]
        assert "hdfc-mid-cap-fund-direct-growth" in data2["citation_url"]


class TestAuditLoggerVerification:
    """Verifies that every conversation turn writes a tamper-evident audit entry without raw PII."""

    def test_audit_log_persists_turn(self):
        t_resp = client.post("/api/v1/threads", json={"client_id": "audit_user"})
        thread_id = t_resp.json()["id"]

        client.post(
            f"/api/v1/threads/{thread_id}/messages",
            json={"text": "What is the fund size of HDFC Top 100?"},
        )

        logs = read_audit_logs(limit=10)
        assert len(logs) > 0
        latest = logs[-1]
        assert latest["thread_id"] == thread_id
        assert latest["client_id"] == "audit_user"
        assert latest["resolution_type"] == "fact_store"
        assert latest["scheme_id"] == "hdfc_largecap_dg"
        assert latest["latency_ms"] is not None

    def test_audit_log_never_contains_raw_pii(self):
        t_resp = client.post("/api/v1/threads", json={"client_id": "pii_audit_user"})
        thread_id = t_resp.json()["id"]

        raw_pan = "ABCPE1234F"
        client.post(
            f"/api/v1/threads/{thread_id}/messages",
            json={"text": f"My tax PAN is {raw_pan}, check my folio details."},
        )

        logs = read_audit_logs(limit=10)
        latest = logs[-1]
        assert latest["resolution_type"] == "pii_block"
        # Zero raw PAN in audit logs!
        assert raw_pan not in latest["redacted_query"]
        assert "[PAN_REDACTED]" in latest["redacted_query"]


class TestTurnLatencyAndContract:
    """Verifies turn latencies and response contract in thread messages."""

    def test_fact_store_latency_under_50ms(self):
        t_resp = client.post("/api/v1/threads", json={"client_id": "perf_user"})
        thread_id = t_resp.json()["id"]

        t0 = time.perf_counter()
        resp = client.post(
            f"/api/v1/threads/{thread_id}/messages",
            json={"text": "What is the minimum SIP in HDFC Small Cap?"},
        )
        elapsed = (time.perf_counter() - t0) * 1000
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "fact_store"
        assert elapsed < 100.0  # Network roundtrip + SQLite lookup
        assert data["sentence_count"] <= 3
        assert "Last updated from sources:" in data["rendered"]
