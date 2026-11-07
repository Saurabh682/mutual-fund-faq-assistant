"""Entity Resolution Engine for Mutual Fund FAQ Assistant.

Extracts scheme and field entities from user input, resolves pronouns/anaphora
using session state, performs fuzzy matching for typos/abbreviations, and detects
ambiguous queries requiring scheme clarification.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field as dc_field
from typing import Any, Dict, List, Optional
from app.guardrails.refusal import CANONICAL_LINKS, get_default_corpus_date
from app.guardrails.validator import validate_response

SCHEME_REGISTRY: Dict[str, Dict[str, Any]] = {
    "hdfc_midcap_dg": {
        "id": "hdfc_midcap_dg",
        "name": "HDFC Mid-Cap Opportunities Fund",
        "official_name": "HDFC Mid-Cap Opportunities Fund (Direct - Growth)",
        "category": "Equity: Mid Cap",
        "url": "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
        "amc_url": "https://www.hdfcfund.com/our-products/hdfc-mid-cap-opportunities-fund",
        "amfi_code": "118989",
        "amfi_url": "https://www.amfiindia.com/research-information/other-data/scheme-details?schemecode=118989",
        "publisher": "HDFC Asset Management Company Limited",
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
            "hdfc midcap opp fund",
            "hdfc mid cap opp",
            "hdfc midcap opp",
            "mid cap opp",
            "midcap opp",
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
        "amc_url": "https://www.hdfcfund.com/our-products/hdfc-small-cap-fund",
        "amfi_code": "130503",
        "amfi_url": "https://www.amfiindia.com/research-information/other-data/scheme-details?schemecode=130503",
        "publisher": "HDFC Asset Management Company Limited",
        "aliases": [
            "hdfc small cap fund",
            "hdfc small-cap fund",
            "hdfc small-cap opportunities",
            "small-cap opportunities",
            "hdfc sml cap direct growth",
            "hdfc sml cap",
            "sml cap direct growth",
            "sml cap fund",
            "sml cap",
            "smlcap",
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
        "amc_url": "https://www.hdfcfund.com/our-products/hdfc-top-100-fund",
        "amfi_code": "119062",
        "amfi_url": "https://www.amfiindia.com/research-information/other-data/scheme-details?schemecode=119062",
        "publisher": "HDFC Asset Management Company Limited",
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
        "amc_url": "https://www.hdfcfund.com/our-products/hdfc-silver-etf-fund-fund",
        "amfi_code": "150186",
        "amfi_url": "https://www.amfiindia.com/research-information/other-data/scheme-details?schemecode=150186",
        "publisher": "HDFC Asset Management Company Limited",
        "aliases": [
            "hdfc silver etf fund of fund",
            "hdfc silver etf fund of funds",
            "silver etf fund of funds",
            "hdfc silver fof growth",
            "hdfc silver etf fof",
            "hdfc silver fof",
            "silver etf fof",
            "silver fof",
            "hdfc silver etf",
            "hdfc silver fund",
            "hdfc silver",
            "silver etf",
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
        "amc_url": "https://www.hdfcfund.com/our-products/hdfc-multi-cap-fund",
        "amfi_code": "149262",
        "amfi_url": "https://www.amfiindia.com/research-information/other-data/scheme-details?schemecode=149262",
        "publisher": "HDFC Asset Management Company Limited",
        "aliases": [
            "hdfc multi cap fund",
            "hdfc multi-cap fund",
            "hdfc multi cap",
            "hdfc multi-cap",
            "hdfc multicap",
            "multicap direct growth",
            "hdfc multicap direct growth",
            "multicap scheme",
            "multicap fund",
            "multicap",
            "multi cap fund",
            "multi-cap fund",
            "multi cap",
            "multi-cap",
        ],
    },
}

EXTERNAL_AMCS = [
    "sbi", "icici", "axis", "kotak", "nippon", "mirae", "tata",
    "parag parikh", "uti", "aditya birla", "dsp", "motilal", "quant",
    "bandhan", "canara robeco", "edelweiss", "franklin", "invesco",
    "hsbc", "sundaram", "pgim", "baroda bnp", "navi", "zerodha"
]

FIELD_GLOSSARY: Dict[str, List[str]] = {
    "ter_direct": [
        "ter", "expense ratio", "total expense ratio", "expenses",
        "management fee", "charges", "annual charge", "direct ter"
    ],
    "exit_load": [
        "exit load", "exit fee", "exit penalty", "redemption fee",
        "redemption penalty", "exit load period", "exit charge"
    ],
    "min_sip": [
        "minimum sip", "min sip", "sip minimum", "starting sip",
        "sip limit", "sip amount", "minimum sip investment",
        "minimum sip installment"
    ],
    "benchmark": [
        "benchmark", "benchmark index", "index", "tracks",
        "tracking index", "target index", "benchmark name"
    ],
    "riskometer": [
        "riskometer", "risk level", "risk grade", "risk category",
        "risk", "risk meter", "sebi riskometer"
    ],
    "nav": [
        "nav", "net asset value", "unit price", "price per unit",
        "current nav", "latest nav", "nav date"
    ],
    "aum": [
        "aum", "assets under management", "fund size", "asset size",
        "total assets", "corpus", "market cap of fund"
    ],
    "lock_in": [
        "lock-in", "lock in", "lockin", "lock-in period", "lock in period",
        "mandatory holding", "holding period", "lock in duration"
    ],
    "fund_manager": [
        "fund manager", "manager", "portfolio manager", "who manages",
        "who is managing", "managing", "managed by", "fund management"
    ],
    "factsheet": [
        "factsheet", "scheme factsheet", "monthly factsheet", "download factsheet", "download the factsheet",
        "standard procedure to check fund manager tenure", "procedure to check fund manager tenure",
        "where to check fund manager tenure", "check fund manager tenure"
    ],
    "nav_source": [
        "official source where unitholders can verify", "where unitholders can verify the nav",
        "where to verify the nav", "source where unitholders can verify the nav"
    ],
    "portfolio_turnover": [
        "portfolio turnover", "portfolio turnover ratio", "turnover ratio"
    ],
    "amc_name": [
        "amc name", "confirm the amc name", "amc", "fund house", "fund house name", "asset management company"
    ],
}

PRONOUN_PATTERN = re.compile(
    r"\b(it|this\s+fund|this\s+scheme|the\s+fund|the\s+scheme|its|that\s+fund|that\s+scheme)\b",
    re.I
)


@dataclass
class EntityResolutionResult:
    scheme_id: Optional[str]
    scheme_name: Optional[str]
    citation_url: Optional[str]
    field: Optional[str]
    fields: List[str] = dc_field(default_factory=list)
    is_ambiguous: bool = False
    is_external_amc: bool = False
    is_unsupported_plan: bool = False
    matched_scheme_alias: Optional[str] = None
    matched_field_alias: Optional[str] = None


def resolve_entities(
    query: str, session_scheme_id: Optional[str] = None
) -> EntityResolutionResult:
    """Resolves target scheme and field entities from a user query string.

    Supports exact alias matching, multi-token colloquial variants,
    pronoun/anaphora resolution, and fuzzy string similarity for typos.
    """
    clean_query = query.lower()
    norm_query = re.sub(r"[-\s]+", " ", clean_query)

    # 1. Match Scheme Entity (Longest exact alias match first)
    detected_scheme_id = None
    detected_scheme_alias = None

    for sid, info in SCHEME_REGISTRY.items():
        sorted_aliases = sorted(info["aliases"], key=len, reverse=True)
        for alias in sorted_aliases:
            norm_alias = re.sub(r"[-\s]+", " ", alias.lower())
            pattern = r"\b" + re.escape(norm_alias) + r"\b"
            if re.search(pattern, norm_query) or re.search(r"\b" + re.escape(alias) + r"\b", clean_query):
                if detected_scheme_alias is None or len(alias) > len(detected_scheme_alias):
                    detected_scheme_id = sid
                    detected_scheme_alias = alias

    # 1b. Fuzzy Matching for Typos & Abbreviations (e.g. 'sml cap', 'midcap opp')
    if not detected_scheme_id:
        words = norm_query.split()
        candidate_ngrams = []
        for n in (1, 2, 3):
            for i in range(len(words) - n + 1):
                candidate_ngrams.append(" ".join(words[i:i+n]))

        best_score = 0.0
        best_sid = None
        best_alias = None

        for sid, info in SCHEME_REGISTRY.items():
            for alias in info["aliases"]:
                norm_alias = re.sub(r"[-\s]+", " ", alias.lower())
                for ngram in candidate_ngrams:
                    if len(ngram) < 4:
                        continue
                    sim = difflib.SequenceMatcher(None, ngram, norm_alias).ratio()
                    if sim > best_score and sim >= 0.78:
                        best_score = sim
                        best_sid = sid
                        best_alias = alias

        if best_sid:
            detected_scheme_id = best_sid
            detected_scheme_alias = best_alias

    # 2. Pronoun / Anaphora Resolution (EC-ENT-02)
    if not detected_scheme_id and session_scheme_id in SCHEME_REGISTRY:
        if PRONOUN_PATTERN.search(clean_query):
            detected_scheme_id = session_scheme_id
            detected_scheme_alias = "session_anaphora"

    # 3. Match Field Entities (supports both single field and multi-field queries)
    detected_field = None
    detected_field_alias = None
    detected_fields = []

    for f_key, keywords in FIELD_GLOSSARY.items():
        sorted_kw = sorted(keywords, key=len, reverse=True)
        for kw in sorted_kw:
            norm_kw = re.sub(r"[-\s]+", " ", kw.lower())
            pattern = r"\b" + re.escape(norm_kw) + r"\b"
            if re.search(pattern, norm_query) or re.search(r"\b" + re.escape(kw) + r"\b", clean_query):
                if f_key not in detected_fields:
                    detected_fields.append(f_key)
                if detected_field_alias is None or len(kw) > len(detected_field_alias):
                    detected_field = f_key
                    detected_field_alias = kw
                break

    # 4. Check External AMC & Ambiguity (EC-ENT-01 & EC-RET-02)
    has_external_amc = any(
        re.search(r"\b" + re.escape(amc) + r"\b", clean_query) for amc in EXTERNAL_AMCS
    )
    if has_external_amc:
        detected_scheme_id = None
        detected_scheme_alias = None

    # Check Unsupported Plan / Option (Regular Plan or IDCW/Dividend)
    is_unsupported_plan = bool(
        re.search(r"\b(?:regular\s+plan|regular\s+growth|regular\s+scheme)\b", clean_query)
        or re.search(r"\b(?:idcw|dividend\s+plan|dividend\s+option|dividend\s+payout)\b", clean_query)
    )

    is_ambiguous = (
        detected_scheme_id is None
        and detected_field is not None
        and not has_external_amc
        and not is_unsupported_plan
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
        fields=detected_fields,
        is_ambiguous=is_ambiguous,
        is_external_amc=has_external_amc,
        is_unsupported_plan=is_unsupported_plan,
        matched_scheme_alias=detected_scheme_alias,
        matched_field_alias=detected_field_alias,
    )


def get_unsupported_plan_response(query: Optional[str] = None) -> Dict[str, Any]:
    """Returns compliant response when user queries Regular plans or IDCW options."""
    doc_date = get_default_corpus_date()
    citation = "https://www.hdfcfund.com"
    text = (
        "This assistant strictly indexes Direct Plan (Growth Option) schemes. "
        "Regular plans and IDCW options are not part of our verified records. "
        "Please query Direct Plan (Growth Option) metrics across our 5 supported HDFC funds."
    )
    val_res = validate_response(text, None, citation, doc_date)
    return {
        "text": val_res.text,
        "citation_url": val_res.citation_url,
        "last_updated": val_res.last_updated,
        "rendered": val_res.rendered,
        "is_unsupported_plan": True,
    }


def get_external_amc_response(detected_amc: Optional[str] = None) -> Dict[str, Any]:
    """Returns compliant response when user asks about a non-HDFC AMC."""
    doc_date = get_default_corpus_date()
    citation = "https://www.amfiindia.com/investor-corner/knowledge-center"
    amc_label = f"'{detected_amc.title()}'" if detected_amc else "external fund houses"
    text = (
        f"I can only provide official records for 5 selected HDFC Mutual Fund schemes. "
        f"Information regarding {amc_label} is not available in our verified corpus. "
        f"You can explore comprehensive scheme information on the official AMFI portal."
    )
    val_res = validate_response(text, None, citation, doc_date)
    return {
        "text": val_res.text,
        "citation_url": val_res.citation_url,
        "last_updated": val_res.last_updated,
        "rendered": val_res.rendered,
        "is_external_amc": True,
    }


def get_disambiguation_response(last_updated: Optional[str] = None) -> Dict[str, Any]:
    """Generates the required single-sentence clarification prompt when scheme is ambiguous."""
    body = (
        "Please specify which HDFC scheme you are inquiring about: "
        "HDFC Mid-Cap Opportunities Fund, HDFC Small Cap Fund, HDFC Top 100 Fund, "
        "HDFC Silver ETF FoF, or HDFC Multi Cap Fund."
    )
    url = CANONICAL_LINKS["ADVISORY"]
    doc_date = last_updated or get_default_corpus_date()
    val_res = validate_response(body, None, url, doc_date)

    return {
        "text": val_res.text,
        "citation_url": val_res.citation_url,
        "last_updated": val_res.last_updated,
        "rendered": val_res.rendered,
        "is_clarification": True,
    }


def get_scheme_meta(scheme_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve metadata for a known scheme ID."""
    return SCHEME_REGISTRY.get(scheme_id)
