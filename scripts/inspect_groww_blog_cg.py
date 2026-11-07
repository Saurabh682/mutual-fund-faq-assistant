import urllib.request
import ssl
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://groww.in/blog/how-to-get-capital-gains-statement-for-mutual-fund-investments"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
    html = resp.read().decode("utf-8", errors="replace")

soup = BeautifulSoup(html, "html.parser")
for s in soup(["script", "style", "noscript"]):
    s.extract()
text = " ".join(soup.get_text().split())

print("Status: 200 OK")
print("Length:", len(text))
print("Sample:\n", text[:1500])
