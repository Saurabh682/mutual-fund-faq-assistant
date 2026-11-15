"""Entity Resolution Engine for Mutual Fund FAQ Assistant.

Extracts scheme and field entities from user input, resolves pronouns/anaphora
using session state, performs fuzzy matching for typos/abbreviations, and detects
ambiguous queries requiring scheme clarification.
"""

from __future__ import annotations

import difflib
import logging
import re
from dataclasses import dataclass, field as dc_field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)
from app.guardrails.refusal import CANONICAL_LINKS, get_default_corpus_date
from app.guardrails.validator import validate_response
from app.core.schemes import (
    FUND_HOUSES,
    LISTED_NAMES_LIMIT,
    SCHEME_COUNT,
    SCHEME_REGISTRY,
    SCOPE_NAME,
    format_choices,
    fund_house_word_pattern,
    fund_houses_named,
    scheme_label,
)


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
        "who is managing", "managing", "managed by", "fund management",
        "who runs", "who is running", "runs", "lead manager"
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

SUPPORTED_FACT_FIELD_DESCRIPTIONS: Dict[str, str] = {
    "ter_direct": "total expense ratio TER direct plan annual management fee charges ratio",
    "exit_load": "exit load penalty redemption fee premature exit charge duration period",
    "min_sip": "minimum systematic investment plan SIP monthly installment starting sip amount",
    "min_lumpsum": "minimum initial lumpsum investment amount purchase minimum lumpsum deposit",
    "min_additional": "minimum additional purchase investment amount additional purchase",
    "benchmark": "benchmark index tracked target index comparison standard index name tracks",
    "riskometer": "riskometer SEBI risk level rating risk category risk grade meter",
    "nav": "net asset value NAV unit price daily valuation price per unit",
    "aum": "assets under management AUM fund size total corpus asset size portfolio value",
    "lock_in": "lock-in period mandatory holding duration lock in tenure lockin",
    "fund_manager": "fund manager lead manager portfolio manager who manages who is managing",
}

_FIELD_EMBEDDINGS_CACHE: Optional[Dict[str, Any]] = None


def get_field_embeddings() -> Optional[Dict[str, Any]]:
    global _FIELD_EMBEDDINGS_CACHE
    if _FIELD_EMBEDDINGS_CACHE is not None:
        return _FIELD_EMBEDDINGS_CACHE
    try:
        from app.rag.retriever import encode_query
        keys = list(SUPPORTED_FACT_FIELD_DESCRIPTIONS.keys())
        descs = list(SUPPORTED_FACT_FIELD_DESCRIPTIONS.values())
        vecs = encode_query(descs, normalize_embeddings=True)
        _FIELD_EMBEDDINGS_CACHE = {"keys": keys, "vecs": vecs}
        return _FIELD_EMBEDDINGS_CACHE
    except Exception as e:
        logger.warning(f"Could not compute field embeddings: {e}")
        return None


def match_field_by_embedding(clause: str, threshold: float = 0.52) -> Optional[Tuple[str, float]]:
    cache = get_field_embeddings()
    if not cache:
        return None
    try:
        from app.rag.retriever import encode_query
        clean = clause.strip()
        if not clean:
            return None
        q_vec = encode_query(clean, normalize_embeddings=True)
        sims = np.dot(cache["vecs"], q_vec)
        best_idx = int(np.argmax(sims))
        best_score = float(sims[best_idx])
        if best_score >= threshold:
            return (cache["keys"][best_idx], best_score)
        return None
    except Exception as e:
        logger.warning(f"Field embedding matching error: {e}")
        return None

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
    is_amc_out_of_scope: bool = False
    is_multi_scheme_comparison: bool = False
    matched_scheme_ids: List[str] = dc_field(default_factory=list)
    matched_scheme_alias: Optional[str] = None
    matched_field_alias: Optional[str] = None
    # Schemes of different fund houses that go by the same name ("mid cap fund"): ask, never guess
    ambiguous_scheme_ids: List[str] = dc_field(default_factory=list)
    named_fund_house_ids: List[str] = dc_field(default_factory=list)
    # No scheme resolved, but the words look like one fund's name ("ultra short term fund"): offered as options
    suggested_scheme_ids: List[str] = dc_field(default_factory=list)

    @property
    def needs_scheme_choice(self) -> bool:
        """A fund-specific question (a field is named) whose scheme name fits several schemes: ask before any generic answer."""
        return bool(self.ambiguous_scheme_ids and self.field)


