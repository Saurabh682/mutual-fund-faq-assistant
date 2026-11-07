import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

urls = [
    "https://www.camsonline.com/Investors/Statements/Consolidated-Account-Statement",
    "https://www.camsonline.com/Investors/Statements/Capital-Gain-Statement",
    "https://www.amfiindia.com/investor-corner/investor-center/account-statement",
    "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=CapitalGainsTaxOnMutualFunds",
    "https://www.amfiindia.com/investor-corner/knowledge-center/taxation-of-mutual-funds",
    "https://www.hdfcfund.com/investor-services/account-statement",
    "https://www.hdfcfund.com",
    "https://groww.in/blog/how-to-download-capital-gains-statement",
]

for url in urls:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            content = resp.read()
            print(f"200 OK ({len(content)} bytes): {url}")
    except Exception as e:
        print(f"FAILED ({e}): {url}")
