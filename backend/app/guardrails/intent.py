"""Intent Classification Guardrail for Mutual Fund FAQ Assistant.

Detects prohibited advisory, comparative, projection, and tax/legal evasion queries
under strict SEBI regulatory compliance guidelines, while allowing factual,
educational, and procedural inquiries.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class IntentType(str, Enum):
    FACTUAL = "FACTUAL"
    PROCEDURAL = "PROCEDURAL"
    ADVISORY = "ADVISORY"
    COMPARATIVE = "COMPARATIVE"
    PROJECTION = "PROJECTION"
    TAX_LEGAL = "TAX_LEGAL"
    HELP = "HELP"
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


# 1. Tax/Legal Evasion Patterns (Highest Severity Compliance Gate)
TAX_LEGAL_PATTERNS = [
    re.compile(r"\btax\s+evasion\b", re.I),
    re.compile(r"\bevade\s+(?:ltcg\s+|stcg\s+)?tax\b", re.I),
    re.compile(r"\b(?:without\s+paying|avoid|escape|bypass|evade|not\s+pay|save)\s+(?:any\s+)?(?:paying\s+)?(?:capital\s+gains|tax)\b", re.I),
    re.compile(r"\bavoid\s+(?:paying\s+)?(?:any\s+)?(?:capital\s+gains\s+)?tax\b", re.I),
    re.compile(r"\b(?:don't|do\s+not)\s+have\s+to\s+pay\s+(?:any\s+)?(?:capital\s+gains|tax)\b", re.I),
    re.compile(r"\b(?:illegal|black\s+money|money\s+laundering|bypass\s+tax)\b", re.I),
    re.compile(r"\bhide\s+(?:money|income|gains)\b", re.I),
    re.compile(r"\bhow\s+(?:can\s+an\s+investor|to)\s+(?:legally\s+)?evade\b", re.I),
]

# 2. Projection Trigger Patterns (Zero Return Extrapolations)
PROJECTION_PATTERNS = [
    re.compile(r"\bhow\s+much\s+(?:will|would)\b", re.I),
    re.compile(r"\bgrow\s+to\b", re.I),
    re.compile(r"\bexpected\s+returns?\b", re.I),
    re.compile(r"\bprojected\s+returns?\b", re.I),
    re.compile(r"\bfuture\s+returns?\b", re.I),
    re.compile(r"\breturns\s+in\s+\d+\s+(?:years?|months?|yrs?)\b", re.I),
    re.compile(r"\bcalculate\s+(?:future|my)?\s*(?:returns|growth|wealth|profit)\b", re.I),
    re.compile(r"\bcalculate\s+(?:my\s+)?(?:sip\s+)?(?:maturity|future|returns|corpus|wealth)\b", re.I),
    re.compile(r"\bmaturity\s+value\b", re.I),
    re.compile(r"\bwhat\s+will\s+be\s+the\s+value\b", re.I),
    re.compile(r"\b(?:will|can)\s+.*?\s+(?:double|triple|grow)\b", re.I),
    re.compile(r"\bdouble\s+(?:my\s+)?(?:investment|money)\b", re.I),
    re.compile(r"\bhow\s+much\s+profit\s+will\s+i\s+make\b", re.I),
]

# 3. Comparative Trigger Patterns (Schemes must not be compared or ranked)
COMPARATIVE_PATTERNS = [
    re.compile(r"\b(?:vs|versus)\b", re.I),
    re.compile(r"\bcompare\s+.*?\s+(?:and|with|to)\b", re.I),
    re.compile(r"\bcomparison\s+(?:of|between)\b", re.I),
    re.compile(r"\bbetter\s+than\b", re.I),
    re.compile(r"\bbetter\s+performance\b", re.I),
    re.compile(r"\bhigher\s+returns?\s+than\b", re.I),
    re.compile(r"\bwhich\s+(?:is|one\s+is)\s+better\b", re.I),
    re.compile(r"\bdifference\s+between\s+.*?\s+and\s+", re.I),
    re.compile(r"\brank\s+(?:these|the)?\s*(?:mutual\s+)?funds?\b", re.I),
    re.compile(r"\brate\s+these\s+.*?\s+funds\b", re.I),
    re.compile(r"\bbetween\s+.*?\s+and\s+.*?\s+which\s+(?:one\s+)?(?:has|is|generates?)\b", re.I),
    re.compile(r"\bwhich\s+scheme\s+is\s+safer\s+.*?\s+(?:or|than)\b", re.I),
    re.compile(r"\bcomparison\s+of\s+.*?\s+cagr\b", re.I),
]

# 4. Factual / Procedural Exemptions from Advisory
# Queries matching these explicit slots are factual/procedural even if they contain weak advisory verbs.
ADVISORY_EXEMPTIONS = [
    re.compile(r"\b(?:suggest|recommend|advise)\s+where\s+(?:in\s+the|to\s+find|to\s+download|to\s+check|can\s+an\s+investor|an\s+investor\s+can)\b", re.I),
    re.compile(r"\badvise\s+(?:me\s+)?(?:on\s+what|what|whether|if)\s+(?:the\s+)?(?:official\s+)?(?:benchmark|ter|expense\s+ratio|exit\s+load|nav|minimum\s+sip|fund\s+manager|as_of|date)\b", re.I),
    re.compile(r"\bhow\s+does\s+sebi\s+recommend\b", re.I),
    re.compile(r"\bsebi\s+(?:recommend|recommended|guidelines?|rules?)\b", re.I),
    re.compile(r"\bshould\s+i\s+enter\s+(?:[₹rs]\s*)?\d+\s+or\s+(?:[₹rs]\s*)?\d+\s+as\s+(?:minimum|min\s+sip|sip\s+amount)\b", re.I),
    re.compile(r"\bhow\s+do\s+i\s+enter\s+(?:a\s+)?sip\s+amount\b", re.I),
    re.compile(r"\bis\s+the\s+exit\s+load\s+safe\s+from\s+change\b", re.I),
    re.compile(r"\bwhat\s+does\s+(?:the\s+)?riskometer\s+say\s+about\s+high\s+risk\b", re.I),
    re.compile(r"\bis\s+it\s+safe\s+to\s+assume\s+(?:the\s+)?lock[\s-]?in\b", re.I),
    re.compile(r"\bwould\s+it\s+be\s+wise\s+to\s+check\s+exit\s+load\b", re.I),
    re.compile(r"\bwhat\s+is\s+(?:a\s+good|the\s+best)\s+(?:way|place)\s+to\s+(?:verify|check)\b", re.I),
    re.compile(r"\bis\s+it\s+better\s+to\s+check\s+nav\s+(?:daily|monthly)\b", re.I),
    re.compile(r"\bhow\s+should\s+one\s+find\s+the\s+fund\s+manager\b", re.I),
    re.compile(r"\bwhat\s+does\s+high\s+risk\s+signify\b", re.I),
    re.compile(r"\b(?:recommend|suggest|advise)\s+(?:the\s+)?(?:official\s+|standard\s+|best\s+)?(?:document|procedure|source|section|method|process|way)\b", re.I),
    re.compile(r"\b(?:advise|suggest)\s+(?:me\s+)?(?:on\s+)?(?:what|whether|where|if)\s+.*?\s+(?:minimum|sip|ter|expense\s+ratio|exit\s+load|nav|lock[\s-]?in|benchmark|manager|tenure|turnover|riskometer)\b", re.I),
    re.compile(r"\b(?:suggest|recommend|advise)\s+what\s+(?:the\s+)?(?:lock[\s-]?in|minimum|sip|ter|nav|benchmark|exit\s+load)\b", re.I),
]

# 5. Advisory Trigger Patterns (Strict SEBI compliance - zero unauthorized advice)
ADVISORY_PATTERNS = [
    # Strong signals (zero-tolerance investment recommendation requests)
    re.compile(r"\bshould\s+(?:i|we|one|a\s+person|they)\s+(?:invest|buy|choose|pick|put\s+money|purchase|allocate|sell|exit|hold)\b", re.I),
    re.compile(r"\b(?:is\s+it|would\s+it\s+be)\s+(?:good|safe|advisable|wise|smart|recommended|profitable)\s+(?:to\s+)?(?:invest|buy|choose|purchase|allocate|put\s+money)\b", re.I),
    re.compile(r"\b(?:where\s+should\s+i\s+invest|which\s+fund\s+is\s+(?:good|better|best|safe|advisable|suitable))\b", re.I),
    re.compile(r"\bhelp\s+me\s+(?:choose|pick|select|decide)\s+(?:a\s+)?(?:fund|scheme|portfolio|investment)\b", re.I),
    re.compile(r"\b(?:what\s+is\s+)?(?:the\s+)?(?:best|top|safest)\s+(?:mutual\s+)?(?:fund|scheme)\b", re.I),
    re.compile(r"\bwhich\s+(?:is\s+)?(?:the\s+)?(?:best|top|safest)\s+(?:mutual\s+)?(?:fund|scheme)\b", re.I),
    re.compile(r"\b(?:best|top|safest)\s+(?:scheme|fund)\s+in\s+\d{4}\b", re.I),
    re.compile(r"\b(?:which\s+.*?\s+)?(?:is\s+)?best\s+for\s+(?:a\s+)?(?:student|senior|beginner|retiree|investor|wealth|retirement)\b", re.I),
    re.compile(r"\b(?:best|top|safest|highest|lowest)\s+(?:yield(?:ing)?|return|returns|cagr|performing|performance|growth)\b", re.I),
    re.compile(r"\bwhich\s+(?:fund|scheme)\s+gives\s+(?:the\s+)?(?:highest|best|top|maximum)\b", re.I),
    re.compile(r"\b(?:smart|wise|conservative|moderate|aggressive)\s+investor\s+(?:prefer|choose|pick|buy|invest)\b", re.I),
    re.compile(r"\b(?:good|right|best)\s+time\s+to\s+(?:invest|buy|start\s+investing|enter(?:\s+the\s+market|\s+[a-z0-9\s-]+)?)\b", re.I),
    re.compile(r"\bif\s+you\s+had\s+(?:[₹rs]\s*)?\d+", re.I),
    re.compile(r"\bshould\s+i\s+(?:hold|sell|redeem|exit)\b", re.I),
    re.compile(r"\bis\s+.*?\s+(?:a\s+)?(?:safe|good|advisable|smart|suitable)\s+(?:investment|fund|option\s+to\s+buy)\b", re.I),
    re.compile(r"\b(?:is\s+)?(?:most\s+)?(?:suitable|appropriate|recommended|safe|good|ideal)\s+(?:for\s+)?(?:a\s+)?(?:senior|beginner|retiree|investor|capital\s+protection|student|tech\s+investor|young)\b", re.I),
    re.compile(r"\b(?:which\s+(?:fund|scheme)\s+is\s+(?:the\s+)?safest|safest\s+(?:among|fund|scheme))\b", re.I),
    re.compile(r"\b(?:financial|investment|portfolio)\s+(?:advice|advisory|guidance|recommendation|planning|proposal)\b", re.I),
    re.compile(r"\b(?:give|provide)\s+(?:me\s+)?(?:financial|investment|personal)\s+advice\b", re.I),
    re.compile(r"\b(?:tell\s+me\s+where\s+to\s+invest|which\s+one\s+would\s+it\s+be\b)", re.I),
    re.compile(r"\b(?:do\s+you\s+agree\s+with\s+(?:this|my)\s+(?:financial\s+)?advisor|agree\s+with\s+this\s+recommendation)\b", re.I),
    re.compile(r"\ballocate\s+\d+%\s+to\b", re.I),
    re.compile(r"\bhypothetically\s+.*?\s+which\s+scheme\s+should\b", re.I),
    re.compile(r"\bwhich\s+scheme\s+would\s+you\s+pick\b", re.I),
    re.compile(r"\bopinion\s+on\s+whether\s+.*?\s+is\s+(?:currently\s+)?(?:overvalued|undervalued)\b", re.I),
    re.compile(r"\bwhich\s+mutual\s+fund\s+will\s+give\s+me\s+higher\s+returns\b", re.I),
    re.compile(r"\bput\s+money\s+in\s+only\s+one\s+fund\b", re.I),
    re.compile(r"\bputting\s+all\s+(?:my\s+)?(?:monthly\s+)?savings\s+into\b", re.I),
    re.compile(r"\bpersonal\s+advice\b", re.I),
    re.compile(r"\blowest\s+downside\s+risk\b", re.I),
    re.compile(r"\bwait\s+for\s+a\s+dip\b", re.I),
    re.compile(r"\b(?:is\s+it\s+)?advisable\s+to\s+(?:exit|enter|invest|switch|buy|sell|redeem)\b", re.I),
    re.compile(r"\b(?:suggest|recommend|build|create)\s+(?:an?\s+)?(?:ideal|good|best|diversified|model)?\s*(?:mutual\s+fund\s+)?portfolio\b", re.I),

    # Weak verbs paired with advisory slots
    re.compile(r"\b(?:recommend|suggest|advise)\s+(?:me\s+)?(?:a|an|any|which|some)?\s*(?:[a-z0-9-]+\s+)*(?:fund|scheme|portfolio|stock|investment|option\s+to\s+invest|to\s+invest|to\s+buy|buying|putting\s+money)\b", re.I),
    re.compile(r"\b(?:recommendation|suggestion|advice)\s+on\s+(?:which|what\s+to\s+buy|investing|fund|scheme)\b", re.I),
    re.compile(r"\b(?:would\s+you\s+advise|do\s+you\s+advise)\s+(?:investing|buying|putting\s+money|allocating)\b", re.I),
    re.compile(r"\b(?:can\s+you\s+recommend|can\s+you\s+suggest|do\s+you\s+recommend)\s+(?:[a-z0-9\s-]+)?\s+(?:for\s+investment|for\s+investing|for\s+returns|for\s+my\s+portfolio|for\s+diversification|as\s+a\s+hedge)\b", re.I),
    re.compile(r"\badvise\s+whether\s+(?:i\s+should\s+)?choose\s+(?:growth|idcw)\b", re.I),
]

# 6. Procedural Query Patterns
PROCEDURAL_PATTERNS = [
    re.compile(r"\bhow\s+(?:to|can\s+i|do\s+i)\s+(?:start\s+(?:a\s+)?sip|invest|redeem|withdraw|switch|change|update|complete|apply|download|get|obtain|set\s+up|pause|track)\b", re.I),
    re.compile(r"\b(?:step\s+by\s+step|process\s+to|procedure\s+(?:for|to)|kyc\s+process|kyc\s+documents|kyc\s+verification|documents\s+required|autopay|bank\s+mandate|e[\s-]?nach)\b", re.I),
    re.compile(r"\bhow\s+can\s+i\s+(?:invest|apply|register|open\s+an\s+account|redeem|download|switch)\b", re.I),
    re.compile(r"\b(?:capital\s+gains?|tax\s+statement|p&l\s+statement|account\s+statement|kyc|cut[\s-]?off\s+time|nav\s+cut[\s-]?off)\b", re.I),
    re.compile(r"\b(?:elss\s+lock[\s-]?in|lock[\s-]?in\s+(?:period\s+)?(?:for\s+)?elss|sebi\s+riskometer|sebi\s+categorization)\b", re.I),
    re.compile(r"\b(?:insufficient\s+funds?|sip\s+bounce|failed\s+sip|pause\s+sip|bank\s+update|settlement\s+cycle|order\s+status|track\s+order)\b", re.I),
]

# 7. Help / Capabilities Query Patterns
HELP_PATTERNS = [
    re.compile(r"^\s*[\?!.,;~]+\s*$"),
    re.compile(r"^\s*(?:what\s+to\s+ask|how\s+to\s+ask|can\s+i\s+ask|to\s+ask|ask)\s*\?*\s*$", re.I),
    re.compile(r"\bwhat\s+(?:else\s+)?(?:can|should|could|do)\s+(?:i|we|you)\s+(?:ask|query|tell|know|answer|do)\b", re.I),
    re.compile(r"^\s*what\s+else\s*[?!.]*\s*$", re.I),
    re.compile(r"\bwhat\s+(?:else\s+)?(?:questions?|topics?|features?|categories?)\b", re.I),
    re.compile(r"\bwhat\s+schemes?\s+(?:do\s+you\s+have|are\s+supported|are\s+available|do\s+you\s+know)\b", re.I),
    re.compile(r"^\s*(?:help|guide|topics?|features?|capabilities|sample\s+questions?|example\s+questions?|how\s+to\s+use|options?|suggestions?|menu)\s*[?!.]*\s*$", re.I),
    re.compile(r"^\s*(?:what\s+next|what\s+now|what\s+more|more|next)\s*[?!.]*\s*$", re.I),
]

# 8. Smalltalk Patterns
SMALLTALK_PATTERNS = [
    re.compile(r"^\s*(?:hi|hello|hey|good\s+morning|good\s+afternoon|good\s+evening|namaste)\b", re.I),
    re.compile(r"\bwho\s+are\s+you\b", re.I),
    re.compile(r"\b(?:thank\s+you|thanks|bye|goodbye)\b", re.I),
]

# 9. Factual Keywords / Concepts
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

    # 2. Projection Check (Fail-closed refusal)
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

    # 3. Comparative Check (Schemes must not be compared or ranked)
    is_educational_comparison = bool(re.search(
        r"\bdifference\s+between\s+(?:direct\s+and\s+regular|regular\s+and\s+direct|growth\s+and\s+idcw|idcw\s+and\s+growth|sip\s+and\s+lump[\s-]?sum|lump[\s-]?sum\s+and\s+sip)\b",
        clean_query,
        re.I
    ))
    if not is_educational_comparison:
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

    # Check if this query qualifies for an explicit factual exemption from advisory
    is_exempt_from_advisory = any(p.search(clean_query) for p in ADVISORY_EXEMPTIONS)

    # 4. Advisory Check (Fail-closed refusal unless explicitly exempted by a factual slot)
    if not is_exempt_from_advisory:
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

    # 5. Help / Capabilities Check
    for p in HELP_PATTERNS:
        m = p.search(clean_query)
        if m:
            matched_triggers.append(m.group(0))
    if matched_triggers:
        return IntentResult(
            intent=IntentType.HELP.value,
            confidence=0.98,
            is_refusal=False,
            is_compound=False,
            matched_triggers=matched_triggers,
        )

    # 6. Smalltalk Check
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

    # 7. Procedural Check
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

    # 8. Factual Check
    if has_factual:
        return IntentResult(
            intent=IntentType.FACTUAL.value,
            confidence=0.95,
            is_refusal=False,
            is_compound=False,
            matched_triggers=["factual_keyword"],
        )

    # 9. Check if mutual fund related
    is_mf_related = any(kw in clean_query.lower() for kw in MUTUAL_FUND_CONTEXT_KEYWORDS)
    if is_mf_related:
        return IntentResult(
            intent=IntentType.FACTUAL.value,
            confidence=0.75,
            is_refusal=False,
            is_compound=False,
            matched_triggers=["mf_context"],
        )

    # 10. Out of Scope
    return IntentResult(
        intent=IntentType.OUT_OF_SCOPE.value,
        confidence=0.90,
        is_refusal=False,
        is_compound=False,
        matched_triggers=["out_of_scope"],
    )
