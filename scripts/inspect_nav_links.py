import urllib.request
from bs4 import BeautifulSoup
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=NetAssetValueNAV"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8', errors='replace')

soup = BeautifulSoup(html, 'html.parser')
for a in soup.find_all('a', href=True):
    if 'Disclosure' in a.get_text() or 'NAV' in a.get_text():
        print(a.get_text().strip(), "->", a['href'])
