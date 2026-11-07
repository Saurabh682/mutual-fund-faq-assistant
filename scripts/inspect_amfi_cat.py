import urllib.request
import sys
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

url = "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=CategorizationOfMutualFundSchemes"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8', errors='replace')

soup = BeautifulSoup(html, 'html.parser')
for s in soup(["script", "style"]):
    s.extract()
text = " ".join(soup.get_text().split())
print("Length:", len(text))
print("Sample:", text[:1500])
