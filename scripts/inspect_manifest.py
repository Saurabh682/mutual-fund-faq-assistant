import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/snapshots/snapshots_manifest.json', 'r', encoding='utf-8') as f:
    manifest = json.load(f)

print("MANIFEST SNAPSHOTS:")
for eid, item in manifest.get('snapshots', {}).items():
    print(f"{eid:35s}: status={item.get('status')} | url={item.get('url')[:50]}")
