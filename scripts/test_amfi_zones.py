import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Let's search amfiindia.com pages using Google search or direct test
test_urls = [
    ("riskometer", "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=ProductLabelingRiskometer"),
    ("nav", "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=NetAssetValueNAV"),
    ("cutoff", "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=CutOffTimingsForNAVAllotment"),
    ("settlement", "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=RedemptionProcessAndSettlement"),
    ("elss", "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=EquityLinkedSavingsSchemeELSS"),
]

headers = {'User-Agent': 'Mozilla/5.0'}
for name, u in test_urls:
    req = urllib.request.Request(u, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            print(f"{name}: OK {r.status} ({len(r.read())} bytes)")
    except Exception as e:
        print(f"{name}: Failed ({e})")
