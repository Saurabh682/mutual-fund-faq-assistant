import urllib.request
import urllib.error

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

candidate_urls = [
    # SEBI Circulars
    ("sebi_categorization", "https://www.sebi.gov.in/legal/circulars/oct-2017/categorization-and-rationalization-of-mutual-fund-schemes_36199.html"),
    ("sebi_cutoff", "https://www.sebi.gov.in/legal/circulars/sep-2020/uniformity-in-applicability-of-net-asset-value-nav-across-various-schemes-upon-realization-of-funds_47630.html"),
    ("sebi_riskometer", "https://www.sebi.gov.in/legal/circulars/oct-2020/circular-on-product-labeling-in-mutual-fund-schemes-riskometer_47791.html"),
    # AMFI Knowledge Center
    ("amfi_home", "https://www.amfiindia.com/investor-corner/knowledge-center"),
    ("amfi_kyc", "https://www.amfiindia.com/investor-corner/knowledge-center/kyc.html"),
    ("amfi_sip", "https://www.amfiindia.com/investor-corner/knowledge-center/systematic-investment-plan.html"),
    ("amfi_nav", "https://www.amfiindia.com/investor-corner/knowledge-center/net-asset-value.html"),
    ("amfi_elss", "https://www.amfiindia.com/investor-corner/knowledge-center/elss.html"),
    ("amfi_ter", "https://www.amfiindia.com/investor-corner/knowledge-center/expense-ratio.html"),
    ("amfi_exit_load", "https://www.amfiindia.com/investor-corner/knowledge-center/exit-load.html"),
    # HDFC AMC
    ("hdfc_nav", "https://www.hdfcfund.com/nav-dividend"),
    ("hdfc_faq", "https://www.hdfcfund.com/investor-services/faq"),
]

for label, url in candidate_urls:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read()
            print(f"{label:20s}: HTTP {resp.status} - {len(content)} bytes")
    except urllib.error.HTTPError as e:
        print(f"{label:20s}: HTTPError {e.code}")
    except Exception as e:
        print(f"{label:20s}: Error {e}")
