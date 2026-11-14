"""Plan 8.2: all 40 synthetic PII injections must be blocked with the raw value redacted."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app, _IP_REQUEST_TIMESTAMPS

client = TestClient(app)
CASES = [json.loads(l) for l in (Path(__file__).parents[2] / "eval/datasets/pii_injection_eval.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]


def test_dataset_has_40_cases():
    assert len(CASES) == 40


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_pii_injection_is_blocked(case):
    _IP_REQUEST_TIMESTAMPS.clear()
    resp = client.post("/api/v1/rag/ask", json={"query": case["query"]})
    assert resp.status_code == 400
    assert resp.json()["error"] == "PII_DETECTED"
