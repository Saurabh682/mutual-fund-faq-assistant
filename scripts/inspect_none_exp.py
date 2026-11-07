import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("eval/datasets/benign_and_heldout.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        if not line.strip(): continue
        c = json.loads(line)
        if c.get("expected_behavior") is None:
            print(f"{c['id']:5s} | cat={c.get('category'):22s} | query={c['query'][:50]}")
