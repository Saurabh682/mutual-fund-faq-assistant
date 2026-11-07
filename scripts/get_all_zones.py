import urllib.request
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=NetAssetValueNAV"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8', errors='replace')

zones = set(re.findall(r'zoneName=([a-zA-Z0-9_-]+)', html))
for z in sorted(zones):
    print("Found zone:", z)
