"""Unit tests verifying rule-based out-of-scope routing for AMC-level company inquiries.

Rule: AMC named, no scheme resolved, and no supported topic (fact field, glossary,
procedure) matched, so return an out-of-scope message with the supported scope.
Do NOT ask 'which scheme do you mean?'.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.rag.entities import resolve_entities

client = TestClient(app)


@pytest.mark.parametrize(
    "query",
    [
        "Where is the registered headquarters office of HDFC Asset Management Company located?",
        "Who is the Chief Executive Officer (CEO) of HDFC AMC?",
        "How many branch offices does HDFC Mutual Fund AMC operate across India?",
    ],
)
def test_amc_level_questions_route_to_out_of_scope_without_clarification(query: str):
    """Verifies invented AMC-level questions do not ask 'which scheme?' and return out-of-scope."""
    # 1. Entity resolution level check
    ent_res = resolve_entities(query)
    assert ent_res.is_amc_out_of_scope is True
    assert ent_res.is_ambiguous is False
    assert ent_res.scheme_id is None

    # 2. Endpoint level check
    resp = client.post("/api/v1/rag/ask", json={"query": query})
    assert resp.status_code == 200
    data = resp.json()

    assert data["resolution_type"] == "not_found"
    assert "Please specify which HDFC scheme" not in data["rendered"]
    assert "could not find official information" in data["rendered"].lower()
    assert "5 HDFC schemes" in data["rendered"] or "verified HDFC Mutual Fund records" in data["rendered"]
