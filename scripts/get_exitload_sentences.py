import urllib.request
from bs4 import BeautifulSoup
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://groww.in/p/exit-load-in-mutual-funds"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    data = resp.read()

soup = BeautifulSoup(data.decode('utf-8', errors='replace'), 'html.parser')
for s in soup(["script", "style", "noscript"]):
    s.extract()
text = " ".join(soup.get_text().split())

for m in re.finditer(r'[^.!?]*\bexit load\b[^.!?]*[.!?]', text, re.I):
    sent = m.group(0).strip()
    if len(sent) > 20:
        print("Sentence:", sent)
