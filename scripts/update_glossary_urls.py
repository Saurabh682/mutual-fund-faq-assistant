with open("backend/app/rag/glossary.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    '"source_url": "https://groww.in/p/nav"',
    '"source_url": "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=NetAssetValueNAV"'
).replace(
    '"citation_url": "https://groww.in/p/nav"',
    '"citation_url": "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=NetAssetValueNAV"'
).replace(
    '        "source_url": "https://groww.in/blog/3-steps-follow-elss-lock-period-ends",\n        "citation_url": "https://groww.in/blog/3-steps-follow-elss-lock-period-ends",',
    '        "source_url": "https://groww.in/p/elss-mutual-funds",\n        "citation_url": "https://groww.in/p/elss-mutual-funds",'
).replace(
    '        "source_url": "https://groww.in/blog/3-steps-follow-elss-lock-period-ends",\r\n        "citation_url": "https://groww.in/blog/3-steps-follow-elss-lock-period-ends",',
    '        "source_url": "https://groww.in/p/elss-mutual-funds",\r\n        "citation_url": "https://groww.in/p/elss-mutual-funds",'
)

with open("backend/app/rag/glossary.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Updated glossary.py successfully")
