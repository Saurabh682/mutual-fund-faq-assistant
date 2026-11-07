import json

with open("eval/datasets/benign_and_heldout.jsonl", "r", encoding="utf-8") as f:
    lines = f.readlines()

for line in lines:
    if not line.strip(): continue
    c = json.loads(line)
    cid = c.get("id")
    if cid in ["h11", "h15", "h29", "b35", "b39", "p01", "p02", "p04", "p09"]:
        print(f"{cid:5s} | exp_beh={c.get('expected_behavior')} | exp_val={c.get('expected_value')} | q={c['query'][:40]}")
