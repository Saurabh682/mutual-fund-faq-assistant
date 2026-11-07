import os
import json
from bs4 import BeautifulSoup

snapshots_dir = os.path.join("data", "snapshots")
manifest_path = os.path.join(snapshots_dir, "snapshots_manifest.json")

with open(manifest_path, "r", encoding="utf-8") as f:
    manifest = json.load(f)

for key, item in manifest["snapshots"].items():
    file_path = os.path.join(snapshots_dir, os.path.basename(item["snapshot_file"]))
    if not os.path.exists(file_path):
        continue
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")
    # remove scripts and styles
    for s in soup(["script", "style"]):
        s.extract()
    text = " ".join(soup.get_text().split())
    supp = item.get("supporting_sentence", "")
    is_sub = supp in text
    print(f"{key:35s}: text_len={len(text):6d} | supp_in_text={is_sub}")
    if not is_sub:
        print(f"   SUPP: {supp[:80]}...")
