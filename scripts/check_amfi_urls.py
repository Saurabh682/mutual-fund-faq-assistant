import urllib.request
import urllib.error
import sys

sys.stdout.reconfigure(encoding='utf-8')

urls_to_test = [
    "https://www.amfiindia.com/investor-corner/knowledge-center/categorization-of-mutual-fund-schemes.html",
    "https://www.amfiindia.com/investor-corner/knowledge-center/types-of-mutual-funds.html",
    "https://www.amfiindia.com/investor-corner/knowledge-center/sebi-guidelines.html",
    "https://www.amfiindia.com/research-information/other-data/categorization-of-mutual-fund-schemes",
    "https://www.sebi.gov.in/sebi_data/attachdocs/oct-2017/1509103633344.pdf",
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

for u in urls_to_test:
    req = urllib.request.Request(u, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"OK {resp.status}: {u} ({len(resp.read())} bytes)")
    except urllib.error.HTTPError as e:
        print(f"HTTPError {e.code}: {u}")
    except Exception as e:
        print(f"Error {u}: {e}")
