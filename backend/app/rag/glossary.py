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
from app.guardrails.refusal import get_default_corpus_date


GLOSSARY_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "id": "ter",
        "field": "ter_direct",
        "patterns": [
            re.compile(r"\b(?:what\s+(?:is|are)|explain|define|meaning\s+of)\s+(?:a\s+)?(?:the\s+)?(?:total\s+expense\s+ratio|expense\s+ratio|ter)\b", re.I),
            re.compile(r"\b(?:what\s+does\s+(?:ter|expense\s+ratio)\s+(?:mean|stand\s+for))\b", re.I),
            re.compile(r"^(?:ter|expense\s+ratio)\??$", re.I),
        ],
        "concept": "Total Expense Ratio (TER)",
        "narrative": (
            "Total Expense Ratio (TER) is the annual percentage fee charged by an AMC to operate a mutual fund, "
            "covering management, administration, and operational costs. Direct plans feature a lower TER than "
            "Regular plans because no distributor commissions are paid. TER is calculated and accrued daily in the fund's NAV."
        ),
        "table_rows": [
            ("Financial Term", "Total Expense Ratio (TER)"),
            ("Definition", "Annual operating & management fee charged as a percentage of AUM"),
            ("Impact", "Deducted daily from the scheme Net Asset Value (NAV)"),
            ("Direct vs Regular", "Direct plans have lower TER due to zero distributor commission"),
            ("Regulatory Cap", "SEBI mandates maximum TER limits tiered by fund asset size"),
        ],
        "citation_url": "https://www.amfiindia.com/investor-corner/knowledge-center",
    },
    {
        "id": "exit_load",
        "field": "exit_load",
        "patterns": [
            re.compile(r"\b(?:what\s+is|explain|define|meaning\s+of)\s+(?:an?\s+)?(?:the\s+)?exit\s+load\b", re.I),
            re.compile(r"\b(?:what\s+does\s+exit\s+load\s+mean)\b", re.I),
            re.compile(r"^exit\s+load\??$", re.I),
        ],
        "concept": "Exit Load",
        "narrative": (
            "An exit load is a fee or penalty charged by an AMC when an investor redeems or switches mutual fund units "
            "before a specified holding window (such as 1 year). It is designed to discourage premature redemptions and "
            "protect long-term unitholders. Units redeemed after the designated exit load period incur zero exit charges."
        ),
        "table_rows": [
            ("Financial Term", "Exit Load"),
            ("Definition", "Penalty percentage applied on redemption before a specified tenure"),
            ("Purpose", "Protects remaining investors by discouraging short-term withdrawals"),
            ("Deduction", "Subtracted from the redemption NAV payout to the investor"),
            ("Exemption", "Zero exit load after the scheme-mandated lock or holding window"),
        ],
        "citation_url": "https://www.amfiindia.com/investor-corner/knowledge-center",
    },
    {
        "id": "nav",
        "field": "nav",
        "patterns": [
            re.compile(r"\b(?:what\s+is|explain|define|meaning\s+of)\s+(?:the\s+)?(?:net\s+asset\s+value|nav)\b", re.I),
            re.compile(r"\b(?:what\s+does\s+nav\s+(?:mean|stand\s+for))\b", re.I),
            re.compile(r"^nav\??$", re.I),
        ],
        "concept": "Net Asset Value (NAV)",
        "narrative": (
            "Net Asset Value (NAV) represents the per-unit market value of a mutual fund scheme. "
            "It is calculated by dividing total fund assets minus liabilities and expenses by the total outstanding units. "
            "In accordance with SEBI norms, AMCs compute and declare scheme NAVs on every business day by 11:00 PM IST."
        ),
        "table_rows": [
            ("Financial Term", "Net Asset Value (NAV)"),
            ("Formula", "(Total Assets - Liabilities & Accrued Expenses) / Outstanding Units"),
            ("Frequency", "Calculated and published daily after market close"),
            ("SEBI Mandate", "Mandatory upload to AMFI portal by 11:00 PM IST on business days"),
        ],
        "citation_url": "https://www.amfiindia.com/investor-corner/knowledge-center",
    },
    {
        "id": "sip",
        "field": "min_sip",
        "patterns": [
            re.compile(r"\b(?:what\s+is|explain|define|meaning\s+of)\s+(?:a\s+)?(?:the\s+)?(?:systematic\s+investment\s+plan|sip)\b", re.I),
            re.compile(r"\b(?:what\s+does\s+sip\s+(?:mean|stand\s+for))\b", re.I),
            re.compile(r"^sip\??$", re.I),
        ],
        "concept": "Systematic Investment Plan (SIP)",
        "narrative": (
            "A Systematic Investment Plan (SIP) allows investors to invest a fixed predetermined amount at regular intervals "
            "(such as monthly) into a mutual fund scheme. SIP fosters financial discipline and enables rupee-cost averaging, "
            "buying more units when prices are lower and fewer units when prices are higher."
        ),
        "table_rows": [
            ("Financial Term", "Systematic Investment Plan (SIP)"),
            ("Mechanism", "Periodic automated investments (monthly, quarterly)"),
            ("Core Benefit", "Rupee-cost averaging and compounding over long horizons"),
            ("Flexibility", "Pause, increase, or cancel anytime without penalty"),
        ],
        "citation_url": "https://www.amfiindia.com/investor-corner/knowledge-center",
    },
    {
        "id": "riskometer",
        "field": "riskometer",
        "patterns": [
            re.compile(r"\b(?:what\s+is|explain|define|meaning\s+of)\s+(?:a\s+)?(?:the\s+)?(?:sebi\s+)?riskometer\b", re.I),
            re.compile(r"\b(?:how\s+does\s+(?:the\s+)?riskometer\s+work)\b", re.I),
            re.compile(r"^riskometer\??$", re.I),
        ],
        "concept": "SEBI Riskometer",
        "narrative": (
            "The SEBI Riskometer is a standardized 6-level graphical meter used to depict the risk level of principal invested in a scheme. "
            "The tiers are Low, Low to Moderate, Moderate, Moderately High, High, and Very High Risk. "
            "Under SEBI regulations, riskometers are reviewed monthly based on portfolio asset credit quality, liquidity, and volatility."
        ),
        "table_rows": [
            ("Framework", "SEBI Product Labeling Riskometer"),
            ("Tiers", "1. Low, 2. Low-Moderate, 3. Moderate, 4. Mod-High, 5. High, 6. Very High"),
            ("Review Cycle", "Evaluated on a monthly basis across portfolio holdings"),
            ("Circular", "SEBI/HO/IMD/DF3/CIR/P/2020/197"),
        ],
        "citation_url": "https://www.sebi.gov.in/legal/circulars/oct-2020/product-labeling-in-mutual-fund-schemes-on-riskometer_47796.html",
    },
    {
        "id": "benchmark",
        "field": "benchmark",
        "patterns": [
            re.compile(r"\b(?:what\s+is|explain|define|meaning\s+of)\s+(?:a\s+)?(?:the\s+)?(?:mutual\s+fund\s+)?benchmark\b", re.I),
            re.compile(r"\b(?:what\s+does\s+benchmark\s+mean)\b", re.I),
            re.compile(r"^benchmark\??$", re.I),
        ],
        "concept": "Benchmark Index",
        "narrative": (
            "A mutual fund benchmark is an independent standard market index (such as Nifty 50, BSE 250 SmallCap, or Silver Spot Price) "
            "against which a fund's returns and portfolio performance are evaluated. "
            "SEBI mandates that all AMCs designate a primary benchmark index matching each scheme's investment category."
        ),
        "table_rows": [
            ("Financial Term", "Benchmark Index"),
            ("Role", "Standard reference yardstick to evaluate fund performance"),
            ("Selection", "Mandated by SEBI to align with fund asset mandate"),
            ("Example Indices", "Nifty 50 (Large Cap), BSE 250 SmallCap (Small Cap)"),
        ],
        "citation_url": "https://www.amfiindia.com/investor-corner/knowledge-center",
    },
    {
        "id": "lock_in",
        "field": "lock_in",
        "patterns": [
            re.compile(r"\b(?:what\s+is|explain|define|meaning\s+of)\s+(?:a\s+)?(?:the\s+)?lock[\s-]?in(?:\s+period)?\b", re.I),
            re.compile(r"\b(?:what\s+does\s+lock[\s-]?in\s+mean)\b", re.I),
            re.compile(r"^lock[\s-]?in(?:\s+period)?\??$", re.I),
        ],
        "concept": "Lock-in Period",
        "narrative": (
            "A lock-in period is a mandatory statutory duration during which mutual fund units cannot be redeemed, switched, or transferred. "
            "Under Section 80C, Equity Linked Savings Schemes (ELSS) carry a mandatory 3-year lock-in period from the date of allotment. "
            "Open-ended equity and debt funds have zero lock-in period."
        ),
        "table_rows": [
            ("Statutory Rule", "Lock-in Period"),
            ("ELSS Requirement", "Mandatory 3 years from allotment date (tax deduction under Section 80C)"),
            ("SIP Allotments", "Each monthly SIP tranche has its own separate 36-month lock-in window"),
            ("Non-ELSS Funds", "Zero statutory lock-in (subject only to exit loads)"),
        ],
        "citation_url": "https://www.amfiindia.com/investor-corner/knowledge-center",
    },
    {
        "id": "aum",
        "field": "aum",
        "patterns": [
            re.compile(r"\b(?:what\s+is|explain|define|meaning\s+of)\s+(?:the\s+)?(?:assets?\s+under\s+management|aum)\b", re.I),
            re.compile(r"\b(?:what\s+does\s+aum\s+(?:mean|stand\s+for))\b", re.I),
            re.compile(r"^aum\??$", re.I),
        ],
        "concept": "Assets Under Management (AUM)",
        "narrative": (
            "Assets Under Management (AUM) is the cumulative market value of all financial assets managed by a mutual fund scheme "
            "or fund house on behalf of investors. Scheme AUM changes daily based on portfolio market fluctuations and new investor "
            "inflows or redemptions."
        ),
        "table_rows": [
            ("Financial Term", "Assets Under Management (AUM)"),
            ("Definition", "Total market value of portfolio assets managed by the fund"),
            ("Fluctuation", "Changes daily based on market valuation and capital flows"),
            ("Disclosure", "Disclosed monthly by AMCs on factsheets and the AMFI portal"),
        ],
        "citation_url": "https://www.amfiindia.com/investor-corner/knowledge-center",
    },
]


def lookup_glossary(query: str) -> Optional[Dict[str, Any]]:
    """Checks if a query is asking for an educational concept definition.

    Returns:
        Structured response dictionary if matched, or None.
    """
    clean_q = query.strip()
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
                body = (
                    f"{item['narrative']}\n\n"
                    f"{stat_table}\n\n"
                    f"*Note: For scheme-specific numbers, ask about any of our 5 supported HDFC funds.*"
                )
                rendered = (
                    f"{body}\n\n"
                    f"Source: {item['citation_url']}\n"
                    f"Last updated from sources: {doc_date}"
                )

                return {
                    "text": body,
                    "citation_url": item["citation_url"],
                    "last_updated": doc_date,
                    "rendered": rendered,
                    "source": "glossary_store",
                    "glossary_id": item["id"],
                    "field": item["field"],
                    "scheme_id": None,
                }

    return None
