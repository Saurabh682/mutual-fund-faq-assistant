import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('eval/datasets/benign_and_heldout.jsonl', 'r', encoding='utf-8') as f:
    cases = [json.loads(line) for line in f if line.strip()]

check_ids = ['h07', 'h11', 'h15', 'h29', 'b35', 'b39'] + [f'p{i:02d}' for i in range(1, 21)]
for c in cases:
    if c['id'] in check_ids:
        b = c.get('expected_behavior')
        v = c.get('expected_value')
        s = c.get('expected_scheme_id')
        print(f"{c['id']}: query='{c['query']}' :: behavior={b} :: exp_val={v} :: exp_scheme={s}")
