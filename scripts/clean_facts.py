with open("backend/app/rag/facts.py", "r", encoding="utf-8") as f:
    text = f.read()

bad_part_1 = """            if field == "nav_source":
                return {
                    "scheme_id": scheme_id,
                    "field": field,
                    "value": "AMFI official portal (amfiindia.com) and hdfcfund.com",
                    "value_str": "AMFI official portal (amfiindia.com) and hdfcfund.com",
                    "value_num": None,
                    "as_of": "2026-11-05",
                    "doc_date": "2026-11-05",
                }
            elif field == "nav_source":
        narrative = f"Unitholders can verify daily NAV for {scheme_name} on the official AMFI portal (amfiindia.com) and the AMC website (hdfcfund.com)."
    elif field == "factsheet":"""

good_part_1 = """            if field == "nav_source":
                return {
                    "scheme_id": scheme_id,
                    "field": field,
                    "value": "AMFI official portal (amfiindia.com) and hdfcfund.com",
                    "value_str": "AMFI official portal (amfiindia.com) and hdfcfund.com",
                    "value_num": None,
                    "as_of": "2026-11-05",
                    "doc_date": "2026-11-05",
                }
            elif field == "factsheet":"""

bad_part_2 = """    elif field == "nav_source":
                return {
                    "scheme_id": scheme_id,
                    "field": field,
                    "value": "AMFI official portal (amfiindia.com) and hdfcfund.com",
                    "value_str": "AMFI official portal (amfiindia.com) and hdfcfund.com",
                    "value_num": None,
                    "as_of": "2026-11-05",
                    "doc_date": "2026-11-05",
                }
            elif field == "nav_source":
        narrative = f"Unitholders can verify daily NAV for {scheme_name} on the official AMFI portal (amfiindia.com) and the AMC website (hdfcfund.com)."
    elif field == "factsheet":"""

good_part_2 = """    elif field == "nav_source":
        narrative = f"Unitholders can verify daily NAV for {scheme_name} on the official AMFI portal (amfiindia.com) and the AMC website (hdfcfund.com)."
    elif field == "factsheet":"""

text = text.replace(bad_part_1, good_part_1).replace(bad_part_2, good_part_2)

with open("backend/app/rag/facts.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Cleaned up facts.py")
