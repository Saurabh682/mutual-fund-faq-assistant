with open("backend/app/rag/entities.py", "r", encoding="utf-8") as f:
    text = f.read()

# Add nav_source to FIELD_GLOSSARY and expand factsheet
old_factsheet = '"factsheet": [\n        "factsheet", "scheme factsheet", "monthly factsheet", "download factsheet", "download the factsheet"\n    ],'
new_factsheet = (
    '"factsheet": [\n'
    '        "factsheet", "scheme factsheet", "monthly factsheet", "download factsheet", "download the factsheet",\n'
    '        "standard procedure to check fund manager tenure", "procedure to check fund manager tenure",\n'
    '        "where to check fund manager tenure", "check fund manager tenure"\n'
    '    ],\n'
    '    "nav_source": [\n'
    '        "official source where unitholders can verify", "where unitholders can verify the nav",\n'
    '        "where to verify the nav", "source where unitholders can verify the nav"\n'
    '    ],'
)

text = text.replace(old_factsheet, new_factsheet)
with open("backend/app/rag/entities.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Updated entities.py")
