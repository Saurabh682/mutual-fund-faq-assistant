import urllib.request
import re
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://groww.in/help/mutual-funds/sip"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode('utf-8', errors='replace')
    print("HTML length:", len(html))
    # Search for __NEXT_DATA__
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html)
    if m:
        data = json.loads(m.group(1))
        print("Found __NEXT_DATA__!")
        props = data.get('props', {})
        pageProps = props.get('pageProps', {})
        print("pageProps keys:", list(pageProps.keys()))
        # Print a snippet of pageProps
        s = json.dumps(pageProps, indent=2)
        print("pageProps sample (500 chars):", s[:500])
        # Search for words in pageProps
        print("Matches for 'SIP' in json:", len(re.findall(r'SIP', s, re.I)))
    else:
        print("No __NEXT_DATA__ script found")
except Exception as e:
    print("Error:", e)
