"""Refusal Engine for Mutual Fund FAQ Assistant.

Serves 100% deterministic, non-LLM refusals for non-compliant queries:
- Advisory & Recommendations
- Scheme Comparisons & Rankings
- Future Return Projections
- Tax Evasion & Legal Advice
- Out-of-Scope Topics

Adheres strictly to the Response Contract:
1. Maximum 3 sentences.
2. Exactly 1 canonical citation URL.
3. Mandatory date footer: 'Last updated from sources: <YYYY-MM-DD>'.
4. Zero opinion words and zero investment advice.
"""

from __future__ import annotations

import os
from datetime import date, datetime
from typing import Any, Dict, Optional
import yaml

REFUSAL_TEMPLATES: Dict[str, str] = {
    "ADVISORY": (
        "I can only provide objective, factual information regarding mutual fund schemes "
        "and cannot offer investment advice, comparisons, or recommendations. "
        "For guidance on fund selection and financial planning, please consult a "
        "SEBI-registered investment advisor or review educational resources."
    ),
    "COMPARATIVE": (
        "I cannot compare or rank mutual fund schemes against each other. "
        "You can review the official factsheet for each individual scheme to compare their "
        "benchmark index, expense ratios, and portfolio allocations."
    ),
    "PROJECTION": (
        "I cannot calculate future returns or provide return projections for mutual fund schemes. "
        "Historical performance data and rolling returns are documented in the official scheme factsheet."
    ),
    "TAX_LEGAL": (
        "I cannot provide tax planning advice or strategies for avoiding capital gains tax. "
        "Please consult a qualified tax professional or refer to official tax guidelines."
    ),
    "OUT_OF_SCOPE": (
        "I can only assist with factual information regarding selected HDFC Mutual Fund schemes "
        "and standard investment procedures. "
        "Please ask a question related to these mutual fund schemes."
    ),
    "SMALLTALK": (
        "Hello! I am the Mutual Fund FAQ Assistant for HDFC Mutual Fund schemes. "
        "You can ask me factual questions regarding expense ratios, exit loads, minimum SIPs, "
        "benchmarks, and riskometers for our 5 supported schemes."
    ),
}

CANONICAL_LINKS: Dict[str, str] = {
    "ADVISORY": "https://www.amfiindia.com/investor-corner/knowledge-center",
    "COMPARATIVE": "https://www.amfiindia.com/investor-corner/knowledge-center",
    "PROJECTION": "https://www.amfiindia.com/investor-corner/knowledge-center",
    "TAX_LEGAL": "https://www.amfiindia.com/investor-corner/knowledge-center",
    "OUT_OF_SCOPE": "https://www.amfiindia.com/investor-corner/knowledge-center",
    "SMALLTALK": "https://www.amfiindia.com/investor-corner/knowledge-center",
}

_DEFAULT_MANIFEST_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../data/corpus_manifest.yaml")
)


def get_default_corpus_date(manifest_path: str = _DEFAULT_MANIFEST_PATH) -> str:
    """Retrieve corpus last_refreshed date from manifest or fall back to current date."""
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data and "last_refreshed" in data:
                    return str(data["last_refreshed"])
        except Exception:
            pass
    return date.today().isoformat()


def normalize_date_footer(date_str: Optional[str]) -> str:
    """Normalizes any date string to ISO YYYY-MM-DD format."""
    if not date_str:
        return get_default_corpus_date()
    clean = str(date_str).strip()
    try:
        # Handles 23-Oct-2026 or 23-OCT-2026
        return datetime.strptime(clean, "%d-%b-%Y").strftime("%Y-%m-%d")
    except Exception:
        pass
    try:
        # Handles YYYY-MM-DD
        return datetime.strptime(clean, "%Y-%m-%d").strftime("%Y-%m-%d")
    except Exception:
        pass
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(clean, fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    return get_default_corpus_date()


def generate_refusal(
    intent: str,
    last_updated: Optional[str] = None,
    scheme_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Generates a deterministic refusal payload complying strictly with the response contract.

    Args:
        intent: Classified intent (e.g., ADVISORY, COMPARATIVE, PROJECTION, TAX_LEGAL).
        last_updated: Date string in YYYY-MM-DD format (defaults to corpus refresh date).
        scheme_url: Optional scheme URL to cite for PROJECTION refusals.

    Returns:
        Dict with keys: text, citation_url, last_updated, rendered.
    """
    normalized_intent = intent.upper()
    body = REFUSAL_TEMPLATES.get(normalized_intent, REFUSAL_TEMPLATES["ADVISORY"])

    if normalized_intent == "PROJECTION" and scheme_url:
        citation_url = scheme_url
    else:
        citation_url = CANONICAL_LINKS.get(
            normalized_intent, CANONICAL_LINKS["ADVISORY"]
        )

    doc_date = normalize_date_footer(last_updated)
    rendered = f"{body}\n\nSource: {citation_url}\nLast updated from sources: {doc_date}"

    return {
        "text": body,
        "citation_url": citation_url,
        "last_updated": doc_date,
        "rendered": rendered,
        "is_refusal": True,
        "intent": normalized_intent,
    }


def generate_compound_refusal(
    factual_sentence: str,
    intent: str,
    citation_url: str,
    last_updated: Optional[str] = None,
) -> Dict[str, Any]:
    """Generates a compound response for queries containing both factual and advisory components.

    Limits total response to 2 sentences:
    - Sentence 1: The factual answer.
    - Sentence 2: The compliance boundary refusal.
    """
    clean_fact = factual_sentence.strip()
    if not clean_fact.endswith("."):
        clean_fact += "."

    if intent == "ADVISORY":
        compliance_sentence = "I cannot provide investment advice or recommendations on whether you should invest in this fund."
    elif intent == "COMPARATIVE":
        compliance_sentence = "I cannot compare or rank mutual fund schemes against each other."
    elif intent == "PROJECTION":
        compliance_sentence = "I cannot calculate future returns or provide return projections."
    else:
        compliance_sentence = "I can only provide factual mutual fund information and cannot offer advice."

    body = f"{clean_fact} {compliance_sentence}"
    doc_date = normalize_date_footer(last_updated)
    rendered = f"{body}\n\nSource: {citation_url}\nLast updated from sources: {doc_date}"

    return {
        "text": body,
        "citation_url": citation_url,
        "last_updated": doc_date,
        "rendered": rendered,
        "is_compound": True,
        "is_refusal": True,
        "intent": intent,
    }
