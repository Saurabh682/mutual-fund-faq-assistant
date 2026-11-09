import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch

# Add backend directory to sys.path
REPO_DIR = Path("D:/VibeCode/Applied Generative AI Bootcamp/mutual-fund-faq-assistant")
sys.path.insert(0, str(REPO_DIR / "backend"))

from fastapi.testclient import TestClient
from app.main import app, _IP_REQUEST_TIMESTAMPS
from app.rag.synthesizer import ConstrainedSynthesizer
import sqlite3

client = TestClient(app)

# Load facts.db
facts_db_path = REPO_DIR / "data" / "index" / "facts.db"
conn = sqlite3.connect(str(facts_db_path))
cursor = conn.cursor()
cursor.execute("SELECT scheme_id, field, value FROM facts")
FACTS_MAP = {f"{r[0]}::{r[1]}": r[2] for r in cursor.fetchall()}

# Load holdout_v3.jsonl
dataset_path = REPO_DIR / "eval" / "datasets" / "holdout_v3.jsonl"
with open(dataset_path, "r", encoding="utf-8") as f:
    cases = [json.loads(line) for line in f if line.strip()]

results = []
forbidden_llm_calls = []

# Mock _call_llm
original_call_llm = ConstrainedSynthesizer._call_llm
llm_call_count_current = 0

def mocked_call_llm(self, system_prompt, user_prompt, *args, **kwargs):
    global llm_call_count_current
    llm_call_count_current += 1
    # Try calling original if configured, else return a safe mock draft
    try:
        return original_call_llm(self, system_prompt, user_prompt, *args, **kwargs)
    except Exception as e:
        return f"Mock answer from LLM ({e})"

with patch.object(ConstrainedSynthesizer, "_call_llm", mocked_call_llm):
    for case in cases:
        cid = case["id"]
        query = case["query"]
        expected = case["expected_behavior"]
        expected_scheme = case.get("expected_scheme_id")
        expected_field = case.get("expected_field")

        _IP_REQUEST_TIMESTAMPS.clear()
        llm_call_count_current = 0

        t0 = time.perf_counter()
        resp = client.post("/api/v1/rag/ask", json={"query": query})
        elapsed_ms = (time.perf_counter() - t0) * 1000

        llm_called = (llm_call_count_current > 0)
        if expected in ("REFUSAL", "COMPOUND") and llm_called:
            forbidden_llm_calls.append(cid)

        status_code = resp.status_code
        data = resp.json() if status_code in (200, 400) else {}

        # Classify observed behavior
        observed = None
        rendered = data.get("rendered", "")
        text = data.get("text", "")
        resolution_type = data.get("resolution_type", "")

        if status_code == 400 and data.get("error") == "PII_DETECTED":
            observed = "PII_BLOCK"
        elif resolution_type == "compound":
            observed = "COMPOUND"
        elif resolution_type == "refusal":
            observed = "REFUSAL"
        elif resolution_type == "unsupported_plan":
            observed = "UNSUPPORTED_PLAN"
        elif resolution_type in ("external_amc", "out_of_scope"):
            observed = "OUT_OF_SCOPE"
        elif resolution_type == "not_found":
            # Check if intent was OUT_OF_SCOPE or if it's NOT_FOUND
            from app.guardrails.intent import classify_intent
            i_res = classify_intent(query)
            if i_res.intent == "OUT_OF_SCOPE":
                observed = "OUT_OF_SCOPE"
            else:
                observed = "NOT_FOUND"
        elif resolution_type in ("fact_store", "llm_synthesis", "hybrid_retrieval", "help"):
            observed = "ANSWER"
        else:
            observed = f"UNKNOWN({resolution_type})"

        # Check fact match for ANSWER and COMPOUND
        fact_match = True
        fact_detail = ""
        if expected_scheme and expected_field and observed in ("ANSWER", "COMPOUND"):
            fields = [f.strip() for f in expected_field.split(",")]
            for fld in fields:
                if fld.startswith("glossary:"):
                    continue
                db_key = f"{expected_scheme}::{fld}"
                expected_val = FACTS_MAP.get(db_key)
                if expected_val:
                    # Normalize comparison: e.g. "0.8%" in text or "0.8" in text, "100" in text
                    val_str = str(expected_val).replace("₹", "").strip()
                    # Check if val_str or expected_val is in rendered or text
                    full_resp_text = f"{rendered} {text}"
                    if val_str not in full_resp_text and expected_val not in full_resp_text:
                        # try without % or extra words
                        val_clean = val_str.replace("%", "").strip()
                        if val_clean not in full_resp_text:
                            fact_match = False
                            fact_detail = f"Expected '{expected_val}' for {db_key} not found in response"

        passed = (observed == expected) and fact_match and (not (expected in ("REFUSAL", "COMPOUND") and llm_called))

        results.append({
            "id": cid,
            "query": query,
            "expected": expected,
            "observed": observed,
            "resolution_type": resolution_type,
            "llm_called": llm_called,
            "llm_call_count": llm_call_count_current,
            "latency_ms": elapsed_ms,
            "passed": passed,
            "fact_match": fact_match,
            "fact_detail": fact_detail,
            "full_response": rendered or text or str(data),
            "status_code": status_code,
        })

print(json.dumps(results, indent=2))
