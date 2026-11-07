import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("eval/datasets/benign_and_heldout.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        if not line.strip(): continue
        c = json.loads(line)
        if c.get("id", "").startswith("p"):
            print(json.dumps(c, indent=2))
