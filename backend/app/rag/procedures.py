"""Procedural Knowledge Store for Mutual Fund & Groww Procedures.

Provides verified, SEBI-compliant procedural answers for:
- Downloading Capital Gains / Tax statements on Groww
- Redeeming mutual fund units on Groww
- Starting a Systematic Investment Plan (SIP) on Groww
- Completing Mutual Fund KYC verification
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional
from app.guardrails.refusal import get_default_corpus_date, normalize_date_footer


PROCEDURE_ITEMS = [
    {
        "id": "capital_gains_statement",
        "patterns": [
            re.compile(r"\bcapital\s+gains?\s+(?:statement|report|tax\s+statement|p&l)\b", re.I),
            re.compile(r"\bdownload\s+(?:my\s+)?(?:capital\s+gains?|tax\s+statement|p&l)\b", re.I),
            re.compile(r"\b(?:where|how)\s+(?:to|can\s+i|do\s+i)\s+(?:download|get|find)\s+(?:my\s+)?(?:capital\s+gains?|tax\s+statement|p&l)\b", re.I),
            re.compile(r"\bcapital\s+gains?\b.*\b(?:groww|statement|download)\b", re.I),
        ],
        "procedure_title": "Download Capital Gains Statement",
        "platform": "Groww Web & Mobile App",
        "navigation": "Profile → Reports → Mutual Funds → Capital Gains (P&L)",
        "narrative": (
            "To download your Capital Gains statement on Groww, tap your profile avatar and navigate to 'Reports'. "
            "Under Mutual Funds, select 'Capital Gains (P&L) Statement', choose the relevant financial year, "
            "and download your statement in Excel or PDF format."
        ),
        "table_rows": [
            ("Procedure", "Download Capital Gains Statement"),
            ("Platform", "Groww Web & Mobile App"),
            ("Navigation", "Profile → Reports → Mutual Funds → Capital Gains (P&L)"),
            ("Formats", "PDF & Excel (.xlsx)"),
            ("Delivery", "Instant download or sent to registered email"),
        ],
        "citation_url": "https://groww.in/help/reports",
    },
    {
        "id": "redeem_mutual_fund",
        "patterns": [
            re.compile(r"\bhow\s+(?:to|can\s+i|do\s+i)\s+redeem\s+(?:my\s+)?(?:mutual\s+fund|mf|units|holdings|investment)\b", re.I),
            re.compile(r"\bredeem\s+(?:my\s+)?(?:mutual\s+fund|units)\s+on\s+groww\b", re.I),
            re.compile(r"\bhow\s+(?:do\s+i|to)\s+sell\s+(?:my\s+)?(?:mutual\s+funds?|units)\s+on\s+groww\b", re.I),
            re.compile(r"\bprocess\s+to\s+redeem\b", re.I),
        ],
        "procedure_title": "Redeem Mutual Fund Units",
        "platform": "Groww Web & Mobile App",
        "navigation": "Dashboard / Holdings → Select Scheme → Redeem",
        "narrative": (
            "To redeem mutual fund units on Groww, open your 'Holdings' or 'Dashboard' and select your mutual fund scheme. "
            "Click on 'Redeem', specify your withdrawal amount or units (or select 'Redeem All'), and confirm with your OTP/TPIN. "
            "Payout proceeds are credited to your verified primary bank account within T+2 to T+3 business days."
        ),
        "table_rows": [
            ("Procedure", "Redeem Mutual Fund Units"),
            ("Platform", "Groww Web & Mobile App"),
            ("Navigation", "Dashboard / Holdings → Select Scheme → Redeem"),
            ("Redemption Options", "Partial amount, specific units, or 'Redeem All'"),
            ("Settlement Timeline", "T+2 to T+3 Business Days (direct to primary bank)"),
        ],
        "citation_url": "https://groww.in/help/mutual-funds/order/redemption",
    },
    {
        "id": "start_sip",
        "patterns": [
            re.compile(r"\bhow\s+(?:to|can\s+i|do\s+i)\s+start\s+(?:a\s+)?sip\b", re.I),
            re.compile(r"\bstart\s+(?:a\s+)?sip\s+on\s+groww\b", re.I),
            re.compile(r"\bprocess\s+(?:to|for)\s+starting\s+(?:a\s+)?sip\b", re.I),
        ],
        "procedure_title": "Start Systematic Investment Plan (SIP)",
        "platform": "Groww Web & Mobile App",
        "navigation": "Scheme Page → Start SIP → Select Amount & Date → Pay",
        "narrative": (
            "To start an SIP on Groww, search for your chosen mutual fund scheme and click 'Start SIP'. "
            "Enter your monthly investment amount (minimum ₹100 for supported HDFC schemes), pick your monthly SIP deduction date, "
            "and complete initial authentication via UPI, Net Banking, or Auto-Pay mandate."
        ),
        "table_rows": [
            ("Procedure", "Start Systematic Investment Plan (SIP)"),
            ("Platform", "Groww Web & Mobile App"),
            ("Navigation", "Scheme Page → Start SIP → Select Amount & Date → Pay"),
            ("Minimum Amount", "₹100 (for all 5 supported HDFC schemes)"),
            ("Payment Modes", "UPI Auto-Pay, Net Banking Mandate, One-Time Mandate (OTM)"),
        ],
        "citation_url": "https://groww.in/help/mutual-funds/sip",
    },
    {
        "id": "kyc_process",
        "patterns": [
            re.compile(r"\b(?:how\s+to\s+complete|process\s+for|documents\s+required\s+(?:for\s+)?)\s*kyc\b", re.I),
            re.compile(r"\b(?:mutual\s+fund\s+kyc|kyc\s+documents|kyc\s+process|kyc\s+verification|kyc)\b", re.I),
        ],
        "procedure_title": "Mutual Fund KYC Verification",
        "platform": "Groww Web & Mobile App / KRA",
        "navigation": "Profile → Complete KYC → DigiLocker Verification",
        "narrative": (
            "Mutual Fund KYC is mandatory under SEBI regulations before making any mutual fund investment. "
            "To complete KYC on Groww, provide your PAN details, verify Aadhaar via DigiLocker OTP, and link an active bank account. "
            "Verification is processed through SEBI-registered KRAs within 24 to 48 business hours."
        ),
        "table_rows": [
            ("Procedure", "Mutual Fund KYC Verification"),
            ("Mandatory Documents", "PAN Card, Aadhaar (linked to mobile), Bank Proof"),
            ("Verification Method", "DigiLocker Online Aadhaar e-KYC"),
            ("Regulatory Authority", "SEBI Registered KRAs (CVL, CAMS, KFintech, NDML)"),
        ],
        "citation_url": "https://www.amfiindia.com/investor-corner/knowledge-center/kyc",
    },
    {
        "id": "elss_lock_in",
        "patterns": [
            re.compile(r"\b(?:what\s+is\s+(?:the\s+)?lock[\s-]?in\s+(?:period\s+)?(?:for\s+)?elss|elss\s+lock[\s-]?in|lock[\s-]?in\s+period\s+for\s+elss)\b", re.I),
            re.compile(r"\b(?:tax\s+saving\s+mutual\s+funds?|elss\s+mutual\s+funds?)\s+lock[\s-]?in\b", re.I),
            re.compile(r"\b(?:lock[\s-]?in\s+period\s+for\s+mutual\s+funds?|do\s+mutual\s+funds\s+have\s+lock[\s-]?in)\b", re.I),
        ],
        "procedure_title": "ELSS Mutual Fund Lock-in Period & Tax Rules",
        "platform": "Official Regulatory Standard",
        "navigation": "SEBI Guidelines / Section 80C of Income Tax Act",
        "narrative": (
            "Equity Linked Savings Schemes (ELSS) have a mandatory statutory lock-in period of 3 years from the date of allotment, "
            "which is the shortest lock-in among all Section 80C tax-saving options. "
            "For SIPs in ELSS, each monthly installment has an independent 3-year lock-in period. "
            "Our 5 supported HDFC schemes are open-ended equity and commodity funds with zero lock-in."
        ),
        "table_rows": [
            ("Category", "Equity Linked Savings Scheme (ELSS)"),
            ("Statutory Lock-in", "3 Years (36 Months from unit allotment date)"),
            ("SIP Installment Rule", "Each individual SIP installment is locked for 3 years"),
            ("Supported Schemes Lock-in", "None (All 5 supported HDFC schemes have 0 lock-in)"),
            ("Regulatory Framework", "SEBI Regulations & Section 80C, Income Tax Act"),
        ],
        "citation_url": "https://www.amfiindia.com/investor-corner/knowledge-center",
    },
    {
        "id": "sebi_riskometer",
        "patterns": [
            re.compile(r"\b(?:sebi\s+riskometer|riskometer\s+(?:tiers?|framework|levels?|guidelines?)|how\s+does\s+riskometer\s+work)\b", re.I),
            re.compile(r"\b(?:explain\s+riskometer|mutual\s+fund\s+riskometer\s+tiers?)\b", re.I),
        ],
        "procedure_title": "SEBI 6-Tier Mutual Fund Riskometer Framework",
        "platform": "SEBI Official Regulatory Standard",
        "navigation": "SEBI Circular SEBI/HO/IMD/DF3/CIR/P/2020/197",
        "narrative": (
            "SEBI mandates a standardized 6-tier Riskometer for all mutual fund schemes: Low, Low to Moderate, Moderate, "
            "Moderately High, High, and Very High. "
            "Asset Management Companies (AMCs) evaluate scheme risk monthly based on portfolio credit risk, interest rate risk, and liquidity risk. "
            "Updated Riskometers must be published by AMCs and AMFI within 10 days of each calendar month-end."
        ),
        "table_rows": [
            ("Regulatory Standard", "SEBI 6-Tier Scheme Riskometer"),
            ("Riskometer Levels", "Low, Low-to-Mod, Moderate, Mod-High, High, Very High"),
            ("Evaluation Frequency", "Monthly (published within 10 days of month-end)"),
            ("Governing Circular", "SEBI/HO/IMD/DF3/CIR/P/2020/197"),
            ("Official Portal", "AMFI India & HDFC AMC Portals"),
        ],
        "citation_url": "https://www.sebi.gov.in/legal/circulars/oct-2020/product-labeling-in-mutual-fund-schemes-on-riskometer_47796.html",
    },
    {
        "id": "sebi_categorization",
        "patterns": [
            re.compile(r"\b(?:sebi\s+categorization|mutual\s+fund\s+categories|market\s+cap\s+definition|sebi\s+scheme\s+categorization)\b", re.I),
            re.compile(r"\b(?:definition\s+of\s+(?:large|mid|small)\s+cap|how\s+are\s+mutual\s+funds\s+categorized)\b", re.I),
        ],
        "procedure_title": "SEBI Mutual Fund Categorization Framework",
        "platform": "SEBI Official Regulatory Standard",
        "navigation": "SEBI Circular SEBI/HO/IMD/DF3/CIR/P/2017/114",
        "narrative": (
            "SEBI circular SEBI/HO/IMD/DF3/CIR/P/2017/114 defines equity mutual fund categories strictly by market capitalization: "
            "Large Cap (1st to 100th company, min 80%), Mid Cap (101st to 250th company, min 65%), and Small Cap (251st company onwards, min 65%). "
            "Multi Cap funds are required to maintain a minimum 25% allocation each in Large Cap, Mid Cap, and Small Cap companies at all times."
        ),
        "table_rows": [
            ("Framework", "SEBI Scheme Categorization & Rationalization"),
            ("Large Cap Mandate", "Top 100 companies by market cap (min 80% allocation)"),
            ("Mid Cap Mandate", "101st to 250th companies (min 65% allocation)"),
            ("Small Cap Mandate", "251st company onwards (min 65% allocation)"),
            ("Multi Cap Mandate", "Min 25% Large, 25% Mid, 25% Small Cap at all times"),
        ],
        "citation_url": "https://www.sebi.gov.in/legal/circulars/oct-2017/categorization-and-rationalization-of-mutual-fund-schemes_36199.html",
    },
]


def lookup_procedure(query: str) -> Optional[Dict[str, Any]]:
    """Checks if a user query is asking for a standard investment or Groww procedure.

    Returns:
        Structured response dictionary if matched, or None.
    """
    clean_q = query.strip()
    doc_date = get_default_corpus_date()

    for item in PROCEDURE_ITEMS:
        for p in item["patterns"]:
            if p.search(clean_q):
                # Build Option C Stat Card Table
                table_lines = [
                    "| Metric | Detail |",
                    "| :--- | :--- |",
                ]
                for k, v in item["table_rows"]:
                    table_lines.append(f"| **{k}** | **{v}** |")

                stat_table = "\n".join(table_lines)
                body = f"{item['narrative']}\n\n{stat_table}"
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
                    "source": "procedural_store",
                    "procedure_id": item["id"],
                    "field": "procedure",
                    "scheme_id": None,
                }

    return None
