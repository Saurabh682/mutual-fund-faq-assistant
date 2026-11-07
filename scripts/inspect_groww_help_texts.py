import os
import json
from bs4 import BeautifulSoup
import re

snapshots_dir = os.path.join("data", "snapshots")
manifest_path = os.path.join(snapshots_dir, "snapshots_manifest.json")

with open(manifest_path, "r", encoding="utf-8") as f:
    manifest = json.load(f)

for key, item in manifest["snapshots"].items():
    if not key.startswith("procedure_"):
        continue
    file_path = os.path.join(snapshots_dir, os.path.basename(item["snapshot_file"]))
    if not os.path.exists(file_path):
        continue
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")
    for s in soup(["script", "style"]):
        s.extract()
    text = " ".join(soup.get_text().split())
    # search for keywords related to the procedure
    print(f"\n=== {key} ({item['url']}) ===")
    print(f"Text length: {len(text)}")
    # Print the first 250 characters of actual body text after header
    print(f"Sample: {text[:200]}")
