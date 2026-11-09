"""Comprehensive PII Security Tests.

Verifies:
1. Blocking of any PAN-shaped string (5 letters, 4 digits, 1 letter) regardless of 4th letter.
2. Blocking of any Aadhaar-like 12-digit number (formatted or plain).
3. Blocking through the real /api/v1/rag/ask endpoint (HTTP 400).
4. Verifies through the thread store (/api/v1/threads/{id}/messages) that raw PII strings
   are never stored in the database or returned in messages.
"""

from fastapi.testclient import TestClient
import pytest

from app.main import app, _IP_REQUEST_TIMESTAMPS
from app.guardrails.pii import scan_pii
from app.sessions.store import SessionStore

client = TestClient(app)


def test_pan_any_fourth_character_blocked():
    """Any 5-letter, 4-digit, 1-letter string is blocked as PAN regardless of entity status letter."""
    # 4th char 'D' is not standard entity char, but shaped as PAN
    has_pii, types, redacted = scan_pii("My PAN is ABCDE1234F, what is the exit load?")
    assert has_pii is True
    assert "PAN" in types
    assert "ABCDE1234F" not in redacted
    assert "[PAN_REDACTED]" in redacted

    # Spaced PAN
    has_pii_sp, types_sp, redacted_sp = scan_pii("PAN is A B C Z E 9 8 7 6 K")
    assert has_pii_sp is True
    assert "PAN" in types_sp


def test_aadhaar_like_numbers_blocked():
    """Any 12-digit number formatted as Aadhaar is blocked even with synthetic check digits."""
    has_pii, types, redacted = scan_pii("Aadhaar card number 1234 5678 9012")
    assert has_pii is True
    assert "AADHAAR" in types
    assert "1234 5678 9012" not in redacted
    assert "[AADHAAR_REDACTED]" in redacted

    has_pii_dash, types_dash, _ = scan_pii("Aadhaar is 9999-8888-7777")
    assert has_pii_dash is True
    assert "AADHAAR" in types_dash


def test_pii_blocked_through_real_ask_api():
    """Real /api/v1/rag/ask returns HTTP 400 PII warning and does not return the raw PII."""
    _IP_REQUEST_TIMESTAMPS.clear()
    raw_pan = "ZZZZZ9999Z"
    resp = client.post("/api/v1/rag/ask", json={"query": f"My PAN is {raw_pan}, what is TER of Mid Cap?"})
    assert resp.status_code == 400
    data = resp.json()
    assert data["error"] == "PII_DETECTED"
    assert raw_pan not in data["message"]
    assert raw_pan not in data["rendered"]
    assert "[PAN_REDACTED]" in data["redacted_text"]


def test_raw_pii_never_stored_in_thread_store():
    """Thread store redacts user messages containing PII before persistence."""
    _IP_REQUEST_TIMESTAMPS.clear()
    store = SessionStore()
    thread = store.create_thread(client_id="test_client_pii", title="PII Security Test")
    thread_id = thread.id

    raw_pan = "QWERT5432Y"
    raw_aadhaar = "8888 7777 6666"
    query = f"Here is my PAN {raw_pan} and Aadhaar {raw_aadhaar}, tell me NAV"

    resp = client.post(
        f"/api/v1/threads/{thread_id}/messages",
        json={"text": query},
        headers={"X-Client-Id": "test_client_pii"},
    )
    # The message is rejected or stored redacted
    # Inspect all stored messages in thread
    updated_thread = store.get_thread(thread_id)
    assert updated_thread is not None
    for msg in updated_thread.messages:
        assert raw_pan not in msg.text, f"Raw PAN leaked into stored message: {msg.text}"
        assert raw_aadhaar not in msg.text, f"Raw Aadhaar leaked into stored message: {msg.text}"
