import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("eval/reports/benign_heldout_eval_results.json", "r", encoding="utf-8") as f:
    report = json.load(f)

for r in report["results"]:
    if not r["passed"]:
        print(f"FAILED {r['id']:5s} | type={r['response_type']:15s} | exp_beh={r.get('expected_behavior')} | reasons={r['failure_reasons']} | query={r['query'][:55]}")
