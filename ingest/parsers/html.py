import re
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from ingest.manifest import fund_house_of, load_schemes

# Stored when the Groww page has no value, so a missing fact is visible instead of a made-up one
NOT_LISTED = "Not listed on the Groww page"

def normalize_date_to_iso(date_str: str) -> str:
    """Converts varying date strings (e.g. '23-Oct-2026', '05-Nov-2026') into strict ISO YYYY-MM-DD format."""
    if not date_str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    date_str = date_str.strip()
    for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%d/%m/%Y", "%b %d, %Y", "%d %b %Y"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str

def extract_active_fund_managers(soup: BeautifulSoup, scheme_id: str = "", default_name: str = "") -> str:
    """Extracts only currently active fund managers from the HTML DOM, filtering out stale/past managers."""
    active_managers = []
    cards = soup.find_all(class_=lambda c: c and "fundManagement_card" in c)
    for card in cards:
        text = card.get_text(separator=" ", strip=True)
        if re.search(r"-\s*Present", text, re.I):
            name_el = card.find(class_=lambda c: c and "personName" in c)
            if name_el:
                name = name_el.get_text(strip=True)
                if name and name not in active_managers:
                    active_managers.append(name)

    # Discard Prashant Jain if present in any legacy field/card (stepped down July 2022)
    clean_mgrs = [m for m in active_managers if "Prashant Jain" not in m]

    # Lead manager(s) a human verified for this scheme (pinned_fund_manager in the manifest)
    pinned = load_schemes().get(scheme_id, {}).get("pinned_fund_manager")
    if pinned:
        return pinned

    if clean_mgrs:
        return ", ".join(clean_mgrs)

    # Fallback to default if clean
    if default_name and "Prashant Jain" not in default_name:
        return default_name

    return NOT_LISTED

# Longest label first so "High Risk" never shadows "Very High Risk" or "Moderately High Risk"
RISK_PATTERN = re.compile(r"\b(Very High|Moderately High|Moderately Low|Moderate|High|Low)\s+Risk\b", re.I)