def _core_aliases() -> Dict[str, List[str]]:
    """Each scheme's aliases with the fund house prefix removed. They name a scheme only when the fund house is
    named too ("liquid fund of Mahindra"); on their own they are common words ("What is a liquid fund?")."""
    cores: Dict[str, List[str]] = {}
    for sid, info in SCHEME_REGISTRY.items():
        prefixes = sorted(FUND_HOUSES[info["amc"]]["aliases"], key=len, reverse=True)
        found = []
        for alias in info["aliases"]:
            for prefix in prefixes:
                if alias.startswith(prefix + " "):
                    core = alias[len(prefix) + 1:]
                    if core not in info["aliases"] and core not in found:
                        found.append(core)
                    break
        cores[sid] = found
    return cores


_CORE_ALIASES = _core_aliases()


def _normalize(text: str) -> str:
    """Lower case, '&' as 'and', and hyphens or runs of spaces as one space."""
    return re.sub(r"[-\s]+", " ", text.lower().replace("&", " and "))


def resolve_entities(
    query: str, session_scheme_id: Optional[str] = None
) -> EntityResolutionResult:
    """Resolves target scheme and field entities from a user query string.

    Supports exact alias matching, multi-token colloquial variants,
    pronoun/anaphora resolution, and fuzzy string similarity for typos.
    """
    clean_query = query.lower()
    norm_query = _normalize(query)

    # 1. Match Scheme Entity (longest alias wins, one match per scheme)
    named_houses = fund_houses_named(norm_query)
    matches = []  # (scheme_id, alias, (start, end))
    for sid, info in SCHEME_REGISTRY.items():
        aliases = info["aliases"] + (_CORE_ALIASES[sid] if info["amc"] in named_houses else [])
        for alias in sorted(aliases, key=len, reverse=True):
            m = re.search(r"\b" + re.escape(_normalize(alias)) + r"\b", norm_query)
            if m:
                matches.append((sid, alias, m.span()))
                break

    # A query that names a fund house can only mean that fund house's schemes
    if named_houses:
        matches = [m for m in matches if SCHEME_REGISTRY[m[0]]["amc"] in named_houses]
    # "mid cap" inside "large and mid cap fund" is part of the longer name, not a second scheme
    matches = [
        m for m in matches
        if not any(o is not m and o[2] != m[2] and o[2][0] <= m[2][0] and m[2][1] <= o[2][1] for o in matches)
    ]

    ambiguous_scheme_ids: List[str] = []
    if len(matches) > 1 and len({m[2] for m in matches}) == 1:
        # The same words name schemes of several fund houses. Keep the fund house the conversation is about, else ask.
        session_house = SCHEME_REGISTRY.get(session_scheme_id or "", {}).get("amc")
        same_house = [m for m in matches if SCHEME_REGISTRY[m[0]]["amc"] == session_house]
        if len(same_house) == 1:
            matches = same_house
        else:
            ambiguous_scheme_ids = [m[0] for m in matches]
            matches = []

    detected_scheme_id = None
    detected_scheme_alias = None
    matched_scheme_ids = [m[0] for m in matches]
    if matches:
        best = max(matches, key=lambda m: len(m[1]))
        detected_scheme_id, detected_scheme_alias = best[0], best[1]

    # 1b. Fuzzy Matching for Typos & Abbreviations (e.g. 'sml cap', 'midcap opp')
    if not detected_scheme_id and not ambiguous_scheme_ids:
        # Fund house words and "mutual fund" / "AMC" name no scheme: leave them out on both sides, so they cannot
        # make "mahindra manulife amc" look like "mahindra manulife large cap".
        generic = re.compile(
            r"\b(?:" + fund_house_word_pattern() + r"|mutual fund|mutual|mf|amc|asset management(?: company)?|fund house)\b"
        )

        def bare(text: str) -> str:
            return re.sub(r"\s+", " ", generic.sub(" ", text)).strip()

        words = bare(norm_query).split()
        candidate_ngrams = [" ".join(words[i:i + n]) for n in (1, 2, 3) for i in range(len(words) - n + 1)]
        candidate_ngrams = [g for g in candidate_ngrams if len(g) >= 4]

        best_score = 0.0
        best_hits: List[Tuple[str, str]] = []

        for sid, info in SCHEME_REGISTRY.items():
            if named_houses and info["amc"] not in named_houses:
                continue
            for alias in info["aliases"]:
                norm_alias = _normalize(alias)
                core = bare(norm_alias)
                if core != norm_alias and info["amc"] not in named_houses:
                    continue  # a name that includes its fund house counts only when the question names that fund house
                norm_alias = core
                al_w = norm_alias.split()
                for ngram in candidate_ngrams:
                    sm = difflib.SequenceMatcher(None, ngram, norm_alias)
                    # cheap upper bounds first: most pairs are nowhere near the threshold
                    if sm.real_quick_ratio() < 0.78 or sm.quick_ratio() < 0.78:
                        continue
                    sim = sm.ratio()
                    # "flexi cap" must not fuzzy-match "large cap": every word has to be close to its alias word
                    ng_w = ngram.split()
                    if len(ng_w) == len(al_w) and not all(
                        a.startswith(g) or difflib.SequenceMatcher(None, g, a).ratio() >= 0.75
                        for g, a in zip(ng_w, al_w)
                    ):
                        continue
                    if sim >= 0.78:
                        if sim > best_score + 1e-9:
                            best_score, best_hits = sim, [(sid, alias)]
                        elif abs(sim - best_score) <= 1e-9:
                            best_hits.append((sid, alias))

        if best_hits:
            if len({SCHEME_REGISTRY[sid]["amc"] for sid, _ in best_hits} | set()) > 1 and len({a for _, a in best_hits}) == 1:
                # equally close to the same name at two fund houses: ask
                ambiguous_scheme_ids = [sid for sid, _ in best_hits]
            else:
                detected_scheme_id, detected_scheme_alias = best_hits[0]

    suggested_scheme_ids: List[str] = []
    if not detected_scheme_id and not ambiguous_scheme_ids:
        for sid, cores in _CORE_ALIASES.items():
            if any(len(c) >= 5 and re.search(r"\b" + re.escape(_normalize(c)) + r"\b", norm_query) for c in cores):
                suggested_scheme_ids.append(sid)

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

    # 3b. Semantic Field Matching for Unmatched Clauses (Task 5)
    if detected_field is None:
        emb_match = match_field_by_embedding(clean_query, threshold=0.52)
        if emb_match:
            detected_field = emb_match[0]
            if detected_field not in detected_fields:
                detected_fields.append(detected_field)
            detected_field_alias = f"semantic_match:{detected_field}"

    # Structural rule: 2+ schemes named with no supported fact field is a comparison request
    is_multi_scheme_comparison = (len(matched_scheme_ids) >= 2 and not detected_field and not detected_fields)

    # 4. Check External AMC & Ambiguity (EC-ENT-01 & EC-RET-02)
    has_external_amc = any(
        re.search(r"\b" + re.escape(amc) + r"\b", clean_query) for amc in EXTERNAL_AMCS
    )
    if has_external_amc:
        detected_scheme_id = None
        detected_scheme_alias = None
        ambiguous_scheme_ids = []
        suggested_scheme_ids = []

    # Check Unsupported Plan / Option (Regular Plan or IDCW/Dividend)
    is_unsupported_plan = bool(
        re.search(r"\b(?:regular\s+plan|regular\s+growth|regular\s+scheme)\b", clean_query)
        or re.search(r"\b(?:idcw|dividend\s+plan|dividend\s+option|dividend\s+payout)\b", clean_query)
    )

    # AMC-level out-of-scope check (Rule: AMC named, no scheme resolved, no scheme fact field matched)
    is_amc_named = bool(
        re.search(r"\b(?:" + fund_house_word_pattern() + r"|amc|asset\s+management(?:\s+company)?|fund\s+house)\b", clean_query, re.I)
    )
    is_amc_out_of_scope = (
        is_amc_named
        and detected_scheme_id is None
        and not ambiguous_scheme_ids
        and detected_field in (None, "amc_name")
        and not has_external_amc
        and not is_unsupported_plan
    )

    # Ask "which scheme?" only when the field was named outright. A field guessed by meaning
    # alone ("autopay mandate for my SIP" -> min_sip) is usually a process question, not a
    # request for that scheme fact, so it goes on to retrieval instead.
    field_named_explicitly = detected_field is not None and not str(detected_field_alias).startswith("semantic_match:")
    is_ambiguous = bool(ambiguous_scheme_ids) or (
        detected_scheme_id is None
        and field_named_explicitly
        and detected_field != "amc_name"
        and not has_external_amc
        and not is_unsupported_plan
        and not is_amc_out_of_scope
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
        is_amc_out_of_scope=is_amc_out_of_scope,
        is_multi_scheme_comparison=is_multi_scheme_comparison,
        matched_scheme_ids=matched_scheme_ids,
        matched_scheme_alias=detected_scheme_alias,
        matched_field_alias=detected_field_alias,
        ambiguous_scheme_ids=ambiguous_scheme_ids,
        named_fund_house_ids=named_houses,
        suggested_scheme_ids=suggested_scheme_ids,
    )


