"""Intent Classification Guardrail for Mutual Fund FAQ Assistant.

Detects prohibited advisory, comparative, projection, and tax/legal evasion queries
under strict SEBI regulatory compliance guidelines, while allowing factual,
educational, and procedural inquiries.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


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
    # The gap may not cross a decision verb: "advise me whether I should redeem ... given the
    # exit load" must not be exempted.
    re.compile(r"\b(?:advise|suggest)\s+(?:me\s+)?(?:on\s+)?(?:what|whether|where|if)\s+(?:(?!\b(?:should|buy|sell|redeem|invest|switch|hold|exit|choose|pick)\b).)*?\s+(?:minimum|sip|ter|expense\s+ratio|exit\s+load|nav|lock[\s-]?in|benchmark|manager|tenure|turnover|riskometer)\b", re.I),
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
    re.compile(r"\b(?:suitable|ideal|opportune|right|good)\s+moment\s+to\s+(?:invest|buy|sell|exit|redeem|enter|switch)\b", re.I),
    re.compile(r"\b(?:smallest|lowest|least)\s+(?:chance|risk|probability)\s+of\s+losing\b", re.I),
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
    # Account servicing. The object must be a servicing record, so "where do I see which scheme
    # I should buy" is not matched.
    re.compile(r"\bwhere\s+(?:can|do|does)\s+(?:i|an?\s+investor|investors|one|we)\s+(?:track|view|check|see|find|download)\s+(?:the\s+|my\s+|an?\s+|their\s+)?(?:allotment|order|transaction|redemption|account|capital\s+gains?|tax|folio|kyc|mandate|sip\s+status|statement)\b", re.I),
    re.compile(r"\b(?:penny[\s-]?drop|(?:allotment|transaction|redemption|mandate)\s+status)\b", re.I),
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

    # 4. Advisory Check (Fail-closed refusal). An exemption excuses only the words it matched:
    # "Is the exit load safe from change, so should I invest now?" still trips "should I invest".
    advisory_text = clean_query
    for p in ADVISORY_EXEMPTIONS:
        advisory_text = p.sub(" ", advisory_text)
    for p in ADVISORY_PATTERNS:
        m = p.search(advisory_text)
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
        if not is_exempt_from_advisory and (veto := _head_decision_veto(clean_query, has_factual)):
            return veto
        return IntentResult(
            intent=IntentType.PROCEDURAL.value,
            confidence=0.95,
            is_refusal=False,
            is_compound=False,
            matched_triggers=matched_triggers,
        )

    # 8. Factual Check
    if has_factual:
        if not is_exempt_from_advisory and (veto := _head_decision_veto(clean_query, has_factual)):
            return veto
        return IntentResult(
            intent=IntentType.FACTUAL.value,
            confidence=0.95,
            is_refusal=False,
            is_compound=False,
            matched_triggers=["factual_keyword"],
        )

    # 9. Embedding Intent Head (Decision Request vs Information Request)
    if not is_exempt_from_advisory:
        # When the query resolves to a supported lookup (glossary term, procedure, or a
        # scheme + field fact), judge only the residual words. Whole-query scoring refused
        # plain questions like "Define Net Asset Value in mutual fund schemes." Queries that
        # resolve to nothing keep the fail-closed whole-query check.
        head_text = clean_query
        residual = _supported_lookup_residual(clean_query)
        if residual is not None:
            if len(residual.split()) < RESIDUAL_MIN_WORDS:
                return IntentResult(
                    intent=IntentType.FACTUAL.value,
                    confidence=0.85,
                    is_refusal=False,
                    is_compound=False,
                    matched_triggers=["supported_lookup_residual"],
                )
            head_text = residual
        try:
            from app.guardrails.intent_head import classify_intent_head
            head_cat, dec_s, info_s, unsup_s = classify_intent_head(head_text)
            if head_cat == "DECISION_REQUEST":
                return IntentResult(
                    intent=IntentType.ADVISORY.value,
                    confidence=dec_s,
                    is_refusal=True,
                    is_compound=has_factual,
                    secondary_intent=IntentType.FACTUAL.value if has_factual else None,
                    matched_triggers=["intent_head_decision"],
                )
            elif head_cat == "UNSUPPORTED_INFORMATION":
                return IntentResult(
                    intent=IntentType.OUT_OF_SCOPE.value,
                    confidence=unsup_s,
                    is_refusal=False,
                    is_compound=False,
                    matched_triggers=["intent_head_unsupported"],
                )
        except Exception:
            pass

        # 9b. Embedding Prototype Guardrail (Fail closed on un-regexed advisory & projections)
        try:
            from app.guardrails.intent_prototype import classify_clause_prototype
            p_cat, p_adv, p_fac = classify_clause_prototype(head_text)
            if p_cat == "ADVISORY" or (p_cat == "UNCERTAIN" and p_adv >= 0.28 and p_adv > p_fac):
                return IntentResult(
                    intent=IntentType.ADVISORY.value,
                    confidence=p_adv,
                    is_refusal=True,
                    is_compound=has_factual,
                    secondary_intent=IntentType.FACTUAL.value if has_factual else None,
                    matched_triggers=["prototype_advisory"],
                )
        except Exception:
            pass

    # 10. Check if mutual fund related
    is_mf_related = any(kw in clean_query.lower() for kw in MUTUAL_FUND_CONTEXT_KEYWORDS)
    if is_mf_related:
        return IntentResult(
            intent=IntentType.FACTUAL.value,
            confidence=0.75,
            is_refusal=False,
            is_compound=False,
            matched_triggers=["mf_context"],
        )

    # 11. Out of Scope
    return IntentResult(
        intent=IntentType.OUT_OF_SCOPE.value,
        confidence=0.90,
        is_refusal=False,
        is_compound=False,
        matched_triggers=["out_of_scope"],
    )


CLAUSE_SPLIT_PATTERN = re.compile(
    r"(?:[?;.!]+|\s*,\s*(?:and|but|also|plus|or|whether)\s*|\s+(?:and|but|also|plus|whether|while|as well as)\s+(?=(?:should|can|could|would|will|is|are|am|do|does|did|how|what|why|who|where|tell|suggest|recommend|advise|give|help|predict|whether|if|my|your|i|you|he|she|they|we|which|define|explain|describe|list|state|share|provide|mention|show|check|confirm)\b|[a-z0-9\s-]+\b(?:invest|buy|sell|redeem|grow|switch|pick|choose)\b))",
    re.I,
)


def split_clauses(query: str) -> List[str]:
    """Splits a query into constituent clauses on punctuation or clause-level conjunctions.

    Preserves coordinated noun phrases like 'TER and exit load' or 'Direct and Regular plans'.
    """
    parts = CLAUSE_SPLIT_PATTERN.split(query.strip())
    clean_parts: List[str] = []
    for p in parts:
        c = p.strip()
        c = re.sub(r"^[,\s;?.!]+|[,\s;?.!]+$", "", c)
        c = re.sub(r"^(?:also|and|but|plus|whether|or)\s+", "", c, flags=re.I).strip()
        if c:
            clean_parts.append(c)
    return clean_parts


# Single-clause compound check: words that only name the fact being asked about. Whatever
# remains after removing these and the matched scheme/field aliases is the "residual"; a
# residual shorter than RESIDUAL_MIN_WORDS is treated as a plain fact lookup.
RESIDUAL_FILLER_WORDS = frozenset(
    """a an the of for in on is are was what whats what's who whom which does do did tell me show
    give please about its it this that fund funds scheme schemes plan direct growth regular option
    hdfc mf mutual today current currently value amount percentage percent limit period level
    category labeled labelled any has have how much many managers manager handling managing""".split()
)
RESIDUAL_MIN_WORDS = 3
# "if sold in 6 months", "when redeemed within 1 year": the holding period an exit load or
# lock-in depends on. Requires if/when so "sell in 6 months" alone is not stripped.
REDEMPTION_TIMING_PATTERN = re.compile(
    r"\b(?:if|when)\s+(?:it\s+is\s+|i\s+|units\s+are\s+)?(?:sold|redeemed|withdrawn|exited)\s+"
    r"(?:in|within|after|before)\s+\d+\s+(?:days?|months?|years?|yrs?)\b",
    re.I,
)


def _supported_lookup_residual(query: str) -> Optional[str]:
    """Residual text if the query names a procedure, glossary term or scheme+field fact, else None.

    The phrases that named the lookup ("redemption cut-off time", "expense ratio") are removed
    too: left in, they dilute the head's score, and "<decision> considering the redemption
    cut-off time" read as an information request.
    """
    from app.rag.entities import resolve_entities

    try:
        ent = resolve_entities(query)
        text, named_lookup = query, False
        for p in _lookup_phrase_patterns():
            if p.search(text):
                named_lookup = True
                text = p.sub(" ", text)
        if named_lookup or (ent.scheme_id and ent.field):
            return _decision_residual(text, ent)
    except Exception as e:  # fail closed: fall back to whole-query head scoring
        logger.warning(f"Supported-lookup residual failed: {e}")
    return None


_LOOKUP_PHRASE_PATTERNS: Optional[List[Any]] = None


def _lookup_phrase_patterns() -> List[Any]:
    """Patterns that name a supported procedure or glossary term, plus PROCEDURAL_PATTERNS."""
    global _LOOKUP_PHRASE_PATTERNS
    if _LOOKUP_PHRASE_PATTERNS is None:
        from app.rag.glossary import GLOSSARY_DEFINITIONS
        from app.rag.procedures import PROCEDURE_ITEMS

        pats = [
            p
            for item in PROCEDURE_ITEMS
            if item.get("supported") is not False and item.get("status") != "unsupported"
            for p in item["patterns"]
        ]
        pats += [p for item in GLOSSARY_DEFINITIONS for p in item["patterns"]]
        _LOOKUP_PHRASE_PATTERNS = pats + PROCEDURAL_PATTERNS
    return _LOOKUP_PHRASE_PATTERNS


def _head_decision_veto(clean_query: str, has_factual: bool) -> Optional[IntentResult]:
    """Embedding-head check for a decision request hidden in a procedural or factual query.

    Steps 7 and 8 of classify_intent return on a single keyword ("cut-off time", "scheme"),
    which let "Which scheme would you recommend for long term wealth creation?" through as
    FACTUAL. Scores the residual left after removing the lookup phrases; a residual shorter
    than RESIDUAL_MIN_WORDS is a plain lookup and is never vetoed.
    """
    from app.rag.entities import resolve_entities

    try:
        if resolve_entities(clean_query).is_external_amc:
            return None  # answered as out-of-corpus; advisory wording there is caught by rules
        residual = _supported_lookup_residual(clean_query)
        if residual is not None and len(residual.split()) < RESIDUAL_MIN_WORDS:
            return None
        from app.guardrails.intent_head import classify_intent_head

        head_cat, dec_s, info_s, unsup_s = classify_intent_head(residual if residual is not None else clean_query)
    except Exception as e:  # fail closed
        logger.warning(f"Head decision veto failed: {e}")
        head_cat, dec_s, info_s, unsup_s = "DECISION_REQUEST", 0.0, 0.0, 0.0
    if head_cat != "DECISION_REQUEST":
        return None
    # Whole-query scoring (no lookup phrase to strip) needs decision to actually win: the head's
    # fail-closed near-tie refused "Can I switch mutual fund units between two different AMCs
    # directly?" (decision 0.49 vs information 0.52). Leaked advice questions score 0.85+.
    if residual is None and dec_s <= max(info_s, unsup_s):
        return None
    return IntentResult(
        intent=IntentType.ADVISORY.value,
        confidence=dec_s,
        is_refusal=True,
        is_compound=has_factual,
        secondary_intent=IntentType.FACTUAL.value if has_factual else None,
        matched_triggers=["intent_head_decision"],
    )


def _decision_residual(query: str, ent: Any) -> str:
    """Returns the query text left after stripping scheme/field aliases and filler words."""
    from app.rag.entities import FIELD_GLOSSARY, SCHEME_REGISTRY

    text = query.lower()
    aliases = [ent.matched_scheme_alias, ent.matched_field_alias]
    aliases += FIELD_GLOSSARY.get(ent.field or "", [])
    # Only the resolved scheme's aliases: stripping every registry alias turned
    # "shift from large caps to small caps" into "shift from s to s" and hid the decision.
    if ent.scheme_id in SCHEME_REGISTRY:
        aliases += SCHEME_REGISTRY[ent.scheme_id].get("aliases", [])
    # Longest first so "hdfc small cap fund" is removed before "small cap"; whole words only.
    for alias in sorted({a.lower() for a in aliases if a}, key=len, reverse=True):
        text = re.sub(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", " ", text)
    # For exit load / lock-in, "if sold in 6 months" is the condition of the fact itself.
    if ent.field in ("exit_load", "lock_in"):
        text = REDEMPTION_TIMING_PATTERN.sub(" ", text)
    tokens = [w for w in re.findall(r"[a-z0-9₹'-]+", text) if w not in RESIDUAL_FILLER_WORDS]
    return " ".join(tokens)


def classify_clause_level_intent(
    query: str, session_scheme_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Evaluates clause-level intent for compound factual-plus-advisory queries.

    Design:
    1. Splits on sentence punctuation and clause conjunctions.
    2. Identifies if one clause contains a supported fact request (facts.db, procedures, glossary).
    3. If a fact request is extracted, classifies the remaining text (residual clause).
    4. If the residual clause is NOT a supported fact, glossary term, or procedure,
       appends the fixed refusal sentence.
    5. Never calls the LLM when a residual clause exists.
    """
    from app.rag.entities import resolve_entities
    from app.rag.facts import lookup_fact
    from app.rag.procedures import lookup_procedure
    from app.rag.glossary import lookup_glossary
    from app.guardrails.refusal import generate_compound_refusal
    from app.guardrails.validator import split_sentences
    from app.guardrails.intent_head import classify_intent_head

    clauses = split_clauses(query)
    full_ent = resolve_entities(query, session_scheme_id=session_scheme_id)
    active_scheme = full_ent.scheme_id or session_scheme_id

    # If query did not split into >= 2 clauses, check if the full query has a fact AND a decision request
    if len(clauses) < 2:
        if active_scheme and full_ent.field:
            fact_candidate = lookup_fact(query, session_scheme_id=active_scheme)
            if fact_candidate:
                # Classify only what is left once the scheme/field words are removed. Scoring the
                # whole query let short keyword-style fact lookups ("TER for hdfc small cap direct
                # growth") fall inside the head's fail-closed margin and read as DECISION_REQUEST.
                residual = _decision_residual(query, full_ent)
                is_decision = classify_intent(query).is_refusal
                # Explicit exemptions ("would it be wise to check exit load", "suggest where an
                # investor can find ...") mark an information action, not an investment decision;
                # classify_intent already skips its head check for them, so this check does too.
                is_exempt = any(p.search(query) for p in ADVISORY_EXEMPTIONS)
                if not is_decision and not is_exempt and len(residual.split()) >= RESIDUAL_MIN_WORDS:
                    head_cat, *_ = classify_intent_head(residual)
                    is_decision = head_cat == "DECISION_REQUEST"
                if is_decision:
                    raw_text = fact_candidate["text"].split("\n\n")[0]
                    sentences = split_sentences(raw_text)
                    first_sentence = sentences[0] if sentences else raw_text
                    return generate_compound_refusal(
                        factual_sentence=first_sentence,
                        intent=IntentType.ADVISORY.value,
                        citation_url=fact_candidate.get("citation_url") or fact_candidate.get("source_url"),
                        last_updated=fact_candidate.get("last_updated"),
                    )
        return None

    fact_resp = None
    fact_clause_idx = -1

    # First pass: find the supported fact clause
    for idx, c in enumerate(clauses):
        c_ent = resolve_entities(c, session_scheme_id=active_scheme)
        target_scheme = c_ent.scheme_id or active_scheme

        f = lookup_fact(c, session_scheme_id=target_scheme)
        if f:
            fact_resp = f
            fact_clause_idx = idx
            break
        elif not target_scheme:
            p = lookup_procedure(c)
            if p:
                fact_resp = p
                fact_clause_idx = idx
                break
            else:
                g = lookup_glossary(c)
                if g:
                    fact_resp = g
                    fact_clause_idx = idx
                    break

    # If no single clause resolved a fact, but the whole query matches a fact:
    if not fact_resp and active_scheme and full_ent.field:
        fact_resp = lookup_fact(query, session_scheme_id=active_scheme)
        if fact_resp:
            for idx, c in enumerate(clauses):
                c_ent = resolve_entities(c, session_scheme_id=active_scheme)
                if c_ent.field or c_ent.scheme_id:
                    fact_clause_idx = idx
                    break

    if not fact_resp:
        return None

    # Second pass: check the remaining (residual) clauses
    residual_clauses = [c for idx, c in enumerate(clauses) if idx != fact_clause_idx]
    has_unsupported_residual = False

    for rc in residual_clauses:
        clean_rc = rc.strip()
        if not clean_rc:
            continue
        rc_words = [w.lower() for w in clean_rc.split()]
        if len(rc_words) == 1 and rc_words[0] in ("please", "today", "now", "thanks"):
            continue

        rc_ent = resolve_entities(clean_rc, session_scheme_id=active_scheme)
        target_scheme = rc_ent.scheme_id or active_scheme

        # 1. Is it another supported fact?
        rc_fact = lookup_fact(clean_rc, session_scheme_id=target_scheme)
        if rc_fact:
            continue

        # 2. Is it a procedure?
        rc_proc = lookup_procedure(clean_rc)
        if rc_proc:
            continue

        # 3. Is it a glossary term?
        rc_gloss = lookup_glossary(clean_rc)
        if rc_gloss:
            continue

        # 4. Is it a pure anaphoric carrier phrase referring to the same fact?
        carrier_tokens = set("what is it tell me show give where published can you point to the value of".split())
        if all(w in carrier_tokens for w in rc_words):
            continue

        # Otherwise, clean_rc is an unsupported residual clause!
        has_unsupported_residual = True
        break

    if has_unsupported_residual:
        raw_text = fact_resp["text"].split("\n\n")[0]
        sentences = split_sentences(raw_text)
        first_sentence = sentences[0] if sentences else raw_text
        return generate_compound_refusal(
            factual_sentence=first_sentence,
            intent=IntentType.ADVISORY.value,
            citation_url=fact_resp.get("citation_url") or fact_resp.get("source_url"),
            last_updated=fact_resp.get("last_updated"),
        )

    return None
