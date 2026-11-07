import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

for fname in ["eval/datasets/benign_and_heldout.jsonl", "eval/datasets/holdout_v2.jsonl"]:
    print(f"\n=== {fname} ===")
    with open(fname, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            c = json.loads(line)
            cid = c.get("id", "")
            exp = str(c.get("expected_behavior", ""))
            scheme = str(c.get("expected_scheme_id", ""))
            val = str(c.get("expected_value", ""))
            if cid.startswith("p") or exp in ["not_found", "refuse", "answer"]:
                print(f"{cid:5s} | exp={exp:10s} | scheme={scheme:22s} | val={val[:20]:20s} | query={c.get('query')[:55]}")
