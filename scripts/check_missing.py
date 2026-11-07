import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('eval/datasets/benign_and_heldout.jsonl', 'r', encoding='utf-8') as f:
    cases = [json.loads(line) for line in f if line.strip()]

missing_behavior = [c['id'] for c in cases if not c.get('expected_behavior')]
print(f"Missing expected_behavior count: {len(missing_behavior)}")
print("Missing IDs:", missing_behavior)