def _risk_label(next_data: dict, soup: BeautifulSoup) -> str:
    """The risk label the Groww page shows beside the scheme name, or "" if it cannot be found.

    Primary source is the scheme's own row of return_stats. nfo_risk is the label at launch and goes stale.
    There is deliberately no default: a wrong label is worse than a missing one.
    """
    stats = next_data.get("return_stats")
    label = stats[0].get("risk") if isinstance(stats, list) and stats and isinstance(stats[0], dict) else None
    if label:
        return f"{str(label).strip()} Risk"

    found = None
    for el in soup.find_all(class_=re.compile(r"(?:pill|badge|riskometer)", re.I)):
        txt = el.get_text(separator=" ", strip=True)
        m = RISK_PATTERN.search(txt)
        if m:
            found = m.group(0).title()
            if len(txt) <= 30:
                break
    if found:
        return found

    # Leaf text only (<= 35 chars), so a whole navigation menu cannot match
    for tag in soup.find_all(["span", "div", "p"]):
        if tag.find_all(["span", "div", "p"]):
            continue
        txt = tag.get_text(separator=" ", strip=True)
        if len(txt) <= 35:
            m = RISK_PATTERN.search(txt)
            if m:
                return m.group(0).title()
    return ""


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

    def rupees(value) -> str:
        return f"₹{value}" if value not in (None, "") else NOT_LISTED

    # Expense ratio
    ter_raw = next_data.get("expense_ratio")
    ter = f"{ter_raw}%" if ter_raw not in (None, "") else NOT_LISTED

    # Exit load
    exit_load = next_data.get("exit_load") or NOT_LISTED

    # Investment minimums
    min_sip = next_data.get("min_sip_investment")
    min_lumpsum = next_data.get("min_investment_amount")
    min_additional = next_data.get("mini_additional_investment")

    # Benchmark
    benchmark = (next_data.get("benchmark_name") or next_data.get("benchmark") or NOT_LISTED).strip()

    # Lock-in
    lock_in_data = next_data.get("lock_in")
    lock_in = "None"
    if lock_in_data and isinstance(lock_in_data, dict):
        for unit, label in (("years", "Years"), ("months", "Months"), ("days", "Days")):
            if lock_in_data.get(unit):
                lock_in = f"{lock_in_data[unit]} {label}"
                break

    riskometer = _risk_label(next_data, soup) or NOT_LISTED

    # NAV & AUM
    nav_raw = next_data.get("nav")
    nav_date = next_data.get("nav_date", fetched_at)
    iso_date = normalize_date_to_iso(nav_date or fetched_at)
    aum_raw = next_data.get("aum")

    # Fund Manager & House (Extracted from active DOM cards, filtering out stale managers like Prashant Jain)
    house = fund_house_of(scheme_id)
    fund_manager = extract_active_fund_managers(soup, scheme_id, next_data.get("fund_manager", ""))
    fund_house = next_data.get("fund_house") or house.get("name", "")
    isin = next_data.get("isin", "")
    stamp_duty = next_data.get("stamp_duty", "0.005% (from July 1st, 2020)")

    # Manager details & RTA
    mgr_details_list = next_data.get("fund_manager_details", [])
    mgr_edu = ""
    mgr_exp = ""
    if mgr_details_list and isinstance(mgr_details_list, list):
        primary_mgr = mgr_details_list[0]
        mgr_edu = primary_mgr.get("education", "")
        mgr_exp = primary_mgr.get("experience", "")

    rta_info = next_data.get("rta_details", {})
    rta_name = rta_info.get("rta_name", "") if isinstance(rta_info, dict) else ""
    rta_email = rta_info.get("email", "") if isinstance(rta_info, dict) else ""
    rta_text = f"Registrar and Transfer Agent (RTA): {rta_name} ({rta_email}). " if rta_name else ""

    # Tax impact
    tax_impact = ""
    cat_info = next_data.get("category_info", {})
    if isinstance(cat_info, dict):
        tax_impact = cat_info.get("tax_impact", "")

    # 2. Extract FAQs from DOM
    faqs = []
    seen_questions = set()
    for h3 in soup.find_all(["h3", "h4"]):
        q_text = h3.get_text(strip=True)
        if "?" in q_text and len(q_text) < 150 and q_text not in seen_questions:
            ans_div = h3.parent.find_next_sibling("div") if h3.parent else None
            if not ans_div and h3.find_next_sibling("div"):
                ans_div = h3.find_next_sibling("div")
            if ans_div:
                ans_clean = ans_div.get_text(separator=" ", strip=True)
                if len(ans_clean) > 20:
                    seen_questions.add(q_text)
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
            "content": f"Minimum SIP Investment for {scheme_name}: {rupees(min_sip)}{' per installment' if min_sip not in (None, '') else ''}. Minimum initial investment / lumpsum: {rupees(min_lumpsum)}. Minimum additional purchase: {rupees(min_additional)}."
        },
        {
            "section": "Lock-in Period & Taxation",
            "content": f"Lock-in Period for {scheme_name}: {lock_in}." + (f" Tax Implications: {tax_impact}" if tax_impact else "")
        },
        {
            "section": "Riskometer & Benchmark Index",
            "content": f"Riskometer Classification for {scheme_name}: {riskometer}. The underlying benchmark against which fund performance is evaluated is {benchmark}."
        },
        {
            "section": "Fund Management & Operations",
            "content": f"Fund Manager: {fund_manager}. {mgr_edu} {mgr_exp[:200] if mgr_exp else ''} {rta_text}ISIN: {isin}. Stamp Duty: {stamp_duty}."
        }
    ]

    # Add FAQ sections (procedural guidance, redemption steps, SIP instructions)
    for faq in faqs:
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
        "doc_date": iso_date,
        "canonical_facts": {
            "ter_direct": ter,
            "exit_load": exit_load,
            "min_sip": rupees(min_sip),
            "min_lumpsum": rupees(min_lumpsum),
            "min_additional": rupees(min_additional),
            "lock_in": lock_in,
            "riskometer": riskometer,
            "benchmark": benchmark,
            "nav": rupees(nav_raw),
            "aum": f"₹{aum_raw} Cr" if aum_raw not in (None, "") else NOT_LISTED,
            "fund_manager": fund_manager
        },
        "sections": sections
    }
