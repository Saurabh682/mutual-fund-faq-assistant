import urllib.request
import ssl
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Search for CAS on amfiindia.com
url = "https://www.amfiindia.com/investor-corner/knowledge-center"
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
    html = resp.read().decode("utf-8", errors="replace")

soup = BeautifulSoup(html, "html.parser")
links = []
for a in soup.find_all("a", href=True):
    href = a["href"]
    text = a.get_text().strip().lower()
    if any(k in href.lower() or k in text for k in ("statement", "cas", "capital", "gains", "tax")):
        links.append((a.get_text().strip(), href))

for text, href in links[:20]:
    print(f"{text} -> {href}")
