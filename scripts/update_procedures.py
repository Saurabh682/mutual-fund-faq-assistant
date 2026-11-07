import re

with open("backend/app/rag/procedures.py", "r", encoding="utf-8") as f:
    text = f.read()

# 1. Update sebi_categorization narrative & URLs
old_cat_url = 'https://www.sebi.gov.in/legal/circulars/oct-2017/categorization-and-rationalization-of-mutual-fund-schemes_36199.html'
new_cat_url = 'https://www.amfiindia.com/investor/knowledge-center-info?zoneName=CategorizationOfMutualFundSchemes'
text = text.replace(old_cat_url, new_cat_url)

old_cat_narrative = (
    'SEBI categorizes equity mutual funds strictly by market capitalization: Large Cap (top 100 stocks), Mid Cap (101st to 250th), and Small Cap (251st onwards). '
    'Multi Cap schemes must maintain at least 25% allocation in each of Large Cap, Mid Cap, and Small Cap segments at all times.'
)
new_cat_narrative = (
    'SEBI categorizes mutual fund schemes into five primary groups: Equity, Debt, Hybrid, Solution Oriented, and Other Schemes. '
    'Equity schemes include Multi Cap, Large Cap (top 100 stocks), Large & Mid Cap, Mid Cap (101st-250th), Small Cap (251st onwards), and ELSS.'
)
text = text.replace(old_cat_narrative, new_cat_narrative)

# 2. Update cutoff_timings URL
old_cutoff_url = 'https://groww.in/blog/sebi-revises-mutual-fund-cut-off-timings'
new_cutoff_url = 'https://www.amfiindia.com/investor/knowledge-center-info?zoneName=CutOffTimingsAndNewRuleOnApplicableNAV'
# Only replace in cutoff_timings block
text = re.sub(
    r'("id":\s*"cutoff_timings"[\s\S]*?"source_url":\s*)"https://groww\.in/blog/sebi-revises-mutual-fund-cut-off-timings"',
    r'\1"https://www.amfiindia.com/investor/knowledge-center-info?zoneName=CutOffTimingsAndNewRuleOnApplicableNAV"',
    text
)
text = re.sub(
    r'("id":\s*"cutoff_timings"[\s\S]*?"citation_url":\s*)"https://groww\.in/blog/sebi-revises-mutual-fund-cut-off-timings"',
    r'\1"https://www.amfiindia.com/investor/knowledge-center-info?zoneName=CutOffTimingsAndNewRuleOnApplicableNAV"',
    text
)

# 3. Update nav_disclosure URL
text = re.sub(
    r'("id":\s*"nav_disclosure"[\s\S]*?"source_url":\s*)"https://groww\.in/blog/sebi-revises-mutual-fund-cut-off-timings"',
    r'\1"https://www.amfiindia.com/uploads/Reviewoftimelimitfordisclosureof_NAV_f5ebc65062.pdf"',
    text
)
text = re.sub(
    r'("id":\s*"nav_disclosure"[\s\S]*?"citation_url":\s*)"https://groww\.in/blog/sebi-revises-mutual-fund-cut-off-timings"',
    r'\1"https://www.amfiindia.com/uploads/Reviewoftimelimitfordisclosureof_NAV_f5ebc65062.pdf"',
    text
)

# 4. Update sebi_riskometer URL
text = re.sub(
    r'("id":\s*"sebi_riskometer"[\s\S]*?"source_url":\s*)"https://groww\.in/p/riskometer"',
    r'\1"https://www.sebi.gov.in/legal/circulars/oct-2020/circular-on-product-labeling-in-mutual-fund-schemes-risk-o-meter_47796.html"',
    text
)
text = re.sub(
    r'("id":\s*"sebi_riskometer"[\s\S]*?"citation_url":\s*)"https://groww\.in/p/riskometer"',
    r'\1"https://www.sebi.gov.in/legal/circulars/oct-2020/circular-on-product-labeling-in-mutual-fund-schemes-risk-o-meter_47796.html"',
    text
)

# 5. Update settlement_cycle URL
text = re.sub(
    r'("id":\s*"settlement_cycle"[\s\S]*?"source_url":\s*)"https://groww\.in/help/mutual-funds/order/redemption"',
    r'\1"https://www.sebi.gov.in/legal/circulars/nov-2022/timelines-for-transfer-of-dividend-and-redemption-proceeds-to-unitholders_65455.html"',
    text
)
text = re.sub(
    r'("id":\s*"settlement_cycle"[\s\S]*?"citation_url":\s*)"https://groww\.in/help/mutual-funds/order/redemption"',
    r'\1"https://www.sebi.gov.in/legal/circulars/nov-2022/timelines-for-transfer-of-dividend-and-redemption-proceeds-to-unitholders_65455.html"',
    text
)

# 6. Mark unsupported Groww help items
unsupported_ids = [
    "capital_gains_statement",
    "redeem_mutual_fund",
    "start_sip",
    "kyc_process",
    "autopay_mandate",
    "switch_procedure",
    "sip_bounce",
    "sip_pause",
    "bank_update",
    "order_tracking",
]

for uid in unsupported_ids:
    text = re.sub(
        rf'({{\s*"id":\s*"{uid}",)',
        r'\1\n        "supported": False,\n        "status": "unsupported",',
        text
    )

# 7. Update lookup_procedure to stop serving unsupported entries
old_lookup_loop = 'for item in PROCEDURE_ITEMS:'
new_lookup_loop = (
    'for item in PROCEDURE_ITEMS:\n'
    '        if item.get("supported") is False or item.get("status") == "unsupported":\n'
    '            continue'
)
text = text.replace(old_lookup_loop, new_lookup_loop)

with open("backend/app/rag/procedures.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Successfully updated procedures.py")
