import re
from bs4 import BeautifulSoup

def parse_groww_scheme(raw_data: dict) -> dict:
    next_data = raw_data.get("next_data", {})
    html_content = raw_data.get("html", "")
    url = raw_data.get("url", "")
    scheme_id = raw_data.get("scheme_id", "")
    fetched_at = raw_data.get("fetched_at", "")

    soup = BeautifulSoup(html_content, "html.parser")

    # 1. Primary Fields from next_data
    scheme_name = next_data.get("scheme_name") or soup.title.string if soup.title else "HDFC Scheme"
    scheme_type = next_data.get("scheme_type", "Growth")
    category = next_data.get("category", "Equity")
    sub_category = next_data.get("sub_category", "")

    # Expense ratio
    ter_raw = next_data.get("expense_ratio")
    ter = f"{ter_raw}%" if ter_raw is not None else ""

    # Exit load
    exit_load = next_data.get("exit_load", "")

    # Investment minimums
    min_sip = next_data.get("min_sip_investment")
    min_lumpsum = next_data.get("min_investment_amount")
    min_additional = next_data.get("mini_additional_investment")

    # Benchmark
    benchmark = next_data.get("benchmark_name") or next_data.get("benchmark", "")

    # Lock-in
    lock_in_data = next_data.get("lock_in")
    lock_in = "None"
    if lock_in_data and isinstance(lock_in_data, dict):
        years = lock_in_data.get("years")
        if years:
            lock_in = f"{years} Years"

    # Riskometer
    riskometer = "Very High Risk"
    # Search DOM for Riskometer label
    for span in soup.find_all(["span", "div"]):
        txt = span.get_text(strip=True)
        if re.search(r"\b(Very High|High|Moderately High|Moderate|Moderately Low|Low)\s+Risk\b", txt, re.I):
            m = re.search(r"\b(Very High|High|Moderately High|Moderate|Moderately Low|Low)\s+Risk\b", txt, re.I)
            if m:
                riskometer = m.group(0).title()
                break

    # NAV & AUM
    nav = str(next_data.get("nav", ""))
    nav_date = next_data.get("nav_date", fetched_at)
    aum = str(next_data.get("aum", ""))

    # Fund Manager & House
    fund_manager = next_data.get("fund_manager", "HDFC Asset Management Company")
    fund_house = next_data.get("fund_house", "HDFC Mutual Fund")

    # Tax impact
    tax_impact = ""
    cat_info = next_data.get("category_info", {})
    if isinstance(cat_info, dict):
        tax_impact = cat_info.get("tax_impact", "")

    # 2. Extract FAQs from DOM
    faqs = []
    for h3 in soup.find_all(["h3", "h4"]):
        q_text = h3.get_text(strip=True)
        if "?" in q_text and len(q_text) < 150:
            parent_div = h3.find_parent("div")
            if parent_div:
                ans_text = parent_div.get_text(separator=" ", strip=True)
                ans_clean = ans_text.replace(q_text, "").strip()
                if 20 < len(ans_clean) < 600:
                    faqs.append({"question": q_text, "answer": ans_clean})

    # Assemble structured sections for RAG chunking
    sections = [
        {
            "section": "Key Scheme Details & Metadata",
            "content": f"Scheme Name: {scheme_name}. Category: {category} ({sub_category}). Plan: Direct. Option: Growth. Fund House: {fund_house}. Fund Manager: {fund_manager}. Benchmark Index: {benchmark}. Riskometer Level: {riskometer}."
        },
        {
            "section": "Expense Ratio & Charges",
            "content": f"The Total Expense Ratio (TER) of {scheme_name} (Direct Plan) is {ter}. This is the annual fee charged by the fund house to manage the investment portfolio."
        },
        {
            "section": "Exit Load & Redemption Terms",
            "content": f"Exit Load Structure for {scheme_name}: {exit_load} No exit load is charged after the completion of the designated tenure. The exit load applies equally to SIP and lumpsum redemption units."
        },
        {
            "section": "Investment Minimums & SIP Limits",
            "content": f"Minimum SIP Investment for {scheme_name}: ₹{min_sip} per installment. Minimum initial investment / lumpsum: ₹{min_lumpsum}. Minimum additional purchase: ₹{min_additional}."
        },
        {
            "section": "Lock-in Period & Taxation",
            "content": f"Lock-in Period for {scheme_name}: {lock_in}. Tax Implications: {tax_impact if tax_impact else 'Short Term Capital Gains (STCG) taxed at 20% if redeemed within 1 year; Long Term Capital Gains (LTCG) exceeding ₹1.25 Lakh taxed at 12.5%.'}"
        },
        {
            "section": "Riskometer & Benchmark Index",
            "content": f"Riskometer Classification for {scheme_name}: {riskometer}. The underlying benchmark against which fund performance is evaluated is {benchmark}."
        }
    ]

    # Add FAQ sections
    for i, faq in enumerate(faqs[:5]):
        sections.append({
            "section": f"FAQ: {faq['question']}",
            "content": f"Question: {faq['question']} Answer: {faq['answer']}"
        })

    return {
        "scheme_id": scheme_id,
        "scheme_name": scheme_name,
        "category": category,
        "sub_category": sub_category,
        "url": url,
        "doc_date": nav_date or fetched_at,
        "canonical_facts": {
            "ter_direct": ter,
            "exit_load": exit_load,
            "min_sip": f"₹{min_sip}",
            "min_lumpsum": f"₹{min_lumpsum}",
            "min_additional": f"₹{min_additional}",
            "lock_in": lock_in,
            "riskometer": riskometer,
            "benchmark": benchmark,
            "nav": f"₹{nav}" if nav else "",
            "aum": f"₹{aum} Cr" if aum else ""
        },
        "sections": sections
    }
