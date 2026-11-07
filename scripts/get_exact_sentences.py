import urllib.request
from bs4 import BeautifulSoup
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

HEADERS = {'User-Agent': 'Mozilla/5.0'}

targets = [
    ("glossary_ter", "https://groww.in/p/expense-ratio", "Expense ratio is"),
    ("glossary_exit_load", "https://groww.in/p/exit-load-in-mutual-funds", "An exit load is"),
    ("glossary_nav", "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=NetAssetValueNAV", "NAV per unit is"),
    ("glossary_sip", "https://groww.in/p/sip-systematic-investment-plan", "SIP or Systematic Investment Plan is"),
    ("glossary_riskometer", "https://groww.in/p/riskometer", "History of Riskometer"),
    ("glossary_benchmark", "https://groww.in/p/benchmark", "Benchmark is an index"),
    ("glossary_lock_in", "https://groww.in/p/elss-mutual-funds", "As the name suggests, an ELSS fund"),
    ("glossary_aum", "https://groww.in/blog/asset-under-management", "Assets under management are important"),
    ("glossary_direct_regular", "https://groww.in/blog/direct-vs-regular-mutual-fund-reasons", "One of the key distinctions between them is"),
    ("procedure_sebi_categorization", "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=CategorizationOfMutualFundSchemes", "As per SEBI guidelines on Categorization and Rationalization"),
    ("procedure_cutoff_timings", "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=CutOffTimingsAndNewRuleOnApplicableNAV", "For determining applicable Net Asset Value (NAV)"),
    ("procedure_nav_disclosure", "https://www.amfiindia.com/uploads/Reviewoftimelimitfordisclosureof_NAV_f5ebc65062.pdf", "Review of time limit for disclosure of NAV"),
    ("procedure_sebi_riskometer", "https://www.sebi.gov.in/legal/circulars/oct-2020/circular-on-product-labeling-in-mutual-fund-schemes-risk-o-meter_47796.html", "Circular on Product Labeling in Mutual Fund schemes"),
    ("procedure_settlement_cycle", "https://www.sebi.gov.in/legal/circulars/nov-2022/timelines-for-transfer-of-dividend-and-redemption-proceeds-to-unitholders_65455.html", "Timelines for transfer of dividend and redemption proceeds"),
    ("procedure_elss_lock_in", "https://groww.in/blog/3-steps-follow-elss-lock-period-ends", "Like most investments under Section 80C"),
]

for eid, url, needle in targets:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        data = resp.read()
    if url.endswith(".pdf"):
        import io
        from pdfminer.high_level import extract_text
        text = " ".join(extract_text(io.BytesIO(data)).split())
    else:
        soup = BeautifulSoup(data.decode('utf-8', errors='replace'), 'html.parser')
        for s in soup(["script", "style", "noscript"]):
            s.extract()
        text = " ".join(soup.get_text().split())

    idx = text.find(needle)
    if idx >= 0:
        snippet = text[idx:idx+150]
        # find end of sentence or clean boundary
        print(f"[{eid}] FOUND:")
        print(f"   {snippet}")
    else:
        print(f"[{eid}] NOT FOUND for needle '{needle}'")
