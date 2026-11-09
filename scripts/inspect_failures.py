import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

def inspect(path):
    print('=== File:', path)
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    print('Summary:', json.dumps(data.get('summary', {}), indent=2))
    failures = [r for r in data.get('results', []) if not r.get('passed', False)]
    print(f'Total failures: {len(failures)} / {len(data.get("results", []))}')
    for r in failures:
        print(f"ID: {r.get('id')} | Category: {r.get('category')} | Passed: {r.get('passed')}")
        print(f"Query: {r.get('query')}")
        print(f"Expected: {r.get('expected_behavior')} | Observed: {r.get('observed_behavior')} (response_type={r.get('response_type')})")
        print(f"Failure reasons: {r.get('failure_reasons')}")
        print(f"Rendered:\n{r.get('rendered')}")
        print('-'*50)

if __name__ == '__main__':
    inspect('eval/reports/holdout_v2_dev_results.json')
    inspect('eval/reports/rewording_v1_results.json')
