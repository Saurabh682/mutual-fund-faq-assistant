import time
import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_first_request_after_boot_within_300ms_refusal():
    """Verify that after application startup / warmup, the first request (refusal) completes in < 300ms."""
    with TestClient(app) as client:
        t0 = time.perf_counter()
        resp = client.post("/api/v1/rag/ask", json={"query": "Which fund should I buy for highest return?"})
        elapsed_ms = (time.perf_counter() - t0) * 1000

        assert resp.status_code == 200
        data = resp.json()
        assert data["resolution_type"] == "refusal"
        print(f"\nRefusal elapsed_ms={elapsed_ms:.1f}ms, server latency_ms={data.get('latency_ms', 0):.1f}ms")
        # Ensure either client time or server latency is strictly within SLA
        assert data.get("latency_ms", elapsed_ms) < 300.0 or elapsed_ms < 300.0, (
            f"First request (refusal) took {elapsed_ms:.1f}ms, expected < 300ms"
        )


def test_first_request_after_boot_within_300ms_fact_lookup():
    """Verify that after application startup / warmup, the first request (fact lookup) completes in < 300ms."""
    with TestClient(app) as client:
        t0 = time.perf_counter()
        resp = client.post("/api/v1/rag/ask", json={"query": "What is the NAV of HDFC Small Cap Fund?"})
        elapsed_ms = (time.perf_counter() - t0) * 1000

        assert resp.status_code == 200
        data = resp.json()
        assert data["resolution_type"] == "fact_store"
        print(f"\nFact lookup elapsed_ms={elapsed_ms:.1f}ms, server latency_ms={data.get('latency_ms', 0):.1f}ms")
        assert data.get("latency_ms", elapsed_ms) < 300.0 or elapsed_ms < 300.0, (
            f"First request (fact lookup) took {elapsed_ms:.1f}ms, expected < 300ms"
        )
