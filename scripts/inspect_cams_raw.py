import urllib.request
url = "https://www.camsonline.com/assets/PDF/Revision_in_timelines-equity_payout.pdf"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    data = resp.read()
print(data[:300])
