"""Entity Resolution Engine for Mutual Fund FAQ Assistant.

Extracts scheme and field entities from user input, resolves pronouns/anaphora
using session state, and detects ambiguous queries requiring scheme clarification.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from app.guardrails.refusal import CANONICAL_LINKS, get_default_corpus_date

SCHEME_REGISTRY: Dict[str, Dict[str, Any]] = {
    "hdfc_midcap_dg": {
        "id": "hdfc_midcap_dg",
        "name": "HDFC Mid-Cap Opportunities Fund",
        "official_name": "HDFC Mid-Cap Opportunities Fund (Direct - Growth)",
        "category": "Equity: Mid Cap",
        "url": "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
        "aliases": [
            "hdfc mid-cap opportunities fund",
            "hdfc mid cap opportunities fund",
            "hdfc mid-cap opportunities",
            "hdfc mid cap opportunities",
            "mid-cap opportunities fund",
            "mid cap opportunities fund",
            "mid-cap opportunities",
            "mid cap opportunities",
            "hdfc mid-cap fund",
            "hdfc mid cap fund",
            "hdfc mid cap",
            "hdfc midcap",
            "mid cap fund",
            "mid-cap fund",
            "mid cap",
            "midcap",
        ],
    },
    "hdfc_smallcap_dg": {
        "id": "hdfc_smallcap_dg",
        "name": "HDFC Small Cap Fund",
        "official_name": "HDFC Small Cap Fund (Direct - Growth)",
        "category": "Equity: Small Cap",
        "url": "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
        "aliases": [
            "hdfc small cap fund",
            "hdfc small-cap fund",
            "hdfc small cap",
            "hdfc smallcap",
            "small cap fund",
            "small-cap fund",
            "small cap",
            "smallcap",
        ],
    },
    "hdfc_largecap_dg": {
        "id": "hdfc_largecap_dg",
        "name": "HDFC Top 100 Fund",
        "official_name": "HDFC Top 100 Fund (Direct - Growth)",
        "category": "Equity: Large Cap",
        "url": "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
        "aliases": [
            "hdfc large cap fund",
            "hdfc large-cap fund",
            "hdfc top 100 fund",
            "hdfc top 100",
            "hdfc top100",
            "top 100 fund",
            "top 100",
            "top100",
            "hdfc large cap",
            "hdfc largecap",
            "large cap fund",
            "large-cap fund",
            "large cap",
            "largecap",
        ],
    },
    "hdfc_silver_fof_dg": {
        "id": "hdfc_silver_fof_dg",
        "name": "HDFC Silver ETF Fund of Fund",
        "official_name": "HDFC Silver ETF FoF (Direct - Growth)",
        "category": "Commodities: Silver FoF",
        "url": "https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth",
        "aliases": [
            "hdfc silver etf fund of fund",
            "hdfc silver etf fof",
            "hdfc silver etf",
            "hdfc silver fund",
            "hdfc silver",
            "silver etf fund of fund",
            "silver etf fof",
            "silver etf",
            "silver fof",
            "silver fund",
            "silver",
        ],
    },
    "hdfc_multicap_dg": {
        "id": "hdfc_multicap_dg",
        "name": "HDFC Multi Cap Fund",
        "official_name": "HDFC Multi Cap Fund (Direct - Growth)",
        "category": "Equity: Multi Cap",
        "url": "https://groww.in/mutual-funds/hdfc-multi-cap-fund-direct-growth",
        "aliases": [
            "hdfc multi cap fund",
            "hdfc multi-cap fund",
            "hdfc multi cap",
            "hdfc multicap",
            "multi cap fund",
            "multi-cap fund",
            "multi cap",
            "multicap",
        ],
    },
}

FIELD_GLOSSARY: Dict[str, List[str]] = {
    "ter_direct": [
        "total expense ratio",
        "expense ratio",
        "ter",
        "management fee",
        "management fees",
        "annual fee",
        "annual fees",
        "charges",
    ],
    "exit_load": [
        "exit load structure",
        "exit load",
        "exit penalty",
        "redemption penalty",
        "redemption fee",
        "redemption charges",
        "penalty for withdrawal",
        "withdrawal fee",
        "load structure",
    ],
    "min_sip": [
        "minimum sip investment",
        "minimum sip amount",
        "minimum sip",
        "min sip amount",
        "min sip",
        "sip installment",
        "minimum monthly investment",
        "start sip",
    ],
    "min_lumpsum": [
        "minimum lumpsum investment",
        "minimum lumpsum",
        "min lumpsum",
        "minimum investment amount",
        "minimum investment",
        "initial investment",
        "minimum purchase",
        "lumpsum",
    ],
    "min_additional": [
        "minimum additional investment",
        "mini additional investment",
        "minimum additional purchase",
        "additional purchase",
        "additional investment",
    ],
    "lock_in": [
        "lock in period",
        "lock-in period",
        "lock in",
        "lock-in",
        "lockin",
        "holding period",
    ],
    "riskometer": [
        "riskometer classification",
        "riskometer rating",
        "riskometer level",
        "riskometer",
        "risk category",
        "risk level",
        "risk profile",
        "risk rating",
    ],
    "benchmark": [
        "benchmark index",
        "underlying benchmark",
        "tracking index",
        "reference index",
        "benchmark",
    ],
    "nav": [
        "net asset value",
        "current nav",
        "nav price",
        "nav",
    ],
    "aum": [
        "assets under management",
        "asset under management",
        "fund size",
        "corpus size",
        "aum",
    ],
    "fund_manager": [
        "who manages",
        "fund manager details",
        "fund manager",
        "portfolio manager",
        "manager",
    ],
}

EXTERNAL_AMCS = [
    "sbi", "icici", "axis", "kotak", "nippon", "mirae", "tata", "dsp",
    "quant", "parag parikh", "motilal", "uti", "aditya birla", "franklin",
    "canara robeco", "bandhan", "invesco", "hsbc", "sundaram", "edelweiss",
]

PRONOUN_PATTERN = re.compile(
    r"\b(it|its|this fund|this scheme|the fund|the scheme|said fund|above fund)\b",
    re.I,
)


@dataclass
class EntityResolutionResult:
    scheme_id: Optional[str] = None
    scheme_name: Optional[str] = None
    citation_url: Optional[str] = None
    field: Optional[str] = None
    is_ambiguous: bool = False
    matched_scheme_alias: Optional[str] = None
    matched_field_alias: Optional[str] = None


def resolve_entities(
    query: str, session_scheme_id: Optional[str] = None
) -> EntityResolutionResult:
    """Resolves target scheme and field entities from a user query string.

    Args:
        query: User input query.
        session_scheme_id: Optional active scheme_id from thread history.

    Returns:
        EntityResolutionResult detailing matched scheme, field, and ambiguity status.
    """
    clean_query = query.lower()

    # 1. Match Scheme Entity (Longest alias match first)
    detected_scheme_id = None
    detected_scheme_alias = None

    for sid, info in SCHEME_REGISTRY.items():
        sorted_aliases = sorted(info["aliases"], key=len, reverse=True)
        for alias in sorted_aliases:
            pattern = r"\b" + re.escape(alias) + r"\b"
            if re.search(pattern, clean_query):
                if detected_scheme_alias is None or len(alias) > len(detected_scheme_alias):
                    detected_scheme_id = sid
                    detected_scheme_alias = alias

    # 2. Pronoun / Anaphora Resolution (EC-ENT-02)
    if not detected_scheme_id and session_scheme_id in SCHEME_REGISTRY:
        if PRONOUN_PATTERN.search(clean_query):
            detected_scheme_id = session_scheme_id
            detected_scheme_alias = "session_anaphora"

    # 3. Match Field Entity
    detected_field = None
    detected_field_alias = None

    for f_key, keywords in FIELD_GLOSSARY.items():
        sorted_kw = sorted(keywords, key=len, reverse=True)
        for kw in sorted_kw:
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, clean_query):
                if detected_field_alias is None or len(kw) > len(detected_field_alias):
                    detected_field = f_key
                    detected_field_alias = kw

    # 4. Check External AMC & Ambiguity (EC-ENT-01 & EC-RET-02)
    # If the user explicitly mentions an external AMC, it is strictly out-of-corpus (not HDFC).
    has_external_amc = any(
        re.search(r"\b" + re.escape(amc) + r"\b", clean_query) for amc in EXTERNAL_AMCS
    )
    if has_external_amc:
        detected_scheme_id = None
        detected_scheme_alias = None

    is_ambiguous = (
        detected_scheme_id is None
        and detected_field is not None
        and not has_external_amc
    )

    scheme_name = None
    citation_url = None
    if detected_scheme_id:
        meta = SCHEME_REGISTRY.get(detected_scheme_id, {})
        scheme_name = meta.get("name")
        citation_url = meta.get("url")

    return EntityResolutionResult(
        scheme_id=detected_scheme_id,
        scheme_name=scheme_name,
        citation_url=citation_url,
        field=detected_field,
        is_ambiguous=is_ambiguous,
        matched_scheme_alias=detected_scheme_alias,
        matched_field_alias=detected_field_alias,
    )


def get_disambiguation_response(last_updated: Optional[str] = None) -> Dict[str, Any]:
    """Generates the required single-sentence clarification prompt when scheme is ambiguous."""
    body = (
        "Please specify which HDFC scheme you are inquiring about: "
        "HDFC Mid-Cap Opportunities Fund, HDFC Small Cap Fund, HDFC Top 100 Fund, "
        "HDFC Silver ETF FoF, or HDFC Multi Cap Fund."
    )
    url = CANONICAL_LINKS["ADVISORY"]
    doc_date = last_updated or get_default_corpus_date()
    rendered = f"{body}\n\nSource: {url}\nLast updated from sources: {doc_date}"

    return {
        "text": body,
        "citation_url": url,
        "last_updated": doc_date,
        "rendered": rendered,
        "is_clarification": True,
    }


def get_scheme_meta(scheme_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve metadata for a known scheme ID."""
    return SCHEME_REGISTRY.get(scheme_id)
