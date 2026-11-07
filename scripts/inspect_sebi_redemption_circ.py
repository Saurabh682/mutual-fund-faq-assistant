import urllib.request
import re

url = "https://www.sebi.gov.in/legal/circulars/nov-2022/timelines-for-transfer-of-dividend-and-redemption-proceeds-to-unitholders_65455.html"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8', errors='replace')

for m in re.finditer(r'(?:attachdocs|sebi_data|pdf|iframe)[^"\'\s>]+', html, re.I):
    print("Match:", m.group(0))
