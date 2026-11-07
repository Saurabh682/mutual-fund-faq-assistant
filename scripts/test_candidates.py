import hashlib
import json
import os
import re
import urllib.request
import sys
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# The target items we want to verify and support
candidates = [
    # Glossary items
    {
        "id": "glossary_ter",
        "url": "https://groww.in/p/expense-ratio",
        "keywords": ["Expense ratio is"],
    },
    {
        "id": "glossary_exit_load",
        "url": "https://groww.in/p/exit-load-in-mutual-funds",
        "keywords": ["An exit load is"],
    },
    {
        "id": "glossary_nav",
        "url": "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=NetAssetValueNAV",
        "keywords": ["NAV per unit is the market value"],
    },
    {
        "id": "glossary_sip",
        "url": "https://groww.in/p/sip-systematic-investment-plan",
        "keywords": ["SIP or Systematic Investment Plan is"],
    },
    {
        "id": "glossary_riskometer",
        "url": "https://groww.in/p/riskometer",
        "keywords": ["History of Riskometer"],
    },
    {
        "id": "glossary_benchmark",
        "url": "https://groww.in/p/benchmark",
        "keywords": ["Benchmark is an index"],
    },
    {
        "id": "glossary_lock_in",
        "url": "https://groww.in/blog/3-steps-follow-elss-lock-period-ends",
        "keywords": ["Like most investments under Section 80C"],
    },
    {
        "id": "glossary_aum",
        "url": "https://groww.in/blog/asset-under-management",
        "keywords": ["Assets under management are important"],
    },
    {
        "id": "glossary_direct_regular",
        "url": "https://groww.in/blog/direct-vs-regular-mutual-fund-reasons",
        "keywords": ["One of the key distinctions between them is that regular mutual funds"],
    },
    # Regulatory items
    {
        "id": "procedure_sebi_categorization",
        "url": "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=CategorizationOfMutualFundSchemes",
        "keywords": ["As per SEBI guidelines on Categorization and Rationalization"],
    },
    {
        "id": "procedure_cutoff_timings",
        "url": "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=CutOffTimingsAndNewRuleOnApplicableNAV",
        "keywords": ["For determining applicable Net Asset Value (NAV) for subscription and redemption transactions"],
    },
    {
        "id": "procedure_nav_disclosure",
        "url": "https://www.amfiindia.com/uploads/Reviewoftimelimitfordisclosureof_NAV_f5ebc65062.pdf",
        "keywords": ["Review of time limit for disclosure of NAV of Mutual fund schemes"],
    },
    {
        "id": "procedure_sebi_riskometer",
        "url": "https://www.sebi.gov.in/legal/circulars/oct-2020/circular-on-product-labeling-in-mutual-fund-schemes-risk-o-meter_47796.html",
        "keywords": ["Circular on Product Labeling in Mutual Fund schemes – Risk-o-meter Oct 05, 2020| Circular No.: SEBI/HO/IMD/DF3/CIR/P/2020/197"],
    },
    {
        "id": "procedure_settlement_cycle",
        "url": "https://www.sebi.gov.in/legal/circulars/nov-2022/timelines-for-transfer-of-dividend-and-redemption-proceeds-to-unitholders_65455.html",
        "keywords": ["Timelines for transfer of dividend and redemption proceeds to unitholders Nov 25, 2022| Circular No.: SEBI/HO/IMD/IMD-I DOF2/P/CIR/2022/161"],
    },
]

for c in candidates:
    req = urllib.request.Request(c["url"], headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            h = hashlib.sha256(data).hexdigest()
            content_type = resp.headers.get("Content-Type", "")
            if "pdf" in content_type or c["url"].endswith(".pdf"):
                from pdfminer.high_level import extract_text
                import io
                text = " ".join(extract_text(io.BytesIO(data)).split())
            else:
                soup = BeautifulSoup(data.decode("utf-8", errors="replace"), "html.parser")
                for s in soup(["script", "style", "noscript"]):
                    s.extract()
                text = " ".join(soup.get_text().split())

            found_kw = [kw for kw in c["keywords"] if kw in text]
            print(f"{c['id']:32s} | status={resp.status} | bytes={len(data):7d} | hash={h[:12]} | found_kw={bool(found_kw)}")
            if not found_kw:
                print(f"   Sample text: {text[:200]}")
    except Exception as e:
        print(f"{c['id']:32s} | FAILED: {e}")
