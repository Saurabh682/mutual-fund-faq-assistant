import urllib.request
from bs4 import BeautifulSoup
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://groww.in/p/elss-mutual-funds"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    data = resp.read()

soup = BeautifulSoup(data.decode('utf-8', errors='replace'), 'html.parser')
for s in soup(["script", "style", "noscript"]):
    s.extract()
text = " ".join(soup.get_text().split())
print("Text length:", len(text))
print("Sample:", text[:1000])
for kw in ["lock-in", "3 years", "Section 80C"]:
    print(f"Has '{kw}':", kw in text)
