import urllib.request
from bs4 import BeautifulSoup
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://www.sebi.gov.in/legal/circulars/oct-2020/circular-on-product-labeling-in-mutual-fund-schemes-risk-o-meter_47796.html"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8', errors='replace')

soup = BeautifulSoup(html, 'html.parser')
for s in soup(["script", "style"]):
    s.extract()
text = " ".join(soup.get_text().split())
print("Text length:", len(text))
print("Sample:", text[:1000])
for a in soup.find_all('a', href=True):
    if '.pdf' in a['href']:
        print("PDF link:", a['href'])
