import urllib.request
import urllib.error

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

probe_urls = [
    # AMFI
    ("amfi_root", "https://www.amfiindia.com/"),
    ("amfi_investor_center", "https://www.amfiindia.com/investor-corner"),
    ("amfi_investor_education", "https://www.amfiindia.com/investor-corner/investor-education"),
    ("amfi_mf_basics", "https://www.amfiindia.com/investor-corner/knowledge-center/what-are-mutual-funds-investments.html"),
    ("amfi_faqs", "https://www.amfiindia.com/investor-corner/faqs"),
    ("amfi_nav_history", "https://www.amfiindia.com/net-asset-value"),
    ("amfi_nav_disclosure", "https://www.amfiindia.com/research-information/other-data/nav-disclosure"),
    ("amfi_scheme_details", "https://www.amfiindia.com/research-information/other-data/scheme-details"),
    # SEBI
    ("sebi_root", "https://www.sebi.gov.in/"),
    ("sebi_categorization", "https://www.sebi.gov.in/legal/circulars/oct-2017/categorization-and-rationalization-of-mutual-fund-schemes_36199.html"),
]

for label, url in probe_urls:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read()
            print(f"{label:25s}: HTTP {resp.status} - {len(content)} bytes")
    except urllib.error.HTTPError as e:
        print(f"{label:25s}: HTTPError {e.code}")
    except Exception as e:
        print(f"{label:25s}: Error {e}")
