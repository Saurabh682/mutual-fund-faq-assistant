with open("backend/app/rag/facts.py", "r", encoding="utf-8") as f:
    text = f.read()

# 1. FIELD_LABELS
text = text.replace(
    '"fund_manager": "Fund Manager",',
    '"fund_manager": "Primary Lead Fund Manager",\n    "nav_source": "Official NAV Verification Source",'
)

# 2. get_fact_from_db
old_branch = 'if field == "factsheet":'
new_branch = (
    'if field == "nav_source":\n'
    '                return {\n'
    '                    "scheme_id": scheme_id,\n'
    '                    "field": field,\n'
    '                    "value": "AMFI official portal (amfiindia.com) and hdfcfund.com",\n'
    '                    "value_str": "AMFI official portal (amfiindia.com) and hdfcfund.com",\n'
    '                    "value_num": None,\n'
    '                    "as_of": "2026-11-05",\n'
    '                    "doc_date": "2026-11-05",\n'
    '                }\n'
    '            elif field == "factsheet":'
)
text = text.replace(old_branch, new_branch)

# 3. format_fact_response narrative
text = text.replace(
    'elif field == "fund_manager":\n        narrative = f"The fund manager for {scheme_name} is {val_clean}."',
    'elif field == "fund_manager":\n        narrative = f"The primary lead fund manager for {scheme_name} is {val_clean} as per official scheme records."'
)
text = text.replace(
    'elif field == "factsheet":',
    'elif field == "nav_source":\n        narrative = f"Unitholders can verify daily NAV for {scheme_name} on the official AMFI portal (amfiindia.com) and the AMC website (hdfcfund.com)."\n    elif field == "factsheet":'
)

with open("backend/app/rag/facts.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Updated facts.py")
