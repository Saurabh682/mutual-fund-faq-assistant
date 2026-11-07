import json
import sys
sys.path.insert(0, "backend")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

with open('eval/datasets/benign_and_heldout.jsonl', 'r', encoding='utf-8') as f:
    cases = [json.loads(line) for line in f if line.strip()]

p_cases = [c for c in cases if c['id'].startswith('p')]
for c in p_cases:
    resp = client.post("/api/v1/rag/ask", json={"query": c["query"]})
    data = resp.json()
    rtype = data.get("resolution_type")
    txt = data.get("text", "")[:80]
    print(f"{c['id']}: rtype={rtype:15s} | text={txt}")
