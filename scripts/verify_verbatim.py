import json
import os
import re

snapshots_dir = os.path.join("data", "snapshots")
manifest_path = os.path.join(snapshots_dir, "snapshots_manifest.json")

with open(manifest_path, "r", encoding="utf-8") as f:
    manifest = json.load(f)

def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()

for key, item in manifest["snapshots"].items():
    file_path = os.path.join(snapshots_dir, os.path.basename(item["snapshot_file"]))
    with open(file_path, "r", encoding="utf-8", errors="replace") as sf:
        page_raw = sf.read()

    # Plain text conversion
    page_text = re.sub(r"<[^>]+>", " ", page_raw)
    page_norm = norm(page_text)
    sent = item.get("supporting_sentence", "")
    sent_norm = norm(sent)

    is_sub = sent_norm in page_norm or sent_norm in norm(page_raw)
    status = "VERBATIM MATCH" if is_sub else "NOT A SUBSTRING"
    print(f"{key:35s}: {status}")
    if not is_sub:
        print(f"   Quote: {sent[:80]}...")
