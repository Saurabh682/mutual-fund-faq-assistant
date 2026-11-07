"""Official Static Knowledge Snapshot Engine and Verifier.

Fetches authoritative regulatory (SEBI, AMFI) and educational pages,
validates that supporting sentences are exact literal substrings of raw snapshot content,
enforces unique SHA-256 digests across all URLs, flags unsupported client-rendered items,
and writes data/snapshots/snapshots_manifest.json.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SNAPSHOTS_DIR = os.path.join(BASE_DIR, "data", "snapshots")
MANIFEST_PATH = os.path.join(SNAPSHOTS_DIR, "snapshots_manifest.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# 15 Verified Authoritative Entries
SUPPORTED_ENTRIES = [
    # Glossary (9 items)
    {
        "id": "glossary_ter",
        "category": "glossary",
        "concept": "Total Expense Ratio (TER)",
        "url": "https://groww.in/p/expense-ratio",
        "supporting_sentence": "Expense ratio is the annual maintenance charge levied by mutual funds to finance its expenses.",
        "verified_on": "2026-11-05",
    },
    {
        "id": "glossary_exit_load",
        "category": "glossary",
        "concept": "Exit Load",
        "url": "https://groww.in/p/exit-load-in-mutual-funds",
        "supporting_sentence": "An exit load is the fee AMCs (Asset management companies) charge the investor at the time of exiting or retrieving the units of the fund.",
        "verified_on": "2026-11-05",
    },
    {
        "id": "glossary_nav",
        "category": "glossary",
        "concept": "Net Asset Value (NAV)",
        "url": "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=NetAssetValueNAV",
        "supporting_sentence": "NAV per unit is the market value of securities of a scheme divided by the total number of units of the scheme on a given date.",
        "verified_on": "2026-11-05",
    },
    {
        "id": "glossary_sip",
        "category": "glossary",
        "concept": "Systematic Investment Plan (SIP)",
        "url": "https://groww.in/p/sip-systematic-investment-plan",
        "supporting_sentence": "SIP or Systematic Investment Plan is a process of investing a fixed amount of money in a mutual funds/stocks on a daily, weekly, monthly or quarterly basis.",
        "verified_on": "2026-11-05",
    },
    {
        "id": "glossary_riskometer",
        "category": "glossary",
        "concept": "SEBI Riskometer",
        "url": "https://groww.in/p/riskometer",
        "supporting_sentence": "History of Riskometer The current version of the meter was introduced on 1st July 2015 by SEBI.",
        "verified_on": "2026-11-05",
    },
    {
        "id": "glossary_benchmark",
        "category": "glossary",
        "concept": "Benchmark Index",
        "url": "https://groww.in/p/benchmark",
        "supporting_sentence": "Benchmark is an index that is used to Measure a Mutual Fund’s overall performance.",
        "verified_on": "2026-11-05",
    },
    {
        "id": "glossary_lock_in",
        "category": "glossary",
        "concept": "Lock-in Period",
        "url": "https://groww.in/p/elss-mutual-funds",
        "supporting_sentence": "As the name suggests, an ELSS fund is an equity-oriented scheme with a mandatory lock-in period of three years.",
        "verified_on": "2026-11-05",
    },
    {
        "id": "glossary_aum",
        "category": "glossary",
        "concept": "Assets Under Management (AUM)",
        "url": "https://groww.in/blog/asset-under-management",
        "supporting_sentence": "Assets under management are important because- Showcases the Size of a Fund",
        "verified_on": "2026-11-05",
    },
    {
        "id": "glossary_direct_regular",
        "category": "glossary",
        "concept": "Direct vs Regular Plans",
        "url": "https://groww.in/blog/direct-vs-regular-mutual-fund-reasons",
        "supporting_sentence": "One of the key distinctions between them is that regular mutual funds (MFs) have a distribution commission, while direct mutual funds do not.",
        "verified_on": "2026-11-05",
    },

    # Regulatory Procedures (6 items)
    {
        "id": "procedure_sebi_categorization",
        "category": "procedure",
        "concept": "SEBI Scheme Categorization Framework",
        "url": "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=CategorizationOfMutualFundSchemes",
        "supporting_sentence": "As per SEBI guidelines on Categorization and Rationalization of schemes issued in October 2017, mutual fund schemes are classified as –Equity SchemesDebt SchemesHybrid SchemesSolution Oriented Schemes – For Retirement and ChildrenOther Schemes – Index Funds & ETFs and Fund of Funds",
        "verified_on": "2026-11-05",
    },
    {
        "id": "procedure_cutoff_timings",
        "category": "procedure",
        "concept": "SEBI Uniform NAV Cut-Off Timings",
        "url": "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=CutOffTimingsAndNewRuleOnApplicableNAV",
        "supporting_sentence": "For determining applicable Net Asset Value (NAV) for subscription and redemption transactions",
        "verified_on": "2026-11-05",
    },
    {
        "id": "procedure_nav_disclosure",
        "category": "procedure",
        "concept": "Daily NAV Disclosure Timelines",
        "url": "https://www.amfiindia.com/uploads/Reviewoftimelimitfordisclosureof_NAV_f5ebc65062.pdf",
        "supporting_sentence": "Review of time limit for disclosure of NAV of Mutual fund schemes investing overseas",
        "verified_on": "2026-11-05",
    },
    {
        "id": "procedure_sebi_riskometer",
        "category": "procedure",
        "concept": "SEBI 6-Tier Mutual Fund Riskometer Framework",
        "url": "https://www.sebi.gov.in/legal/circulars/oct-2020/circular-on-product-labeling-in-mutual-fund-schemes-risk-o-meter_47796.html",
        "supporting_sentence": "Circular on Product Labeling in Mutual Fund schemes – Risk-o-meter",
        "verified_on": "2026-11-05",
    },
    {
        "id": "procedure_settlement_cycle",
        "category": "procedure",
        "concept": "Mutual Fund Redemption Settlement Timelines",
        "url": "https://www.sebi.gov.in/legal/circulars/nov-2022/timelines-for-transfer-of-dividend-and-redemption-proceeds-to-unitholders_65455.html",
        "supporting_sentence": "Timelines for transfer of dividend and redemption proceeds to unitholders",
        "verified_on": "2026-11-05",
    },
    {
        "id": "procedure_elss_lock_in",
        "category": "procedure",
        "concept": "ELSS Mutual Fund Statutory Lock-in Period",
        "url": "https://groww.in/blog/3-steps-follow-elss-lock-period-ends",
        "supporting_sentence": "Like most investments under Section 80C, ELSS funds also have a mandatory lock-in.",
        "verified_on": "2026-11-05",
    },
]

# Client-Rendered JS Help Items marked unsupported
UNSUPPORTED_GROWW_HELP_ITEMS = [
    ("procedure_capital_gains_statement", "https://groww.in/help/reports", "Download Capital Gains Statement"),
    ("procedure_redeem_mutual_fund", "https://groww.in/help/mutual-funds/order/redemption", "Redeem Mutual Fund Units"),
    ("procedure_start_sip", "https://groww.in/help/mutual-funds/sip", "Start Systematic Investment Plan (SIP)"),
    ("procedure_kyc_process", "https://groww.in/help/mutual-funds/kyc", "Mutual Fund KYC Verification"),
    ("procedure_autopay_mandate", "https://groww.in/help/mutual-funds/sip/autopay", "Set Up SIP AutoPay / Bank Mandate"),
    ("procedure_switch_procedure", "https://groww.in/switch", "Switch from Regular to Direct Plan"),
    ("procedure_sip_bounce", "https://groww.in/help/mutual-funds/sip/missed-installment", "SIP Installment Insufficient Balance / Bounce Policy"),
    ("procedure_sip_pause", "https://groww.in/help/mutual-funds/sip/pause", "Pause Active SIP Installments"),
    ("procedure_bank_update", "https://groww.in/help/account/bank-account", "Update Registered Bank Account in Mutual Funds"),
    ("procedure_order_tracking", "https://groww.in/help/mutual-funds/order/track", "Track Mutual Fund Order Status"),
]


def extract_clean_text(data: bytes, url: str) -> str:
    """Extracts clean text from HTML or PDF bytes."""
    if url.endswith(".pdf"):
        import io
        from pdfminer.high_level import extract_text
        return " ".join(extract_text(io.BytesIO(data)).split())

    html = data.decode("utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")
    for s in soup(["script", "style", "noscript"]):
        s.extract()
    return " ".join(soup.get_text().split())


def run():
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
    manifest: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_items": len(SUPPORTED_ENTRIES) + len(UNSUPPORTED_GROWW_HELP_ITEMS),
        "supported_count": len(SUPPORTED_ENTRIES),
        "unsupported_count": len(UNSUPPORTED_GROWW_HELP_ITEMS),
        "snapshots": {},
    }

    seen_hashes: Dict[str, str] = {}

    print("=" * 80)
    print("FETCHING & VALIDATING SUPPORTED STATIC KNOWLEDGE ENTRIES")
    print("=" * 80)

    for item in SUPPORTED_ENTRIES:
        eid = item["id"]
        url = item["url"]
        supp = item["supporting_sentence"]
        ext = ".pdf" if url.endswith(".pdf") else ".html"
        snapshot_file = f"{eid}{ext}"
        target_path = os.path.join(SNAPSHOTS_DIR, snapshot_file)

        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                status = resp.status
                data = resp.read()
        except Exception as e:
            print(f"FAILED to fetch {eid} from {url}: {e}")
            raise RuntimeError(f"Cannot fetch required entry {eid}: {e}")

        # Compute SHA-256 hash
        h = hashlib.sha256(data).hexdigest()
        if h in seen_hashes:
            raise ValueError(f"DUPLICATE HASH detected: {eid} shares hash {h} with {seen_hashes[h]}")
        seen_hashes[h] = eid

        # Extract normalized text
        page_text = extract_clean_text(data, url)

        # Enforce exact literal substring
        norm_supp = " ".join(supp.split())
        norm_page = " ".join(page_text.split())
        if norm_supp not in norm_page:
            raise AssertionError(f"Supporting sentence for {eid} is NOT a substring of page text!\nExpected: {norm_supp}\nPage snippet: {norm_page[:300]}")

        # Enforce no 404, not found, or enable JavaScript
        lower_page = norm_page.lower()
        if re.search(r"\b404\b|page not found", lower_page):
            raise AssertionError(f"Snapshot for {eid} contains 404/not found")
        if "enable javascript" in lower_page:
            raise AssertionError(f"Snapshot for {eid} contains 'enable javascript'")

        # Save snapshot
        with open(target_path, "wb") as sf:
            sf.write(data)

        manifest["snapshots"][eid] = {
            "status": "supported",
            "category": item["category"],
            "concept": item["concept"],
            "url": url,
            "http_status": status,
            "sha256": h,
            "bytes": len(data),
            "snapshot_file": snapshot_file,
            "supporting_sentence": supp,
            "verified_on": item["verified_on"],
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
        print(f"✅ {eid:32s} | status={status} | {len(data):7d} bytes | hash={h[:12]} | substring verified")

    print("\n" + "=" * 80)
    print("RECORDING UNSUPPORTED CLIENT-RENDERED GROWW HELP ITEMS")
    print("=" * 80)

    for eid, url, title in UNSUPPORTED_GROWW_HELP_ITEMS:
        manifest["snapshots"][eid] = {
            "status": "unsupported",
            "category": "procedure",
            "concept": title,
            "url": url,
            "reason": "Client-rendered JS shell lacking static DOM article text; stopped from being served per compliance specification.",
            "verified_on": "2026-11-05",
        }
        print(f"🚫 {eid:32s} | marked unsupported (not served)")

    with open(MANIFEST_PATH, "w", encoding="utf-8") as mf:
        json.dump(manifest, mf, indent=2)

    print("\nSaved manifest to:", MANIFEST_PATH)


if __name__ == "__main__":
    run()
