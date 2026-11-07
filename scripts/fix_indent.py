with open("backend/app/rag/procedures.py", "r", encoding="utf-8") as f:
    text = f.read()

bad_block = """# Strict build-time validation of procedures
for item in PROCEDURE_ITEMS:
        if item.get("supported") is False or item.get("status") == "unsupported":
            continue
    if not item.get("source_url") or not str(item.get("source_url")).startswith("https://"):
        raise ValueError(f"Procedure item '{item.get('id')}' missing mandatory 'source_url'")
    if not item.get("verified_on") or not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", str(item.get("verified_on"))):
        raise ValueError(f"Procedure item '{item.get('id')}' missing mandatory 'verified_on'")"""

good_block = """# Strict build-time validation of procedures
for item in PROCEDURE_ITEMS:
    if item.get("supported") is False or item.get("status") == "unsupported":
        continue
    if not item.get("source_url") or not str(item.get("source_url")).startswith("https://"):
        raise ValueError(f"Procedure item '{item.get('id')}' missing mandatory 'source_url'")
    if not item.get("verified_on") or not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", str(item.get("verified_on"))):
        raise ValueError(f"Procedure item '{item.get('id')}' missing mandatory 'verified_on'")"""

text = text.replace(bad_block, good_block)
with open("backend/app/rag/procedures.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Fixed indentation")
