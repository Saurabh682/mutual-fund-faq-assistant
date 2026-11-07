import json

with open("backend/app/rag/procedures.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
in_cg = False
cg_done = False

cg_block = """    {
        "id": "capital_gains_statement",
        "supported": True,
        "status": "supported",
        "patterns": [
            re.compile(r"\\bcapital\\s+gains?\\s+(?:statement|report|tax\\s+statement|p&l)\\b", re.I),
            re.compile(r"\\bdownload\\s+(?:my\\s+)?(?:capital\\s+gains?|tax\\s+statement|p&l)\\b", re.I),
            re.compile(r"\\b(?:where|how)\\s+(?:to|can\\s+i|do\\s+i)\\s+(?:download|get|find)\\s+(?:my\\s+)?(?:capital\\s+gains?|tax\\s+statement|p&l)\\b", re.I),
            re.compile(r"\\bcapital\\s+gains?\\b.*\\b(?:groww|statement|download)\\b", re.I),
        ],
        "procedure_title": "Download Capital Gains Statement",
        "platform": "Groww Mobile App & Web",
        "navigation": "You → SIP & Reports → Capital Gain → Download",
        "narrative": (
            "To download your mutual fund capital gains statement on Groww, open the Groww app and navigate to the 'You' tab at the bottom right. "
            "Select 'SIP & Reports', tap 'Capital Gain', choose the relevant financial year, and download your statement."
        ),
        "table_rows": [
            ("Procedure", "Download Capital Gains Statement"),
            ("Platform", "Groww Mobile App & Web"),
            ("Navigation", "You → SIP & Reports → Capital Gain → Download"),
            ("Available Formats", "PDF & Excel (.xlsx)"),
        ],
        "source_url": "https://groww.in/blog/how-to-get-capital-gains-statement-for-mutual-fund-investments",
        "citation_url": "https://groww.in/blog/how-to-get-capital-gains-statement-for-mutual-fund-investments",
        "verified_on": "2026-11-05",
    },
"""

i = 0
while i < len(lines):
    line = lines[i]
    if '"id": "capital_gains_statement"' in line and not cg_done:
        # replace the whole item until '},'
        while i < len(lines) and not lines[i].strip().startswith("},"):
            i += 1
        i += 1 # skip '},'
        new_lines.append(cg_block)
        cg_done = True
        continue
    else:
        new_lines.append(line)
        i += 1

with open("backend/app/rag/procedures.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Capital gains statement procedure successfully updated in procedures.py")
