"""AMFI Educational Glossary Store for Mutual Fund Concepts.

Provides verified, SEBI-compliant educational definitions for core mutual fund terms:
- Total Expense Ratio (TER)
- Exit Load
- Net Asset Value (NAV)
- Systematic Investment Plan (SIP)
- SEBI Riskometer
- Benchmark Index
- Lock-in Period
- Assets Under Management (AUM)
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from app.guardrails.refusal import get_default_corpus_date, normalize_date_footer
from app.guardrails.validator import validate_response


GLOSSARY_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "id": "ter",
        "field": "ter_direct",
        "patterns": [
            re.compile(r"\b(?:what\s+(?:is|are|does)|explain|define|meaning\s+of)\s+.*?(?:\btotal\s+expense\s+ratio\b|\bexpense\s+ratio\b|\bter\b)", re.I),
            re.compile(r"^(?:ter|expense\s+ratio)\??$", re.I),
        ],
        "concept": "Total Expense Ratio (TER)",
        "narrative": (
            "Total Expense Ratio (TER) covers the annual management and operational expenses charged by an AMC to operate a mutual fund. "
            "Direct plans feature lower annual operating costs and a lower TER than Regular plans because no distributor commissions are paid."
        ),
        "table_rows": [
            ("Financial Term", "Total Expense Ratio (TER)"),
            ("Definition", "Annual operating fee charged as a percentage of daily AUM"),
            ("Direct Advantage", "Lower TER due to zero intermediary distributor commission"),
        ],
        "source_url": "https://groww.in/p/expense-ratio",
        "citation_url": "https://groww.in/p/expense-ratio",
        "verified_on": "2026-11-05",
    },
    {
        "id": "exit_load",
        "field": "exit_load",
        "patterns": [
            re.compile(r"\b(?:what\s+(?:is|are|does)|explain|define|meaning\s+of)\s+.*?\bexit\s+load\b", re.I),
            re.compile(r"^exit\s+load\??$", re.I),
        ],
        "concept": "Exit Load",
        "narrative": (
            "An exit load is a premature exit fee or redemption fee charged by an AMC when an investor redeems or switches mutual fund units before a specified holding window. "
            "Units redeemed after the designated exit load window incur zero exit charges."
        ),
        "table_rows": [
            ("Financial Term", "Exit Load"),
            ("Definition", "Penalty percentage applied on redemption before a specified tenure"),
            ("Exemption", "Zero exit load after the scheme-mandated holding window"),
        ],
        "source_url": "https://groww.in/p/exit-load-in-mutual-funds",
        "citation_url": "https://groww.in/p/exit-load-in-mutual-funds",
        "verified_on": "2026-11-05",
    },
    {
        "id": "nav",
        "field": "nav",
        "patterns": [
            re.compile(r"\b(?:what\s+(?:is|are|does)|explain|define|meaning\s+of)\s+.*?\b(?:net\s+asset\s+value|nav)\b", re.I),
            re.compile(r"^nav\??$", re.I),
        ],
        "concept": "Net Asset Value (NAV)",
        "narrative": (
            "Net Asset Value (NAV) represents the per-unit market value of securities held in a mutual fund scheme. "
            "It is calculated daily by dividing net fund assets by total outstanding units, and published after market close on business days."
        ),
        "table_rows": [
            ("Financial Term", "Net Asset Value (NAV)"),
            ("Formula", "(Total Assets - Liabilities) / Outstanding Units"),
            ("Frequency", "Calculated and published daily after market close"),
        ],
        "source_url": "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=NetAssetValueNAV",
        "citation_url": "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=NetAssetValueNAV",
        "verified_on": "2026-11-05",
    },
    {
        "id": "sip",
        "field": "min_sip",
        "patterns": [
            re.compile(r"\b(?:what\s+(?:is|are|does)|explain|define|meaning\s+of)\s+.*?(?:systematic\s+investment\s+plan|sip)\b", re.I),
            re.compile(r"^sip\??$", re.I),
        ],
        "concept": "Systematic Investment Plan (SIP)",
        "narrative": (
            "A Systematic Investment Plan (SIP) allows investors to invest a fixed predetermined amount at regular intervals into a mutual fund scheme. "
            "SIP promotes financial discipline and enables rupee-cost averaging across market cycles."
        ),
        "table_rows": [
            ("Financial Term", "Systematic Investment Plan (SIP)"),
            ("Mechanism", "Periodic automated investments (monthly or quarterly)"),
            ("Core Benefit", "Rupee-cost averaging and long-term compounding"),
        ],
        "source_url": "https://groww.in/p/sip-systematic-investment-plan",
        "citation_url": "https://groww.in/p/sip-systematic-investment-plan",
        "verified_on": "2026-11-05",
    },
    {
        "id": "riskometer",
        "field": "riskometer",
        "patterns": [
            re.compile(r"\b(?:what\s+(?:is|are|does)|explain|define|meaning\s+of)\s+.*?\briskometer\b", re.I),
            re.compile(r"^riskometer\??$", re.I),
        ],
        "concept": "SEBI Riskometer",
        "narrative": (
            "The SEBI Riskometer is a standardized 6-level graphical meter depicting the risk level of principal invested in a scheme. "
            "Tiers range from Low to Very High Risk, with Very High Risk indicating that principal will be at very high risk."
        ),
        "table_rows": [
            ("Framework", "SEBI Product Labeling Riskometer"),
            ("Tiers", "Low, Low-Mod, Moderate, Mod-High, High, Very High"),
            ("Review Cycle", "Evaluated monthly based on portfolio risk"),
        ],
        "source_url": "https://groww.in/p/riskometer",
        "citation_url": "https://groww.in/p/riskometer",
        "verified_on": "2026-11-05",
    },
    {
        "id": "benchmark",
        "field": "benchmark",
        "patterns": [
            re.compile(r"\b(?:what\s+(?:is|are|does)|explain|define|meaning\s+of)\s+.*?\bbenchmark\b", re.I),
            re.compile(r"^benchmark\??$", re.I),
        ],
        "concept": "Benchmark Index",
        "narrative": (
            "A mutual fund benchmark is an independent standard against which a fund's returns and portfolio performance are evaluated. "
            "SEBI mandates that all AMCs designate a primary benchmark index matching each scheme's asset mandate."
        ),
        "table_rows": [
            ("Financial Term", "Benchmark Index"),
            ("Role", "Standard reference yardstick to evaluate fund performance"),
            ("Mandate", "Designated by SEBI to align with fund asset class"),
        ],
        "source_url": "https://groww.in/p/benchmark",
        "citation_url": "https://groww.in/p/benchmark",
        "verified_on": "2026-11-05",
    },
    {
        "id": "lock_in",
        "field": "lock_in",
        "patterns": [
            re.compile(r"\b(?:what\s+(?:is|are|does)|explain|define|meaning\s+of)\s+.*?\block[\s-]?in\b", re.I),
            re.compile(r"^lock[\s-]?in(?:\s+period)?\??$", re.I),
        ],
        "concept": "Lock-in Period",
        "narrative": (
            "A lock-in period is a mandatory statutory duration during which mutual fund units cannot be redeemed, switched, or transferred. "
            "Open-ended equity and debt funds have zero lock-in period, whereas ELSS funds have a mandatory 3-year lock-in under Section 80C."
        ),
        "table_rows": [
            ("Statutory Rule", "Lock-in Period"),
            ("ELSS Requirement", "Mandatory 3 years from allotment date"),
            ("Open-Ended Schemes", "Zero statutory lock-in"),
        ],
        "source_url": "https://groww.in/p/elss-mutual-funds",
        "citation_url": "https://groww.in/p/elss-mutual-funds",
        "verified_on": "2026-11-05",
    },
    {
        "id": "aum",
        "field": "aum",
        "patterns": [
            re.compile(r"\b(?:what\s+(?:is|are|does)|explain|define|meaning\s+of)\s+.*?\b(?:assets?\s+under\s+management|aum)\b", re.I),
            re.compile(r"^aum\??$", re.I),
        ],
        "concept": "Assets Under Management (AUM)",
        "narrative": (
            "Assets Under Management (AUM) is the total market value of all financial assets managed by a mutual fund scheme or fund house. "
            "Scheme AUM fluctuates daily based on market price movements and net investor subscriptions or redemptions."
        ),
        "table_rows": [
            ("Financial Term", "Assets Under Management (AUM)"),
            ("Definition", "Total market value of portfolio assets managed by the fund"),
            ("Fluctuation", "Changes daily based on market valuation and capital flows"),
        ],
        "source_url": "https://groww.in/blog/asset-under-management",
        "citation_url": "https://groww.in/blog/asset-under-management",
        "verified_on": "2026-11-05",
    },
    {
        "id": "direct_regular",
        "field": "direct_plan",
        "patterns": [
            re.compile(r"\b(?:difference\s+between\s+direct\s+and\s+regular|direct\s+vs\s+regular|direct\s+plan\s+vs\s+regular\s+plan)\b", re.I),
        ],
        "concept": "Direct vs Regular Plans",
        "narrative": (
            "Direct mutual fund plans have lower expense ratios because unitholders invest directly with zero distributor commission fees. "
            "Regular plans include ongoing intermediary distributor commission embedded within the fund's expense ratio."
        ),
        "table_rows": [
            ("Plan Type", "Direct vs Regular Mutual Fund Plans"),
            ("Direct Plan", "Zero intermediary commission, resulting in higher returns"),
            ("Regular Plan", "Includes distributor commission embedded in TER"),
        ],
        "source_url": "https://groww.in/blog/direct-vs-regular-mutual-fund-reasons",
        "citation_url": "https://groww.in/blog/direct-vs-regular-mutual-fund-reasons",
        "verified_on": "2026-11-05",
    },
]

# Strict build-time validation of glossary definitions
for item in GLOSSARY_DEFINITIONS:
    if not item.get("source_url") or not str(item.get("source_url")).startswith("https://"):
        raise ValueError(f"Glossary entry '{item.get('id')}' missing mandatory 'source_url'")
    if not item.get("verified_on") or not re.match(r"^\d{4}-\d{2}-\d{2}$", str(item.get("verified_on"))):
        raise ValueError(f"Glossary entry '{item.get('id')}' missing mandatory 'verified_on'")


def lookup_glossary(query: str) -> Optional[Dict[str, Any]]:
    """Checks if a query is asking for an educational concept definition.

    Returns:
        Structured response dictionary validated against the contract, or None.
    """
    clean_q = query.strip()
    if re.search(r"\b(?:cut[\s-]?off|timings?|same\s+day|disclosure|how\s+many\s+months|penny[\s-]?drop|pause|bounce|min|minimum|how\s+much)\b", clean_q, re.I):
        return None
    doc_date = get_default_corpus_date()

    for item in GLOSSARY_DEFINITIONS:
        for p in item["patterns"]:
            if p.search(clean_q):
                table_lines = [
                    "| Aspect | Detail |",
                    "| :--- | :--- |",
                ]
                for k, v in item["table_rows"]:
                    table_lines.append(f"| **{k}** | {v} |")

                stat_table = "\n".join(table_lines)
                body = f"{item['narrative']}\n\n{stat_table}"

                # Run through Contract Validator as Final Gate
                citation_url = item.get("source_url") or item.get("citation_url")
                effective_date = item.get("verified_on") or doc_date

                val_res = validate_response(
                    draft_text=body,
                    context_chunks=None,
                    primary_url=citation_url,
                    doc_date=effective_date,
                )

                return {
                    "text": val_res.text,
                    "citation_url": val_res.citation_url,
                    "last_updated": val_res.last_updated,
                    "rendered": val_res.rendered,
                    "sentence_count": val_res.sentence_count,
                    "source": "glossary_store",
                    "glossary_id": item["id"],
                    "field": item["field"],
                    "scheme_id": None,
                }

    return None
