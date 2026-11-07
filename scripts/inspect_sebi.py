import os
import sys
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

path = os.path.join("data", "snapshots", "procedure_sebi_categorization.html")
with open(path, "r", encoding="utf-8", errors="replace") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

for s in soup(["script", "style"]):
    s.extract()
text = " ".join(soup.get_text().split())
print("Full text length:", len(text))
print("Text content:", text)
