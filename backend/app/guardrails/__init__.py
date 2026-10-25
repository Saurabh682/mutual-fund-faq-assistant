"""Guardrail and Compliance Firewall Layer.

Components:
- PII Firewall (scan_pii, verhoeff_validate): Scans and redacts financial PII, credentials, folios.
- Intent Classifier (classify_intent): Classifies queries with fail-closed refusal rules.
- Refusal Engine (generate_refusal): Produces deterministic contract-compliant refusals without LLM.
"""

from app.guardrails.pii import (
    PII_SECURITY_WARNING,
    scan_pii,
    verhoeff_checksum,
    verhoeff_validate,
)
from app.guardrails.intent import (
    IntentResult,
    IntentType,
    REFUSAL_INTENTS,
    classify_intent,
)
from app.guardrails.refusal import (
    CANONICAL_LINKS,
    REFUSAL_TEMPLATES,
    generate_compound_refusal,
    generate_refusal,
    get_default_corpus_date,
)

__all__ = [
    "scan_pii",
    "verhoeff_validate",
    "verhoeff_checksum",
    "PII_SECURITY_WARNING",
    "classify_intent",
    "IntentType",
    "IntentResult",
    "REFUSAL_INTENTS",
    "generate_refusal",
    "generate_compound_refusal",
    "REFUSAL_TEMPLATES",
    "CANONICAL_LINKS",
    "get_default_corpus_date",
]
