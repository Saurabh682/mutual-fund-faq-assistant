import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("eval/reports/benign_heldout_eval_results.json", "r", encoding="utf-8") as f:
    report = json.load(f)

for r in report["results"]:
    if r["id"] in ["b35", "b39"]:
        print(f"=== {r['id']} ===")
        print("Query:", r["query"])
        print("Type:", r["response_type"])
        print("Text:", r["response_text"])
        print("Rendered:", r["rendered"])
        print("Expected:", r["expected_value"])
        print("Reasons:", r["failure_reasons"])
