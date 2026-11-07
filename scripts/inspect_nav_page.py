import urllib.request
from bs4 import BeautifulSoup
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=NetAssetValueNAV"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8', errors='replace')

soup = BeautifulSoup(html, 'html.parser')
for s in soup(["script", "style"]):
    s.extract()
text = " ".join(soup.get_text().split())
print("Length:", len(text))
for m in re.finditer(r"(?:11[:.]00|disclosure|timing|daily|calculate)", text, re.I):
    start = max(0, m.start() - 100)
    end = min(len(text), m.end() + 100)
    print("Match:", text[start:end])
    print("-" * 50)
