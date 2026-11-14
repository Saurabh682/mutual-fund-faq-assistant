"""Plan 8.2 hallucination target: out-of-corpus questions must never get an invented or borrowed number.

Questions about other AMCs, metrics we do not store, dated NAVs or unlisted HDFC funds may be declined or
answered with a definition, but never with a rupee or percent value, and never with another scheme's facts.
"""

import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app, _IP_REQUEST_TIMESTAMPS

client = TestClient(app)
CASES = [json.loads(l) for l in (Path(__file__).parents[2] / "eval/datasets/out_of_corpus_eval.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
VALUE = re.compile(r"₹\s?\d|\d\s?%")


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_no_value_for_out_of_corpus_query(case):
    _IP_REQUEST_TIMESTAMPS.clear()
    data = client.post("/api/v1/rag/ask", json={"query": case["query"]}).json()
    if data["resolution_type"] in ("fact_store", "llm_synthesis", "compound"):
        assert not VALUE.search(data["text"]), data["text"]


def test_unlisted_hdfc_fund_is_not_mapped_to_a_listed_one():
    from app.rag.entities import resolve_entities
    assert resolve_entities("What is the expense ratio of HDFC Flexi Cap Fund?").scheme_id is None
