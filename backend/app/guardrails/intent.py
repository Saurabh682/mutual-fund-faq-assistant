"""Intent Classifier for Mutual Fund FAQ Assistant.

Classifies user queries into:
- ADVISORY: Requests for advice, recommendations, stock/fund picking, "should I invest", etc.
- COMPARATIVE: Fund comparisons, rankings, "which is better", "vs".
- PROJECTION: Future return estimates, compounding calculators, "how much will ₹X grow".
- TAX_LEGAL: Tax avoidance, evasion, non-payment of capital gains tax, illegal strategies.
- PROCEDURAL: Step-by-step operations (how to invest, redeem, complete KYC, change mandate).
- FACTUAL: Objective data inquiries (TER, exit load, min SIP, NAV, AUM, riskometer, benchmark, lock-in).
- SMALLTALK: Greetings, bot capabilities, identity questions.
- OUT_OF_SCOPE: Inquiries unrelated to HDFC mutual fund schemes or standard mutual fund investing.

Enforces a strict FAIL-CLOSED policy: any non-factual/advisory indicator marks the query
as a refusal intent (is_refusal=True) to comply with SEBI regulations.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class IntentType(str, Enum):
    FACTUAL = "FACTUAL"
    PROCEDURAL = "PROCEDURAL"
    ADVISORY = "ADVISORY"
    COMPARATIVE = "COMPARATIVE"
    PROJECTION = "PROJECTION"
    TAX_LEGAL = "TAX_LEGAL"
    SMALLTALK = "SMALLTALK"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


REFUSAL_INTENTS = {
    IntentType.ADVISORY.value,
    IntentType.COMPARATIVE.value,
    IntentType.PROJECTION.value,
    IntentType.TAX_LEGAL.value,
}


@dataclass
class IntentResult:
    intent: str
    confidence: float
    is_refusal: bool
    is_compound: bool = False
    secondary_intent: Optional[str] = None
    matched_triggers: List[str] = field(default_factory=list)


# 1. Advisory Trigger Patterns (Strict SEBI compliance - zero unauthorized advice)
ADVISORY_PATTERNS = [
    re.compile(r"\bshould\s+(?:i|we|one|a\s+person)\s+(?:invest|buy|choose|pick|put\s+money|start|enter)\b", re.I),
    re.compile(r"\b(?:is\s+it|would\s+it\s+be)\s+(?:good|safe|advisable|wise|smart|recommended|profitable)\s+(?:to\s+)?(?:invest|buy|enter|choose)\b", re.I),
    re.compile(r"\b(?:recommend|recommendation|suggest|suggestion|advise|advice)\b", re.I),
    re.compile(r"\b(?:best|top|safest|highest\s+yielding|highest\s+return)\s+(?:for|to|fund|scheme|mutual\s+fund|option|investment)\b", re.I),
    re.compile(r"\b(?:is|would\s+be)\s+best\b", re.I),
    re.compile(r"\bhighest\s+(?:yield(?:ing)?|return|cagr|growth)\b", re.I),
    re.compile(r"\b(?:smart|wise|conservative|moderate|aggressive)\s+investor\s+(?:prefer|choose|pick|buy)\b", re.I),
    re.compile(r"\b(?:good\s+time|right\s+time)\s+to\s+(?:invest|buy|enter|start)\b", re.I),
    re.compile(r"\bwhere\s+should\s+i\s+invest\b", re.I),
    re.compile(r"\bhelp\s+me\s+(?:choose|pick|select)\s+(?:a\s+)?(?:fund|scheme)\b", re.I),
    re.compile(r"\bwhich\s+fund\s+is\s+(?:good|better|best|safe)\b", re.I),
    re.compile(r"\bif\s+you\s+had\s+(?:[₹rs]\s*)?\d+", re.I),
    re.compile(r"\bshould\s+i\s+(?:hold|sell|redeem|exit)\b", re.I),
    re.compile(r"\bis\s+(?:this|it)\s+(?:a\s+)?good\s+(?:fund|scheme|investment)\b", re.I),
]

# 2. Comparative Trigger Patterns (Schemes must not be compared or ranked)
COMPARATIVE_PATTERNS = [
    re.compile(r"\b(?:vs|versus)\b", re.I),
    re.compile(r"\bcompare\b", re.I),
    re.compile(r"\bcomparison\b", re.I),
    re.compile(r"\bbetter\s+than\b", re.I),
    re.compile(r"\bbetter\s+performance\b", re.I),
    re.compile(r"\bbetter\b", re.I),
    re.compile(r"\bhigher\s+return\s+than\b", re.I),
    re.compile(r"\bwhich\s+(?:is|one\s+is)\s+better\b", re.I),
    re.compile(r"\bdifference\s+between\b", re.I),
    re.compile(r"\brank\s+(?:these|the)?\s*(?:mutual\s+)?funds\b", re.I),
]

# 3. Projection Trigger Patterns (No future return extrapolations)
PROJECTION_PATTERNS = [
    re.compile(r"\bhow\s+much\s+(?:will|would)\b", re.I),
    re.compile(r"\bgrow\s+to\b", re.I),
    re.compile(r"\bexpected\s+returns?\b", re.I),
    re.compile(r"\bprojected\s+returns?\b", re.I),
    re.compile(r"\bfuture\s+returns?\b", re.I),
    re.compile(r"\breturns\s+in\s+\d+\s+(?:years?|months?|yrs?)\b", re.I),
    re.compile(r"\bcalculate\s+(?:future|my)?\s*(?:returns|growth|wealth)\b", re.I),
    re.compile(r"\bwhat\s+will\s+be\s+the\s+value\b", re.I),
]

# 4. Tax/Legal Evasion Patterns
TAX_LEGAL_PATTERNS = [
    re.compile(r"\btax\s+evasion\b", re.I),
    re.compile(r"\bevade\s+tax\b", re.I),
    re.compile(r"\b(?:without\s+paying|avoid|escape|bypass|evade|not\s+pay|save)\s+(?:any\s+)?(?:capital\s+gains|tax)\b", re.I),
    re.compile(r"\b(?:illegal|black\s+money|money\s+laundering|bypass\s+tax)\b", re.I),
    re.compile(r"\bhide\s+(?:money|income|gains)\b", re.I),
]

# 5. Procedural Query Patterns
PROCEDURAL_PATTERNS = [
    re.compile(r"\bhow\s+(?:to|can\s+i|do\s+i)\s+(?:start\s+(?:a\s+)?sip|invest|redeem|withdraw|switch|change|update|complete|apply)\b", re.I),
    re.compile(r"\b(?:step\s+by\s+step|process\s+to|procedure\s+(?:for|to)|kyc\s+process|documents\s+required)\b", re.I),
    re.compile(r"\bhow\s+can\s+i\s+(?:invest|apply|register|open\s+an\s+account|redeem)\b", re.I),
]

# 6. Smalltalk Patterns
SMALLTALK_PATTERNS = [
    re.compile(r"^\s*(?:hi|hello|hey|good\s+morning|good\s+afternoon|good\s+evening|namaste)\b", re.I),
    re.compile(r"\bwho\s+are\s+you\b", re.I),
    re.compile(r"\bwhat\s+can\s+you\s+do\b", re.I),
    re.compile(r"\b(?:thank\s+you|thanks|bye|goodbye)\b", re.I),
]

# 7. Factual Keywords / Concepts
FACTUAL_KEYWORDS = [
    "ter", "expense ratio", "exit load", "minimum sip", "min sip",
    "minimum lumpsum", "min lumpsum", "minimum investment", "lumpsum",
    "lock-in", "lock in", "riskometer", "risk level", "benchmark",
    "nav", "aum", "fund manager", "category", "fund size",
    "portfolio", "turnover", "as on", "direct", "regular", "growth"
]

MUTUAL_FUND_CONTEXT_KEYWORDS = [
    "fund", "scheme", "hdfc", "sip", "nav", "aum", "ter", "load",
    "investment", "invest", "portfolio", "amfi", "sebi", "units"
]


def classify_intent(query: str, use_llm_fallback: bool = False) -> IntentResult:
    """Classifies a user query using high-precision regex triggers and a fail-closed policy.

    Args:
        query: User input string.
        use_llm_fallback: Whether to invoke Groq LLM if text matches no rules.

    Returns:
        IntentResult object with intent, confidence, is_refusal, and compound flags.
    """
    clean_query = query.strip()
    matched_triggers: List[str] = []

    # Check factual indicators first to detect compound queries
    has_factual = any(kw in clean_query.lower() for kw in FACTUAL_KEYWORDS)

    # 1. Tax/Legal Evasion check (Highest severity refusal)
    for p in TAX_LEGAL_PATTERNS:
        m = p.search(clean_query)
        if m:
            matched_triggers.append(m.group(0))
    if matched_triggers:
        return IntentResult(
            intent=IntentType.TAX_LEGAL.value,
            confidence=1.0,
            is_refusal=True,
            is_compound=has_factual,
            secondary_intent=IntentType.FACTUAL.value if has_factual else None,
            matched_triggers=matched_triggers,
        )

    # 2. Comparative Check (Schemes must not be compared or ranked)
    for p in COMPARATIVE_PATTERNS:
        m = p.search(clean_query)
        if m:
            matched_triggers.append(m.group(0))
    if matched_triggers:
        return IntentResult(
            intent=IntentType.COMPARATIVE.value,
            confidence=1.0,
            is_refusal=True,
            is_compound=has_factual,
            secondary_intent=IntentType.FACTUAL.value if has_factual else None,
            matched_triggers=matched_triggers,
        )

    # 3. Advisory Check (Fail-closed refusal)
    for p in ADVISORY_PATTERNS:
        m = p.search(clean_query)
        if m:
            matched_triggers.append(m.group(0))
    if matched_triggers:
        return IntentResult(
            intent=IntentType.ADVISORY.value,
            confidence=1.0,
            is_refusal=True,
            is_compound=has_factual,
            secondary_intent=IntentType.FACTUAL.value if has_factual else None,
            matched_triggers=matched_triggers,
        )

    # 4. Projection Check (Fail-closed refusal)
    for p in PROJECTION_PATTERNS:
        m = p.search(clean_query)
        if m:
            matched_triggers.append(m.group(0))
    if matched_triggers:
        return IntentResult(
            intent=IntentType.PROJECTION.value,
            confidence=1.0,
            is_refusal=True,
            is_compound=has_factual,
            secondary_intent=IntentType.FACTUAL.value if has_factual else None,
            matched_triggers=matched_triggers,
        )

    # 5. Smalltalk Check
    for p in SMALLTALK_PATTERNS:
        m = p.search(clean_query)
        if m:
            matched_triggers.append(m.group(0))
    if matched_triggers:
        return IntentResult(
            intent=IntentType.SMALLTALK.value,
            confidence=0.95,
            is_refusal=False,
            is_compound=False,
            matched_triggers=matched_triggers,
        )

    # 6. Procedural Check
    for p in PROCEDURAL_PATTERNS:
        m = p.search(clean_query)
        if m:
            matched_triggers.append(m.group(0))
    if matched_triggers:
        return IntentResult(
            intent=IntentType.PROCEDURAL.value,
            confidence=0.95,
            is_refusal=False,
            is_compound=False,
            matched_triggers=matched_triggers,
        )

    # 7. Factual Check
    if has_factual:
        return IntentResult(
            intent=IntentType.FACTUAL.value,
            confidence=0.95,
            is_refusal=False,
            is_compound=False,
            matched_triggers=["factual_keyword"],
        )

    # 8. Check if mutual fund related
    is_mf_related = any(kw in clean_query.lower() for kw in MUTUAL_FUND_CONTEXT_KEYWORDS)
    if is_mf_related:
        # Default to FACTUAL query for mutual fund terms
        return IntentResult(
            intent=IntentType.FACTUAL.value,
            confidence=0.75,
            is_refusal=False,
            is_compound=False,
            matched_triggers=["mf_context"],
        )

    # 9. Out of Scope
    return IntentResult(
        intent=IntentType.OUT_OF_SCOPE.value,
        confidence=0.90,
        is_refusal=False,
        is_compound=False,
        matched_triggers=["out_of_scope"],
    )
