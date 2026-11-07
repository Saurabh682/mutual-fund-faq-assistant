import hashlib
import json
import os
import re

snapshots_dir = os.path.join("data", "snapshots")
manifest_path = os.path.join(snapshots_dir, "snapshots_manifest.json")

with open(manifest_path, "r", encoding="utf-8") as f:
    manifest = json.load(f)

print(f"Total manifest entries: {len(manifest['snapshots'])}\n")

hash_map = {}
for key, item in manifest["snapshots"].items():
    file_path = os.path.join(snapshots_dir, os.path.basename(item["snapshot_file"]))
    if not os.path.exists(file_path):
        print(f"MISSING FILE: {file_path}")
        continue
    with open(file_path, "rb") as sf:
        content = sf.read()
    h = hashlib.sha256(content).hexdigest()
    if h in hash_map:
        print(f"DUPLICATE HASH: {key} ({item['url']}) shares hash {h[:12]} with {hash_map[h]}")
    else:
        hash_map[h] = key

    # Check for 404, not found, enable JavaScript
    text_sample = content.decode("utf-8", errors="replace")
    has_404 = bool(re.search(r"\b404\b|not found", text_sample, re.I))
    has_enable_js = "enable javascript" in text_sample.lower()
    print(f"{key:35s}: {len(content):7d} bytes | hash {h[:12]} | 404={has_404} | enable_js={has_enable_js}")
