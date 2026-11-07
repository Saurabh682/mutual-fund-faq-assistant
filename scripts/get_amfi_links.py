import urllib.request
import re
from bs4 import BeautifulSoup
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=NetAssetValueNAV"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8', errors='replace')

soup = BeautifulSoup(html, 'html.parser')
links = set()
for a in soup.find_all('a', href=True):
    href = a['href']
    if 'knowledge-center' in href or 'zoneName' in href or 'investor' in href:
        links.add((a.get_text().strip(), href))

for text, href in sorted(links):
    print(f"{text[:40]:40s} -> {href}")