def _house_site(house_ids: Optional[List[str]]) -> str:
    """The fund house's own site when the question named exactly one, else AMFI's investor page."""
    if house_ids and len(house_ids) == 1 and house_ids[0] in FUND_HOUSES:
        return FUND_HOUSES[house_ids[0]]["website"]
    return CANONICAL_LINKS["ADVISORY"]


def get_unsupported_plan_response(query: Optional[str] = None, house_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """Returns compliant response when user queries Regular plans or IDCW options."""
    doc_date = get_default_corpus_date()
    citation = _house_site(house_ids)
    text = (
        "This assistant strictly indexes Direct Plan (Growth Option) schemes. "
        "Regular plans and IDCW options are not supported per the Groww scheme page. "
        f"Please query Direct Plan (Growth Option) metrics across our {SCHEME_COUNT} supported {SCOPE_NAME} funds."
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
    """Returns compliant response when user asks about a fund house outside the supported ones."""
    doc_date = get_default_corpus_date()
    citation = "https://www.amfiindia.com/investor-corner/knowledge-center"
    amc_label = f"'{detected_amc.title()}'" if detected_amc else "external fund houses"
    text = (
        f"I can only provide records for {SCHEME_COUNT} selected {SCOPE_NAME} Mutual Fund schemes per the Groww scheme page. "
        f"Information regarding {amc_label} is not available in our records. "
        f"You can explore comprehensive scheme information on the AMFI portal."
    )
    val_res = validate_response(text, None, citation, doc_date)
    return {
        "text": val_res.text,
        "citation_url": val_res.citation_url,
        "last_updated": val_res.last_updated,
        "rendered": val_res.rendered,
        "is_external_amc": True,
    }


_FIELD_QUESTIONS = {
    "ter_direct": "What is the expense ratio of {n}?",
    "exit_load": "What is the exit load of {n}?",
    "min_sip": "What is the minimum SIP of {n}?",
    "benchmark": "What is the benchmark of {n}?",
    "riskometer": "What is the riskometer of {n}?",
    "nav": "What is the NAV of {n}?",
    "aum": "What is the AUM of {n}?",
    "lock_in": "What is the lock-in period of {n}?",
    "fund_manager": "Who manages {n}?",
}


def get_disambiguation_response(
    last_updated: Optional[str] = None,
    candidate_ids: Optional[List[str]] = None,
    field: Optional[str] = None,
    house_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """The clarification prompt, with one button-ready option per scheme the user may have meant.

    candidate_ids are the schemes that share the name the user typed; without them the first few schemes are offered.
    Each option's prompt repeats the question the user asked, so one tap answers it.
    """
    in_named_houses = [sid for sid, info in SCHEME_REGISTRY.items() if info["amc"] in (house_ids or [])]
    ids = [c for c in (candidate_ids or in_named_houses or list(SCHEME_REGISTRY)) if c in SCHEME_REGISTRY]
    labels = [scheme_label(SCHEME_REGISTRY[c]) for c in ids]
    if candidate_ids:
        body = f"Please specify which scheme you mean: {format_choices(labels)}."
    else:
        sep = ", for example: " if len(labels) > LISTED_NAMES_LIMIT else ": "
        body = f"Please specify which scheme you are inquiring about{sep}{format_choices(labels)}."
    url = CANONICAL_LINKS["ADVISORY"]
    doc_date = last_updated or get_default_corpus_date()
    val_res = validate_response(body, None, url, doc_date)
    template = _FIELD_QUESTIONS.get(field or "", "Show facts for {n}")
    options = [
        {"id": sid, "label": label, "prompt": template.format(n=label)}
        for sid, label in list(zip(ids, labels))[:LISTED_NAMES_LIMIT]
    ]

    return {
        "text": val_res.text,
        "citation_url": val_res.citation_url,
        "last_updated": val_res.last_updated,
        "rendered": val_res.rendered,
        "is_clarification": True,
        "options": options,
    }


def get_scheme_meta(scheme_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve metadata for a known scheme ID."""
    return SCHEME_REGISTRY.get(scheme_id)


def get_clarification_response(entity_res: "EntityResolution") -> Dict[str, Any]:
    """Clarification for a question whose scheme is unresolved: the schemes that share the name, else the
    ones its words suggest, else the named fund house's, else the first few."""
    return get_disambiguation_response(
        candidate_ids=entity_res.ambiguous_scheme_ids or entity_res.suggested_scheme_ids or None,
        field=entity_res.field,
        house_ids=entity_res.named_fund_house_ids,
    )


def get_amc_out_of_scope_response(last_updated: Optional[str] = None, house_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """Generates deterministic out-of-scope response for AMC-level company inquiries without asking which scheme."""
    body = (
        f"I don't have that information. I can answer questions about TER, exit load, minimum SIP, NAV, AUM, benchmark, riskometer, lock-in and fund manager for {SCHEME_COUNT} {SCOPE_NAME} schemes. "
        "For corporate AMC information, please refer to regulatory filings."
    )
    url = _house_site(house_ids)
    doc_date = last_updated or get_default_corpus_date()
    val_res = validate_response(body, None, url, doc_date)

    return {
        "text": val_res.text,
        "citation_url": val_res.citation_url,
        "last_updated": val_res.last_updated,
        "rendered": val_res.rendered,
        "is_out_of_scope": True,
    }
