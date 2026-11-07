"""Procedural Knowledge Store for Mutual Fund & Groww Procedures.

Provides verified, SEBI-compliant procedural answers for:
- Downloading Capital Gains / Tax statements on Groww
- Redeeming mutual fund units on Groww
- Starting a Systematic Investment Plan (SIP) on Groww
- Completing Mutual Fund KYC verification
- Setting up an Autopay bank mandate for SIP
- SEBI NAV cut-off timings for same-day realization
- Switching from Regular to Direct plan
- Handling SIP date insufficient funds / bounce
- Pausing active SIP installments
- Updating registered bank account documentation
- Redemption payout settlement timeline (T+2)
- Tracking mutual fund order execution status
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from app.guardrails.refusal import get_default_corpus_date, normalize_date_footer
from app.guardrails.validator import validate_response


PROCEDURE_ITEMS: List[Dict[str, Any]] = [
    {
        "id": "capital_gains_statement",
        "supported": False,
        "status": "unsupported",
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
            "Under Mutual Funds, select 'Capital Gains (P&L) Statement', choose the relevant financial year, and download in Excel or PDF format."
        ),
        "table_rows": [
            ("Procedure", "Download Capital Gains Statement"),
            ("Platform", "Groww Web & Mobile App"),
            ("Navigation", "Profile → Reports → Mutual Funds → Capital Gains (P&L)"),
            ("Formats", "PDF & Excel (.xlsx)"),
        ],
        "source_url": "https://groww.in/help/reports",
        "citation_url": "https://groww.in/help/reports",
        "verified_on": "2026-11-05",
    },
    {
        "id": "redeem_mutual_fund",
        "supported": False,
        "status": "unsupported",
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
            "To redeem mutual fund units on Groww, open 'Holdings', select your scheme, and click 'Redeem'. "
            "Enter your withdrawal amount or units, authenticate with OTP/TPIN, and funds will credit directly to your verified primary bank account within T+2 business days."
        ),
        "table_rows": [
            ("Procedure", "Redeem Mutual Fund Units"),
            ("Platform", "Groww Web & Mobile App"),
            ("Navigation", "Dashboard / Holdings → Select Scheme → Redeem"),
            ("Settlement Timeline", "T+2 Business Days (direct to primary bank)"),
        ],
        "source_url": "https://groww.in/help/mutual-funds/order/redemption",
        "citation_url": "https://groww.in/help/mutual-funds/order/redemption",
        "verified_on": "2026-11-05",
    },
    {
        "id": "start_sip",
        "supported": False,
        "status": "unsupported",
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
            "Enter your monthly investment amount (minimum ₹100 for supported HDFC schemes), choose your monthly deduction date, and authenticate your payment."
        ),
        "table_rows": [
            ("Procedure", "Start Systematic Investment Plan (SIP)"),
            ("Platform", "Groww Web & Mobile App"),
            ("Minimum Amount", "₹100 (for all 5 supported HDFC schemes)"),
            ("Payment Modes", "UPI Auto-Pay, Net Banking Mandate, One-Time Mandate (OTM)"),
        ],
        "source_url": "https://groww.in/help/mutual-funds/sip",
        "citation_url": "https://groww.in/help/mutual-funds/sip",
        "verified_on": "2026-11-05",
    },
    {
        "id": "kyc_process",
        "supported": False,
        "status": "unsupported",
        "patterns": [
            re.compile(r"\b(?:how\s+to\s+complete|process\s+for|procedure\s+to\s+complete|(?:what\s+)?documents\s+(?:are\s+)?required\s+(?:for\s+)?)\s*kyc\b", re.I),
            re.compile(r"\b(?:mutual\s+fund\s+kyc|kyc\s+documents|kyc\s+process|kyc\s+verification|kyc\s+online|accepted\s+kyc)\b", re.I),
            re.compile(r"\bkyc\b.*?\b(?:documents?|proof|identity)\b", re.I),
        ],
        "procedure_title": "Mutual Fund KYC Verification",
        "platform": "Groww Web & Mobile App / KRA",
        "navigation": "Profile → Complete KYC → DigiLocker Verification",
        "narrative": (
            "Mutual Fund KYC is mandatory under SEBI regulations before making any mutual fund investment. "
            "To complete KYC online on Groww, submit your PAN, verify Aadhaar via DigiLocker OTP, and link an active bank account."
        ),
        "table_rows": [
            ("Procedure", "Mutual Fund KYC Verification"),
            ("Mandatory Documents", "PAN Card, Aadhaar (linked to mobile), Bank Proof"),
            ("Verification Method", "DigiLocker Online Aadhaar e-KYC"),
            ("Turnaround Time", "24 to 48 business hours via SEBI-registered KRAs"),
        ],
        "source_url": "https://groww.in/help/mutual-funds/kyc",
        "citation_url": "https://groww.in/help/mutual-funds/kyc",
        "verified_on": "2026-11-05",
    },
    {
        "id": "autopay_mandate",
        "supported": False,
        "status": "unsupported",
        "patterns": [
            re.compile(r"\b(?:autopay|auto[\s-]pay|bank\s+mandate|e[\s-]?nach|otm|one[\s-]time\s+mandate)\b", re.I),
            re.compile(r"\b(?:set\s+up|setup|create|enable)\s+(?:an?\s+)?(?:autopay|mandate|auto-debit)\b", re.I),
        ],
        "procedure_title": "Set Up SIP AutoPay / Bank Mandate",
        "platform": "Groww Web & Mobile App / NPCI e-NACH",
        "navigation": "Profile → Bank & AutoPay → Select Bank → Set Up AutoPay",
        "narrative": (
            "To set up an AutoPay bank mandate on Groww, go to 'Bank & AutoPay' under your profile and select your primary bank. "
            "Authorize the e-NACH or UPI mandate using Net Banking, Debit Card, or UPI PIN so recurring SIPs are debited automatically without manual intervention."
        ),
        "table_rows": [
            ("Procedure", "Set Up SIP AutoPay Mandate"),
            ("Authorization Options", "UPI AutoPay, Net Banking, or Debit Card (NPCI e-NACH)"),
            ("Mandate Cap", "Set as maximum debit limit; only exact SIP amount is deducted"),
            ("Approval Window", "Instant for UPI; 1 to 2 business days for Net Banking/Debit Card"),
        ],
        "source_url": "https://groww.in/help/mutual-funds/sip/autopay",
        "citation_url": "https://groww.in/help/mutual-funds/sip/autopay",
        "verified_on": "2026-11-05",
    },
    {
        "id": "cutoff_timings",
        "patterns": [
            re.compile(r"\b(?:cut[\s-]?off\s+times?|cut[\s-]?off\s+timings?|nav\s+cut[\s-]?off|same\s+day\s+nav)\b", re.I),
            re.compile(r"\bcut[\s-]?off\s+(?:for\s+)?(?:equity|same\s+day)\b", re.I),
            re.compile(r"\bcut[\s-]?off\s+time\b", re.I),
            re.compile(r"\bcut[\s-]?off\b.*?\b(?:equity|nav|funds?)\b", re.I),
        ],
        "procedure_title": "SEBI Official NAV Cut-Off Timings",
        "platform": "SEBI Regulatory Standard",
        "navigation": "SEBI Circular SEBI/HO/IMD/DF2/CIR/P/2020/175",
        "narrative": (
            "Under SEBI regulations, the official NAV cut-off time for equity and hybrid mutual funds is 3:00 PM IST on business days. "
            "Same-day NAV allotment is subject to funds being realized in the AMC's bank account before the 3:00 PM cut-off threshold."
        ),
        "table_rows": [
            ("Regulatory Standard", "SEBI Uniform NAV Cut-Off Timings"),
            ("Equity Purchase Cut-Off", "3:00 PM IST (subject to realization of funds)"),
            ("Equity Redemption Cut-Off", "3:00 PM IST (same-day closing NAV)"),
            ("Fund Realization Rule", "NAV is allotted based on when funds hit AMC account"),
        ],
        "source_url": "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=CutOffTimingsAndNewRuleOnApplicableNAV",
        "citation_url": "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=CutOffTimingsAndNewRuleOnApplicableNAV",
        "verified_on": "2026-11-05",
    },
    {
        "id": "switch_procedure",
        "supported": False,
        "status": "unsupported",
        "patterns": [
            re.compile(r"\b(?:switch|switch\s+units?|switch\s+from\s+regular\s+to\s+direct|convert\s+regular\s+to\s+direct)\b", re.I),
            re.compile(r"\bhow\s+(?:can|do)\s+i\s+switch\b", re.I),
        ],
        "procedure_title": "Switch from Regular to Direct Plan",
        "platform": "Groww Web & Mobile App / AMC Portal",
        "navigation": "Holdings → Select Regular Scheme → More Options → Switch to Direct",
        "narrative": (
            "To switch from a Regular plan to a Direct plan, select the scheme from your holdings and place a 'Switch' request to the Direct-Growth plan. "
            "A switch is treated under tax law as a redemption from the regular plan followed by a fresh purchase, so capital gains tax and exit loads may apply if redeemed within the exit window."
        ),
        "table_rows": [
            ("Procedure", "Switch from Regular to Direct Plan"),
            ("Platform", "Groww App or AMC / RTA Portal (CAMS/KFintech)"),
            ("Tax Implications", "Treated as redemption: Capital Gains Tax applies"),
            ("Exit Load", "Applicable if switched before the scheme holding window"),
        ],
        "source_url": "https://groww.in/switch",
        "citation_url": "https://groww.in/switch",
        "verified_on": "2026-11-05",
    },
    {
        "id": "sip_bounce",
        "supported": False,
        "status": "unsupported",
        "patterns": [
            re.compile(r"\b(?:insufficient\s+funds?|insufficient\s+balance|sip\s+(?:auto[\s-]?debit\s+)?bounces?|failed\s+sip|sip\s+failed)\b", re.I),
            re.compile(r"\bwhat\s+happens\s+if\s+.*?\s+(?:no\s+funds|no\s+balance|lacks\s+balance|bounces?|does\s+not\s+have\s+funds)\b", re.I),
            re.compile(r"\b(?:insufficient|does\s+not\s+have|without|no|lack\s+of)\s+(?:funds?|balance)\b", re.I),
            re.compile(r"\b(?:sip|auto[\s-]?debit)\b.*?\b(?:bounces?|fails?|failed|penalty|insufficient)\b", re.I),
        ],
        "procedure_title": "SIP Installment Insufficient Balance / Bounce Policy",
        "platform": "Groww & AMC Operational Standard",
        "navigation": "Groww FAQ / AMC Terms",
        "narrative": (
            "If your bank account lacks sufficient balance on your monthly SIP date, the auto-debit attempt fails and no mutual fund units are allotted. "
            "Neither Groww nor the AMC charges any penalty, but your bank may levy a ECS/e-NACH mandate bounce charge; three consecutive bounces automatically pause the SIP."
        ),
        "table_rows": [
            ("Event", "SIP Auto-Debit Failed (Insufficient Funds)"),
            ("AMC / Platform Penalty", "₹0 (Zero penalty charged by Groww or HDFC AMC)"),
            ("Bank Bounce Fee", "Applicable as per your personal bank's ECS/NACH policy"),
            ("Mandate Status", "Active (auto-paused only after 3 consecutive failed cycles)"),
        ],
        "source_url": "https://groww.in/help/mutual-funds/sip/missed-installment",
        "citation_url": "https://groww.in/help/mutual-funds/sip/missed-installment",
        "verified_on": "2026-11-05",
    },
    {
        "id": "sip_pause",
        "supported": False,
        "status": "unsupported",
        "patterns": [
            re.compile(r"\b(?:pause\s+(?:my\s+)?sip|stop\s+sip\s+temporarily|temporarily\s+stop\s+sip|pause\s+active\s+sip)\b", re.I),
            re.compile(r"\bhow\s+(?:do\s+i|to|can\s+i)\s+pause\b", re.I),
            re.compile(r"\bpause\s+(?:my\s+)?(?:active\s+)?sip\b", re.I),
            re.compile(r"\bhow\s+many\s+months\b.*?\b(?:pause|paused)\b", re.I),
            re.compile(r"\b(?:pause|paused)\b.*?\bsip\b", re.I),
            re.compile(r"\bsip\b.*?\b(?:pause|paused)\b", re.I),
            re.compile(r"\bpause\s+(?:active\s+)?sip\s+installment\b", re.I),
        ],
        "procedure_title": "Pause Active SIP Installments",
        "platform": "Groww Web & Mobile App",
        "navigation": "SIPs Tab → Select Active SIP → More Options → Pause SIP",
        "narrative": (
            "To pause an active SIP on Groww without canceling the mandate, go to your 'SIPs' dashboard, choose the active scheme, and tap 'Pause SIP'. "
            "Select the number of months to pause from 1 to 3 months (maximum 3 consecutive monthly installments) at least 2 business days prior to your next deduction date."
        ),
        "table_rows": [
            ("Procedure", "Pause SIP Without Cancellation"),
            ("Platform", "Groww Web & Mobile App"),
            ("Pause Duration", "1 to 3 months (maximum 3 consecutive monthly installments)"),
            ("Cut-Off Window", "Submit request at least 2 business days before next SIP date"),
        ],
        "source_url": "https://groww.in/help/mutual-funds/sip/pause",
        "citation_url": "https://groww.in/help/mutual-funds/sip/pause",
        "verified_on": "2026-11-05",
    },
    {
        "id": "bank_update",
        "supported": False,
        "status": "unsupported",
        "patterns": [
            re.compile(r"\b(?:update|change|modify)\s+(?:my\s+)?(?:bank|bank\s+account|account\s+details)\b", re.I),
            re.compile(r"\bdocuments\s+(?:needed|required)\s+(?:for|to)\s+(?:update|change)\s+bank\b", re.I),
            re.compile(r"\b(?:penny[\s-]?drop|bank\s+verification)\b", re.I),
        ],
        "procedure_title": "Update Registered Bank Account in Mutual Funds",
        "platform": "Groww Web & Mobile App / RTA Portal",
        "navigation": "Profile → Bank Details → Add New Bank → Set Primary",
        "narrative": (
            "To update your registered bank account for mutual fund folios, navigate to 'Bank Details' in your profile, add the new account, and upload proof. "
            "SEBI guidelines require automated Penny-drop bank verification or an original cancelled cheque bearing your printed name."
        ),
        "table_rows": [
            ("Procedure", "Change / Add Mutual Fund Bank Account"),
            ("Accepted Proofs", "Original cancelled cheque with printed name or attested bank statement"),
            ("Verification Mode", "Penny-drop verification followed by RTA folio update"),
            ("Turnaround Time", "24 to 48 hours for verification and primary bank change"),
        ],
        "source_url": "https://groww.in/help/account/bank-account",
        "citation_url": "https://groww.in/help/account/bank-account",
        "verified_on": "2026-11-05",
    },
    {
        "id": "settlement_cycle",
        "patterns": [
            re.compile(r"\b(?:settlement\s+cycle|settlement\s+timelines?|t\+[12]|redemption\s+settlement)\b", re.I),
            re.compile(r"\b(?:how\s+long|timeline|how\s+many\s+days|when\s+will\s+money\s+reach)\s+.*?\s+(?:redemption|redeem|bank|credit)\b", re.I),
            re.compile(r"\b(?:redemption\s+(?:timeline|payout|settlement|credit\s+time))\b", re.I),
            re.compile(r"\bsettlement\s+cycle\s+for\s+(?:equity|purchase)\b", re.I),
        ],
        "procedure_title": "Mutual Fund Redemption Settlement Timelines",
        "platform": "SEBI Regulatory Standard",
        "navigation": "SEBI Master Circular / AMFI Settlement Norms",
        "narrative": (
            "Under SEBI circular guidelines, redemption proceeds for equity mutual funds are credited to your bank account within T+2 business days. "
            "For Commodity Fund of Funds (such as HDFC Silver ETF FoF), proceeds are settled within T+3 business days directly to your verified bank."
        ),
        "table_rows": [
            ("Regulatory Standard", "SEBI Settlement Cycles"),
            ("Equity Purchase Settlement", "T+1 Business Day (units allotted upon fund realization)"),
            ("Equity Redemption Settlement", "T+2 Business Days (for example, Tuesday redemption credits by Thursday)"),
            ("Commodity FoF Settlement", "T+3 Business Days (Silver ETF FoF)"),
            ("Payout Destination", "Direct credit via NEFT/RTGS to verified primary bank"),
        ],
        "source_url": "https://www.sebi.gov.in/legal/circulars/nov-2022/timelines-for-transfer-of-dividend-and-redemption-proceeds-to-unitholders_65455.html",
        "citation_url": "https://www.sebi.gov.in/legal/circulars/nov-2022/timelines-for-transfer-of-dividend-and-redemption-proceeds-to-unitholders_65455.html",
        "verified_on": "2026-11-05",
    },
    {
        "id": "order_tracking",
        "supported": False,
        "status": "unsupported",
        "patterns": [
            re.compile(r"\b(?:track|check\s+status|order\s+status)\s+(?:of\s+)?(?:my\s+)?(?:redemption|sip|order|purchase)\b", re.I),
            re.compile(r"\bhow\s+(?:do\s+i|to)\s+track\s+(?:my\s+)?(?:order|redemption)\b", re.I),
            re.compile(r"\b(?:track|check|view|where)\b.*?\b(?:status|history|allotment)\b.*?\b(?:order|transaction|redemption)\b", re.I),
            re.compile(r"\b(?:view\s+(?:my\s+)?mutual\s+fund\s+transaction\s+history|transaction\s+history\s+on\s+groww)\b", re.I),
            re.compile(r"\btrack\s+(?:the\s+status\s+of\s+)?(?:my\s+)?(?:mutual\s+fund\s+)?redemption\s+order\b", re.I),
            re.compile(r"\btrack\s+(?:the\s+)?allotment\s+status\b", re.I),
        ],
        "procedure_title": "Track Mutual Fund Order Status",
        "platform": "Groww Web & Mobile App",
        "navigation": "Profile → All Orders → Mutual Funds → Select Order",
        "narrative": (
            "To track the status of your mutual fund order or redemption on Groww, navigate to 'All Orders' from your profile menu. "
            "Tap on the specific transaction to view live order progression from 'Order Placed', 'Sent to AMC/RTA', through 'Units Allotted' or 'Payout Credited'."
        ),
        "table_rows": [
            ("Procedure", "Track Mutual Fund Order Status"),
            ("Platform", "Groww Web & Mobile App"),
            ("Navigation", "Profile → All Orders → Mutual Funds"),
            ("Lifecycle Stages", "Order Placed → Sent to RTA → Completed (Allotted / Credited)"),
        ],
        "source_url": "https://groww.in/help/mutual-funds/order/track",
        "citation_url": "https://groww.in/help/mutual-funds/order/track",
        "verified_on": "2026-11-05",
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
            "Equity Linked Savings Schemes (ELSS) carry a mandatory statutory lock-in period of 3 years from the date of allotment under Section 80C. "
            "Investments up to ₹1.5 lakh qualify for tax deduction under Section 80C strictly under the Old Tax Regime (not available under the New Tax Regime). "
            "Our 5 supported HDFC schemes are open-ended equity and commodity funds with zero lock-in."
        ),
        "table_rows": [
            ("Category", "Equity Linked Savings Scheme (ELSS)"),
            ("Statutory Lock-in", "3 Years (36 Months from unit allotment date)"),
            ("Supported Schemes Lock-in", "None (All 5 supported HDFC schemes have 0 lock-in)"),
        ],
        "source_url": "https://groww.in/blog/3-steps-follow-elss-lock-period-ends",
        "citation_url": "https://groww.in/blog/3-steps-follow-elss-lock-period-ends",
        "verified_on": "2026-11-05",
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
            "Under SEBI circular guidelines, the standardized 6-tier Riskometer evaluates scheme risk monthly from Low to Very High Risk. "
            "A Very High Risk classification signifies that investors understand that their principal will be at very high risk due to equity or commodity volatility."
        ),
        "table_rows": [
            ("Regulatory Standard", "SEBI 6-Tier Scheme Riskometer"),
            ("Riskometer Levels", "Low, Low-to-Mod, Moderate, Mod-High, High, Very High"),
            ("Very High Risk Level", "Investors understand that their principal will be at very high risk"),
            ("Evaluation Frequency", "Monthly (published within 10 days of month-end)"),
        ],
        "source_url": "https://www.sebi.gov.in/legal/circulars/oct-2020/circular-on-product-labeling-in-mutual-fund-schemes-risk-o-meter_47796.html",
        "citation_url": "https://www.sebi.gov.in/legal/circulars/oct-2020/circular-on-product-labeling-in-mutual-fund-schemes-risk-o-meter_47796.html",
        "verified_on": "2026-11-05",
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
            "Under SEBI Circular SEBI/HO/IMD/DF3/CIR/P/2017/114, mutual funds are classified into 5 primary groups: Equity, Debt, Hybrid, Solution Oriented, and Other Schemes. "
            "The 10 equity subcategories include Multi Cap, Large Cap (top 100 companies), Mid Cap (101st-250th), Small Cap (251st onwards), and ELSS."
        ),
        "table_rows": [
            ("Regulatory Framework", "SEBI Scheme Categorization (Oct 2017 Circular)"),
            ("Primary Scheme Groups", "Equity, Debt, Hybrid, Solution Oriented, and Other Schemes"),
            ("Key Equity Categories", "Multi Cap, Large Cap, Mid Cap, Small Cap, Large & Mid Cap, ELSS"),
            ("Market Cap Definitions", "Large: 1-100; Mid: 101-250; Small: 251st company onwards"),
        ],
        "source_url": "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=CategorizationOfMutualFundSchemes",
        "citation_url": "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=CategorizationOfMutualFundSchemes",
        "verified_on": "2026-11-05",
    },
    {
        "id": "nav_disclosure",
        "patterns": [
            re.compile(r"\b(?:nav\s+disclosure|nav\s+timing|disclosure\s+timing|daily\s+nav\s+disclosure|11:00\s+pm)\b", re.I),
            re.compile(r"\b(?:good\s+practice\s+for\s+daily\s+nav\s+disclosure\s+timing|nav\s+disclosure\s+timing)\b", re.I),
        ],
        "procedure_title": "Daily NAV Disclosure Timelines",
        "platform": "SEBI / AMFI Regulatory Standard",
        "navigation": "SEBI Circular on NAV Disclosure / AMFI Guidelines",
        "narrative": (
            "Under SEBI regulatory guidelines, AMCs are required to calculate and disclose the daily Net Asset Value (NAV) of all mutual fund schemes on the AMFI portal and scheme website by 11:00 PM IST on business days. "
            "Timely daily disclosure ensures unitholders receive accurate valuation metrics before subsequent business day transaction cutoff deadlines."
        ),
        "table_rows": [
            ("Regulatory Standard", "SEBI / AMFI Daily NAV Disclosure Timing"),
            ("Daily Disclosure Deadline", "11:00 PM IST"),
            ("Official Portals", "AMFI (amfiindia.com) and AMC website (hdfcfund.com)"),
        ],
        "source_url": "https://www.amfiindia.com/uploads/Reviewoftimelimitfordisclosureof_NAV_f5ebc65062.pdf",
        "citation_url": "https://www.amfiindia.com/uploads/Reviewoftimelimitfordisclosureof_NAV_f5ebc65062.pdf",
        "verified_on": "2026-11-05",
    },
]

# Strict build-time validation of procedures
for item in PROCEDURE_ITEMS:
    if item.get("supported") is False or item.get("status") == "unsupported":
        continue
    if not item.get("source_url") or not str(item.get("source_url")).startswith("https://"):
        raise ValueError(f"Procedure item '{item.get('id')}' missing mandatory 'source_url'")
    if not item.get("verified_on") or not re.match(r"^\d{4}-\d{2}-\d{2}$", str(item.get("verified_on"))):
        raise ValueError(f"Procedure item '{item.get('id')}' missing mandatory 'verified_on'")


def lookup_procedure(query: str) -> Optional[Dict[str, Any]]:
    """Checks if a user query is asking for a standard investment or Groww procedure.

    Returns:
        Structured response dictionary validated against the contract, or None.
    """
    clean_q = query.strip()
    doc_date = get_default_corpus_date()

    for item in PROCEDURE_ITEMS:
        if item.get("supported") is False or item.get("status") == "unsupported":
            continue
        for p in item["patterns"]:
            if p.search(clean_q):
                # Build Option C Stat Card Table
                table_lines = [
                    "| Metric | Detail |",
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
                    "source": "procedural_store",
                    "procedure_id": item["id"],
                    "field": "procedure",
                    "scheme_id": None,
                }

    return None
