import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('eval/datasets/benign_and_heldout.jsonl', 'r', encoding='utf-8') as f:
    cases = [json.loads(line) for line in f if line.strip()]

for c in cases[:40]: # b01 to b40
    print(f"{c['id']}: q='{c['query']}' | b={c.get('expected_behavior')} | v={c.get('expected_value')} | s={c.get('expected_scheme_id')} | orig_s={c.get('scheme_id')} | orig_f={c.get('target_field')}")
