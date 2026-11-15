"""Structured Fact Store Engine for Mutual Fund FAQ Assistant.

Retrieves exact canonical figures (TER, NAV, Exit Load, Min SIP, Riskometer)
from SQLite (data/index/facts.db) with O(1) latency (< 50ms) and zero hallucinations.
Adheres strictly to the 5-point Output Response Contract.
"""

from __future__ import annotations

import os
import re
import sqlite3
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.guardrails.validator import normalize_date_footer, validate_response
from app.rag.entities import SCHEME_REGISTRY, resolve_entities

# What ingest/parsers/html.py stores when the Groww page has no value for a field (a test pins both copies)
NOT_LISTED = "Not listed on the Groww page"

_FACTS_DB_PATH = os.path.join(settings.DATA_DIR, "index", "facts.db")

FIELD_LABELS = {
    "nav": "NAV (Net Asset Value)",
    "expense_ratio": "Total Expense Ratio (Direct - Growth)",
    "ter_direct": "Total Expense Ratio (Direct - Growth)",
    "exit_load": "Exit Load",
    "min_sip": "Minimum SIP Amount",
    "riskometer": "SEBI Riskometer Tier",
    "benchmark": "Benchmark Index",
    "fund_manager": "Primary Lead Fund Manager",
    "nav_source": "NAV Source",
    "aum": "AUM (Fund Size)",
    "aum_cr": "AUM (Fund Size)",
    "turnover_ratio": "Portfolio Turnover Ratio",
    "lock_in": "Lock-in Period",
    "min_lumpsum": "Minimum Lumpsum Amount",
    "min_additional": "Minimum Additional Investment",
}

FACT_TEMPLATES = {
    "ter_direct": "The Total Expense Ratio (TER) of {scheme_name} (Direct Plan - Growth Option) is {value}% per the Groww scheme page.",
    "nav": "The Net Asset Value (NAV) of {scheme_name} is ₹{value} as per the latest daily valuation.",
    "exit_load": "The exit load for {scheme_name} is {value}.",
    "min_sip": "The minimum SIP investment amount for {scheme_name} is ₹{value}.",
    "riskometer": "The risk level for {scheme_name} is classified as {value} on the SEBI Riskometer per the Groww scheme page.",
    "benchmark": "The benchmark index for {scheme_name} is {value}.",
    "fund_manager": "The fund manager for {scheme_name} is {value} as listed on the Groww scheme page.",
    "aum_cr": "The total Assets Under Management (AUM) for {scheme_name} is ₹{value} Cr per the Groww scheme page.",
    "lock_in": "The lock-in period for {scheme_name} is {value} per the Groww scheme page.",
    "min_lumpsum": "The minimum lumpsum investment amount for {scheme_name} is {value}.",
    "min_additional": "The minimum additional investment amount for {scheme_name} is {value}.",
}


def normalize_iso_date(date_str: Optional[str]) -> str:
    """Ensures consistent ISO YYYY-MM-DD format for fact timestamps."""
    return normalize_date_footer(date_str)


