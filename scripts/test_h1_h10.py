import json
import sys
sys.path.insert(0, "backend")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

with open('eval/datasets/benign_and_heldout.jsonl', 'r', encoding='utf-8') as f:
    cases = [json.loads(line) for line in f if line.strip()]

for c in cases[20:30]:
    resp = client.post("/api/v1/rag/ask", json={"query": c["query"]})
    data = resp.json()
    print(f"{c['id']}: type={data.get('resolution_type'):15s} | scheme={data.get('scheme_id')} | val={data.get('raw_value')}")
