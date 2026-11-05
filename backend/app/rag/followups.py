"""Deterministic Grounded Follow-up Suggestions Generator.

Generates 2-3 contextual follow-up question chips based on the active scheme,
metric field, and resolution type (EC-AUDIT-4.6).
"""

from __future__ import annotations

from typing import List, Optional
from app.rag.entities import SCHEME_REGISTRY


SCHEME_FIELD_SUGGESTIONS = {
    "ter_direct": [
        "What is the exit load for this fund?",
        "What is the minimum SIP amount for this fund?",
        "What is the riskometer rating for this fund?",
    ],
    "exit_load": [
        "What is the TER of this fund?",
        "What is the minimum SIP for this fund?",
        "Who is the fund manager of this fund?",
    ],
    "min_sip": [
        "What is the minimum lumpsum investment for this fund?",
        "What is the exit load for this fund?",
        "What is the TER of this fund?",
    ],
    "min_lumpsum": [
        "What is the minimum SIP amount for this fund?",
        "What is the exit load for this fund?",
    ],
    "riskometer": [
        "What is the benchmark index for this fund?",
        "What is the TER of this fund?",
        "Does this fund have any lock-in period?",
    ],
    "benchmark": [
        "What is the riskometer rating for this fund?",
        "Who manages this fund?",
        "What is the AUM of this fund?",
    ],
    "lock_in": [
        "What is the exit load for this fund?",
        "What is the minimum SIP for this fund?",
    ],
    "nav": [
        "What is the AUM of this fund?",
        "What is the TER of this fund?",
    ],
    "aum": [
        "What is the current NAV of this fund?",
        "Who manages this fund?",
    ],
    "fund_manager": [
        "What is the benchmark of this fund?",
        "What is the TER of this fund?",
    ],
    "multi_field": [
        "What is the benchmark for this fund?",
        "What is the riskometer rating for this fund?",
        "What is the minimum SIP for this fund?",
    ],
}

GLOSSARY_FOLLOWUPS = {
    "ter": [
        "What is the TER of HDFC Small Cap Fund?",
        "What is the TER of HDFC Top 100 Fund?",
        "Explain exit load",
    ],
    "exit_load": [
        "What is the exit load for HDFC Mid-Cap?",
        "What is the exit load for HDFC Silver FoF?",
        "What is lock-in period?",
    ],
    "sip": [
        "What is the minimum SIP for HDFC Small Cap?",
        "What is the minimum SIP for HDFC Multi Cap?",
        "What is Total Expense Ratio?",
    ],
    "nav": [
        "What is the NAV of HDFC Top 100 Fund?",
        "What is the NAV of HDFC Mid-Cap?",
    ],
    "riskometer": [
        "What is the riskometer rating for HDFC Small Cap?",
        "What is the riskometer rating for HDFC Silver FoF?",
    ],
    "benchmark": [
        "What is the benchmark for HDFC Multi Cap Fund?",
        "What is the benchmark for HDFC Small Cap?",
    ],
    "lock_in": [
        "What is the lock-in period for ELSS mutual funds?",
        "Does HDFC Mid-Cap have any lock-in period?",
    ],
    "aum": [
        "What is the AUM of HDFC Top 100 Fund?",
        "What is the AUM of HDFC Small Cap?",
    ],
}

DEFAULT_SUGGESTIONS = [
    "What is the TER of HDFC Mid-Cap Opportunities Fund?",
    "What is the exit load for HDFC Small Cap Fund?",
    "What is the benchmark for HDFC Multi Cap Fund?",
]


def generate_followup_suggestions(
    resolution_type: str = "fact_store",
    scheme_id: Optional[str] = None,
    field: Optional[str] = None,
    glossary_id: Optional[str] = None,
    intent: Optional[str] = None,
    is_refusal: bool = False,
) -> List[str]:
    """Generates 2 to 3 grounded, relevant follow-up query suggestions."""
    if is_refusal or intent in ("ADVISORY", "RECOMMENDATION", "COMPARISON", "PROJECTION", "OPINION", "TAX_LEGAL"):
        return [
            "What is the TER of HDFC Mid-Cap Opportunities Fund?",
            "What is the exit load for HDFC Small Cap Fund?",
            "What is the lock-in period for ELSS mutual funds?",
        ]

    if intent in ("HELP", "SMALLTALK"):
        return [
            "What is the TER of HDFC Top 100 Fund?",
            "What is the minimum SIP for HDFC Multi Cap Fund?",
            "Explain exit load",
        ]

    # 1. Scheme-specific metric answers
    if scheme_id and scheme_id in SCHEME_REGISTRY:
        if field and field in SCHEME_FIELD_SUGGESTIONS:
            return SCHEME_FIELD_SUGGESTIONS[field][:3]
        return [
            "What is the TER of this fund?",
            "What is the exit load for this fund?",
            "What is the minimum SIP for this fund?",
        ]

    # 2. Glossary definition answers
    if (resolution_type == "glossary" or field) and (glossary_id or field):
        gid = glossary_id or field
        if gid in GLOSSARY_FOLLOWUPS:
            return GLOSSARY_FOLLOWUPS[gid][:3]

    # 3. Disambiguation / Clarification
    if resolution_type == "clarification":
        return [
            "What is the TER of HDFC Small Cap?",
            "What is the exit load for HDFC Mid-Cap?",
            "What is the benchmark for HDFC Top 100?",
        ]

    # 4. Out of scope / Unsupported plan
    if resolution_type in ("not_found", "out_of_scope", "unsupported_plan", "external_amc"):
        return [
            "What is the TER of HDFC Small Cap (Direct - Growth)?",
            "What is the exit load for HDFC Top 100?",
            "What schemes are supported?",
        ]

    return DEFAULT_SUGGESTIONS[:3]