def get_fact_from_db(
    scheme_id: str, field: str, db_path: str = _FACTS_DB_PATH
) -> Optional[Dict[str, Any]]:
    """Fetches a canonical ground-truth value for a scheme and field from SQLite."""
    if not os.path.exists(db_path):
        return None

    # Map aliases
    canonical_field = "ter_direct" if field == "expense_ratio" else field

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT scheme_id, field, value, as_of
            FROM facts
            WHERE scheme_id = ? AND field = ?
            LIMIT 1
            """,
            (scheme_id, canonical_field),
        )
        row = cursor.fetchone()
        if not row:
            meta = SCHEME_REGISTRY.get(scheme_id, {})
            site = meta.get("amc_domain", "the AMC website")
            if field == "nav_source":
                return {
                    "scheme_id": scheme_id,
                    "field": field,
                    "value": f"AMFI official portal (amfiindia.com) and {site}",
                    "value_str": f"AMFI official portal (amfiindia.com) and {site}",
                    "value_num": None,
                    "as_of": "2026-11-05",
                    "doc_date": "2026-11-05",
                }
            elif field == "factsheet":
                return {
                    "scheme_id": scheme_id,
                    "field": field,
                    "value": f"Monthly Factsheet available on {site}",
                    "value_str": f"Monthly Factsheet available on {site}",
                    "value_num": None,
                    "as_of": "2026-11-05",
                    "doc_date": "2026-11-05",
                }
            elif field == "portfolio_turnover":
                return {
                    "scheme_id": scheme_id,
                    "field": field,
                    "value": f"Disclosed in monthly scheme factsheet on {site}",
                    "value_str": f"Disclosed in monthly scheme factsheet on {site}",
                    "value_num": None,
                    "as_of": "2026-11-05",
                    "doc_date": "2026-11-05",
                }
            elif field == "amc_name":
                return {
                    "scheme_id": scheme_id,
                    "field": field,
                    "value": meta.get("publisher", "the asset management company"),
                    "value_str": meta.get("publisher", "the asset management company"),
                    "value_num": None,
                    "as_of": "2026-11-05",
                    "doc_date": "2026-11-05",
                }
            return None

        val_str = str(row["value"])
        val_num = None
        num_match = re.search(r"[-+]?\d*\.\d+|\d+", val_str.replace(",", ""))
        if num_match:
            try:
                val_num = float(num_match.group(0))
            except ValueError:
                pass

        return {
            "scheme_id": row["scheme_id"],
            "field": row["field"],
            "value": val_str,
            "value_str": val_str,
            "value_num": val_num,
            "as_of": row["as_of"],
            "doc_date": row["as_of"],
        }
    finally:
        conn.close()


def get_all_facts_for_scheme(scheme_id: str, db_path: str = _FACTS_DB_PATH) -> Dict[str, Dict[str, Any]]:
    """Retrieve all structured facts from facts.db for a given scheme."""
    if not os.path.exists(db_path):
        return {}
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT field, value, as_of, source_url FROM facts WHERE scheme_id = ?",
            (scheme_id,),
        )
        rows = cur.fetchall()
        return {
            r["field"]: {
                "value": str(r["value"]),
                "as_of": r["as_of"],
                "source_url": r["source_url"] if "source_url" in r.keys() else None,
            }
            for r in rows
        }
    finally:
        conn.close()


def plain_exit_load(value: Any) -> str:
    """Groww words the value 'Exit load of 1% if redeemed within 1 year.'; drop the lead-in so 'The exit load is ...' reads once."""
    return re.sub(r"^\s*exit\s+load\s+(?:of\s+)?", "", str(value), flags=re.I).rstrip(".")


def group_indian(text: str) -> str:
    """'₹100687.07 Cr' -> '₹1,00,687.07 Cr': lakh/crore grouping, as Groww prints it. Numbers already grouped are left alone."""

    def _group(m: "re.Match[str]") -> str:
        digits, frac = m.group(1), m.group(2) or ""
        if len(digits) < 4:
            return m.group(0)
        head = re.sub(r"\B(?=(\d{2})+(?!\d))", ",", digits[:-3])
        return f"{head},{digits[-3:]}{frac}" if head else f"{digits}{frac}"

    return re.sub(r"(?<![\d,.])(\d+)(\.\d+)?(?![\d,])", _group, text)


def _display_value(field: str, value: Any) -> str:
    """The value as shown in the stat card, without the wording and number-format quirks of the source page."""
    if field == "exit_load":
        return plain_exit_load(value)
    if field == "aum":
        return group_indian(str(value))
    return str(value)


def format_fact_response(fact: Dict[str, Any]) -> Dict[str, Any]:
    """Formats a deterministic ground-truth fact card complying with the response contract.

    Adheres strictly to:
    1. Maximum 3 sentences (narrative prose strictly 1 sentence).
    2. Exactly 1 primary citation URL footer.
    3. Mandatory ISO date footer.
    4. Numeric grounding invariant verified via Output Contract Validator.
    """
    scheme_id = fact["scheme_id"]
    field = fact["field"]
    raw_val = fact["value"]

    meta = SCHEME_REGISTRY.get(scheme_id, {})
    scheme_name = meta.get("official_name", meta.get("name", scheme_id))
    citation_url = meta.get("url", "https://groww.in")
    site = meta.get("amc_domain", "the AMC website")
    publisher = meta.get("publisher", "the asset management company")
    amc_url = meta.get("amc_url")
    amfi_code = meta.get("amfi_code")
    field_title = FIELD_LABELS.get(field, field.replace("_", " ").title())

    # Build compliant single-sentence narrative prose
    val_clean = str(raw_val).rstrip(".")
    if str(raw_val).startswith(NOT_LISTED):
        narrative = f"The {field_title} of {scheme_name} is not listed on the Groww scheme page."
    elif field in ("expense_ratio", "ter_direct"):
        val_display = f"{raw_val}%" if not str(raw_val).endswith("%") else str(raw_val)
        narrative = (
            f"The Total Expense Ratio (TER) of {scheme_name} (Direct Plan - Growth Option) is "
            f"{val_display.rstrip('.')} per the Groww scheme page."
        )
    elif field == "nav":
        val_display = f"₹{raw_val}" if not str(raw_val).startswith("₹") else str(raw_val)
        narrative = f"The Net Asset Value (NAV) of {scheme_name} is {val_display.rstrip('.')} as per the latest daily valuation."
    elif field == "exit_load":
        narrative = f"The exit load for {scheme_name} is {plain_exit_load(raw_val)}."
    elif field == "aum":
        narrative = f"The AUM for {scheme_name} is {group_indian(val_clean)}."
    elif field == "min_sip":
        val_display = f"₹{raw_val}" if not str(raw_val).startswith("₹") else str(raw_val)
        narrative = f"The minimum SIP investment amount for {scheme_name} is {val_display.rstrip('.')}."
    elif field == "min_lumpsum":
        val_display = f"₹{raw_val}" if not str(raw_val).startswith("₹") else str(raw_val)
        narrative = f"The minimum lumpsum investment amount for {scheme_name} is {val_display.rstrip('.')}."
    elif field == "min_additional":
        val_display = f"₹{raw_val}" if not str(raw_val).startswith("₹") else str(raw_val)
        narrative = f"The minimum additional investment amount for {scheme_name} is {val_display.rstrip('.')}."
    elif field == "riskometer":
        narrative = f"The risk level for {scheme_name} is classified as {val_clean} on the SEBI Riskometer per the Groww scheme page."
    elif field == "benchmark":
        narrative = f"The benchmark index for {scheme_name} is {val_clean}."
    elif field == "fund_manager":
        narrative = f"The primary lead fund manager for {scheme_name} is {val_clean} as listed on the Groww scheme page."
    elif field == "aum_cr":
        val_display = (
            f"₹{raw_val} Cr" if not str(raw_val).endswith("Cr") else f"₹{raw_val}"
        )
        narrative = f"The total Assets Under Management (AUM) for {scheme_name} is {val_display.rstrip('.')}."
    elif field == "lock_in":
        narrative = f"The lock-in period for {scheme_name} is {val_clean} per the Groww scheme page."
    elif field == "nav_source":
        narrative = f"Unitholders can verify daily NAV for {scheme_name} on the AMFI portal (amfiindia.com) and the AMC website ({site})."
    elif field == "factsheet":
        narrative = f"The monthly scheme factsheet for {scheme_name} is published and available for download on {site}."
    elif field == "portfolio_turnover":
        narrative = f"The portfolio turnover ratio for {scheme_name} is documented in the monthly scheme factsheet on {site}."
    elif field == "amc_name":
        narrative = f"The asset management company (AMC) for {scheme_name} is {publisher}."
    else:
        narrative = f"The {field_title} for {scheme_name} is {val_clean}."

    # Programmatic markdown stat-card table
    stat_card_rows = [
        "| Metric | Value |",
        "| :--- | :--- |",
        f"| **Scheme** | {scheme_name} |",
        f"| **{field_title}** | {_display_value(field, raw_val)} |",
    ]
    if amfi_code:
        stat_card_rows.append(f"| **AMFI Code** | {amfi_code} |")
    stat_card_rows.append(f"| **Fund House** | {publisher} |")
    stat_card_rows.append("| **Data Source** | Groww scheme page |")
    doc_date = normalize_iso_date(fact.get("as_of") or fact.get("doc_date", ""))

    stat_card = "\n".join(stat_card_rows)
    body = f"{narrative}\n\n{stat_card}".strip()
    val_res = validate_response(body, None, citation_url, doc_date)

    return {
        "text": val_res.text,
        "citation_url": val_res.citation_url,
        "last_updated": val_res.last_updated,
        "rendered": val_res.rendered,
        "sentence_count": val_res.sentence_count,
        "source": "fact_store",
        "scheme_id": scheme_id,
        "field": field,
        "raw_value": raw_val,
    }


def format_multi_fact_response(
    facts: List[Dict[str, Any]], scheme_id: str
) -> Dict[str, Any]:
    """Formats multiple canonical ground-truth facts into a single structured response."""
    meta = SCHEME_REGISTRY.get(scheme_id, {})
    scheme_name = meta.get("official_name", meta.get("name", scheme_id))
    citation_url = meta.get("url", "https://groww.in")
    site = meta.get("amc_domain", "the AMC website")
    publisher = meta.get("publisher", "the asset management company")

    narrative_sentences = []
    stat_card_rows = [
        "| Metric | Value |",
        "| :--- | :--- |",
        f"| **Scheme** | {scheme_name} |",
    ]

    latest_doc_date = "2026-11-05"
    for fact in facts:
        f_name = fact["field"]
        val = fact["value"]
        title = FIELD_LABELS.get(f_name, f_name.replace("_", " ").title())
        stat_card_rows.append(f"| **{title}** | {_display_value(f_name, val)} |")

        if fact.get("as_of"):
            d = normalize_iso_date(fact["as_of"])
            if d > latest_doc_date:
                latest_doc_date = d

        if str(val).startswith(NOT_LISTED):
            narrative_sentences.append(f"The {title} is not listed on the Groww scheme page.")
        elif f_name in ("ter_direct", "expense_ratio"):
            val_disp = f"{val}%" if not str(val).endswith("%") else str(val)
            narrative_sentences.append(f"The Total Expense Ratio (TER) is {val_disp}.")
        elif f_name == "exit_load":
            narrative_sentences.append(f"The exit load is {plain_exit_load(val)}.")
        elif f_name == "nav":
            val_disp = f"₹{val}" if not str(val).startswith("₹") else str(val)
            narrative_sentences.append(f"The latest NAV is {val_disp}.")
        elif f_name == "min_sip":
            val_disp = f"₹{val}" if not str(val).startswith("₹") else str(val)
            narrative_sentences.append(f"The minimum SIP amount is {val_disp}.")
        elif f_name == "riskometer":
            narrative_sentences.append(f"The SEBI Riskometer level is {val}.")
        else:
            narrative_sentences.append(f"The {title} is {val}.")

    if meta.get("amfi_code"):
        stat_card_rows.append(f"| **AMFI Code** | {meta['amfi_code']} |")
    stat_card_rows.append(f"| **Fund House** | {publisher} |")
    stat_card_rows.append("| **Data Source** | Groww scheme page |")

    narrative = f"For {scheme_name}: " + " ".join(narrative_sentences)
    stat_card = "\n".join(stat_card_rows)
    body = f"{narrative}\n\n{stat_card}".strip()
    val_res = validate_response(body, None, citation_url, latest_doc_date)

    return {
        "text": val_res.text,
        "citation_url": val_res.citation_url,
        "last_updated": val_res.last_updated,
        "rendered": val_res.rendered,
        "sentence_count": val_res.sentence_count,
        "source": "fact_store",
        "scheme_id": scheme_id,
        "field": "multi_field",
        "fields": [f["field"] for f in facts],
        "raw_value": ", ".join(f"{f['field']}={f['value']}" for f in facts),
    }


_PAST_POINT_IN_TIME = re.compile(
    r"\b(?:19|20)\d{2}\b|\b(?:yesterday|last\s+(?:year|month|week)|on\s+\d{1,2}(?:st|nd|rd|th)?\s+\w+)\b", re.I
)


def lookup_fact(
    query: str, session_scheme_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """End-to-end fact and procedural path lookup.

    Resolves scheme and field entities from query, queries facts.db, and formats
    a 100% deterministic response if hit. If not a specific fund metric, checks
    standard mutual fund and Groww procedures (e.g. Capital Gains, Redemption).
    """
    entity_res = resolve_entities(query, session_scheme_id=session_scheme_id)

    # Only today's NAV/AUM is stored: a dated question must not get the current value as if it were that day's
    if entity_res.field in ("nav", "aum") and _PAST_POINT_IN_TIME.search(query):
        return None

    # 1. Scheme-Specific Fact Path
    if entity_res.scheme_id and entity_res.field:
        if entity_res.fields and len(entity_res.fields) > 1:
            matched_facts = []
            for f in entity_res.fields:
                row = get_fact_from_db(entity_res.scheme_id, f)
                if row:
                    matched_facts.append(row)
            if len(matched_facts) > 1:
                return format_multi_fact_response(matched_facts, entity_res.scheme_id)
            elif len(matched_facts) == 1:
                return format_fact_response(matched_facts[0])

        fact_row = get_fact_from_db(entity_res.scheme_id, entity_res.field)
        if fact_row:
            return format_fact_response(fact_row)

    # 2. Educational Glossary Match (e.g., "What is Total Expense Ratio?", "What is exit load?")
    from app.rag.glossary import lookup_glossary
    glossary_match = lookup_glossary(query)
    if glossary_match:
        return glossary_match

    # 3. Procedural / Regulatory Norms Match (e.g. KYC, ELSS lock-in, SEBI riskometer)
    from app.rag.procedures import lookup_procedure
    proc_match = lookup_procedure(query)
    if proc_match:
        return proc_match

    # 4. Ambiguity check: scheme-specific query missing scheme identity
    if entity_res.is_ambiguous:
        return None

    return None


def get_all_scheme_facts_from_db() -> list[dict]:
    """Returns verified scheme facts for every indexed scheme."""
    from app.rag.entities import SCHEME_REGISTRY
    result = []
    for sid, info in SCHEME_REGISTRY.items():
        f = get_all_facts_for_scheme(sid)
        f["scheme_id"] = sid
        f["scheme_name"] = info.get("name", sid)
        result.append(f)
    return result
