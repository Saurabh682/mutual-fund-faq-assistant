"""Cross-fund factual lookups: one fact for every scheme, shown as a table.

"What is the exit load of all schemes?" and "Which funds have a Very High riskometer?" are lookups of facts the
store already holds. Ranking or recommending ("lowest risk", "best", "cheapest") is not: those get the usual
comparison refusal, plus a pointer to the lookup that is allowed.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from app.core.schemes import SCHEME_REGISTRY, fund_houses_named, scheme_label
from app.guardrails.refusal import generate_refusal
from app.guardrails.validator import normalize_date_footer
from app.rag.entities import resolve_entities
from app.rag.facts import NOT_LISTED, _display_value, get_all_scheme_facts_from_db

CITATION_URL = "https://groww.in/mutual-funds"

# Which fact a question asks for: first match wins, so "risk" is only reached when no sharper phrase matched
_FIELDS = {
    "ter_direct": r"\bter\b|expense ratio|expenses",
    "exit_load": r"exit load",
    "min_sip": r"\bsip\b",
    "min_lumpsum": r"lump ?sum",
    "nav": r"\bnav\b|net asset value",
    "aum": r"\baum\b|fund size|assets under management",
    "benchmark": r"benchmark",
    "fund_manager": r"fund manager|managed by|who manages",
    "lock_in": r"lock[- ]?in",
    "riskometer": r"risk",
}
_TITLES = {
    "ter_direct": "Expense ratio (TER)", "exit_load": "Exit load", "min_sip": "Minimum SIP",
    "min_lumpsum": "Minimum lumpsum", "nav": "NAV", "aum": "AUM", "benchmark": "Benchmark",
    "fund_manager": "Fund manager", "lock_in": "Lock-in", "riskometer": "Riskometer",
}
_SCOPE = re.compile(
    r"\b(?:all|every|each)\b.{0,30}\b(?:funds|schemes)\b|\bwhich\s+(?:funds?|schemes?)\b"
    r"|\b(?:list|show)\b.{0,15}\b(?:funds|schemes)\b|\bacross\b.{0,15}\b(?:funds|schemes)\b"
)
# Wording that asks for a ranking or a recommendation, not for a fact
_JUDGEMENT = re.compile(
    r"\b(?:best|better|top|safest|safer|worst|lowest|highest|cheapest|cheaper|least|most|recommend\w*|suggest\w*"
    r"|should|compar\w*|rank\w*|suitable|ideal|good|outperform\w*|pick|choose)\b"
)
# "least risky among all": a lookup of the extreme riskometer level on the page, worded as data, never as "safest"
_EXTREME = re.compile(r"\b(?:least|lowest|most|highest)\s+risk\w*|\briskiest\b")
_ALL = re.compile(r"\b(?:among|all|every|any|which)\b")
_LEVELS = ["low", "low to moderate", "moderate", "moderately high", "high", "very high"]
_RISK_LEVEL = re.compile(r"\b(very high|moderately high|low to moderate|moderate|low|high)\b(?: risk)?")


def _show(field: str, raw: str) -> str:
    if raw.startswith(NOT_LISTED):
        return "Not listed"
    raw = raw.rstrip(".")
    if field == "ter_direct":
        return raw if raw.endswith("%") else f"{raw}%"
    if field in ("nav", "min_sip", "min_lumpsum"):
        return raw if raw.startswith("₹") else f"₹{raw}"
    return _display_value(field, raw)


def _followups(field: str) -> list[str]:
    others = [f for f in ("riskometer", "exit_load", "min_sip", "ter_direct") if f != field]
    return [f"Show the {_TITLES[f].lower()} of all schemes" for f in others[:3]]


def answer_cross_fund(query: str) -> Optional[Dict[str, Any]]:
    """A ready message payload (type, text, citation_url, last_updated, rendered, followups) or None if this is not a cross-fund question."""
    q = re.sub(r"\bmedium\b", "moderate", query.lower())
    extreme = _EXTREME.search(q)
    level = _RISK_LEVEL.search(q) if "risk" in q and not extreme else None
    if not (_SCOPE.search(q) or ((extreme or level) and _ALL.search(q))):
        return None
    field = "riskometer" if extreme or level else next((f for f, pat in _FIELDS.items() if re.search(pat, q)), None)
    if field is None:
        return None
    # A scheme named in the question makes it a single-fund question ("all the charges for HDFC Small Cap Fund")
    named = resolve_entities(query)
    if named.scheme_id or named.ambiguous_scheme_ids:
        return None

    if not extreme and _JUDGEMENT.search(q):
        refusal = generate_refusal("COMPARATIVE")
        return {
            "type": "refusal", "field": field, "text": refusal["text"], "citation_url": refusal["citation_url"],
            "last_updated": refusal["last_updated"], "rendered": refusal["rendered"],
            "followups": [f"Show the {_TITLES[field].lower()} of all schemes"] + _followups(field)[:2],
        }

    houses = fund_houses_named(q)
    rows = []
    for facts in get_all_scheme_facts_from_db():
        info = SCHEME_REGISTRY[facts["scheme_id"]]
        if houses and info["amc"] not in houses:
            continue
        if field in facts:
            rows.append((scheme_label(info), _show(field, facts[field]["value"]), facts[field]["as_of"]))

    if level:
        want = level.group(1)
        rows = [r for r in rows if r[1].lower().removesuffix(" risk") == want]
    title = _TITLES[field]
    if extreme:
        rows = [r for r in rows if r[1].lower().removesuffix(" risk") in _LEVELS]
        rank = lambda r: _LEVELS.index(r[1].lower().removesuffix(" risk"))
        low = bool(re.search(r"least|lowest", extreme.group()))
        end = (min if low else max)((rank(r) for r in rows), default=None)
        total, rows = len(rows), [r for r in rows if rank(r) == end]
    if not rows:
        body = f"No scheme lists a riskometer of {level.group(1).title()} on its Groww scheme page." if level else (
            f"{title} is not available for these schemes.")
    else:
        if extreme:
            lead = (f"The {'lowest' if low else 'highest'} riskometer level among the {total} schemes is {rows[0][1]}, "
                    f"listed for the {len(rows)} below per each Groww scheme page. "
                    f"The riskometer is SEBI's risk class for a scheme, not a suitability view.")
        else:
            scope = f"the {len(rows)} schemes" if not level else f"the {len(rows)} schemes rated {level.group(1).title()} Risk"
            lead = f"{title} across {scope}, per each Groww scheme page."
        table = "\n".join(f"| {name} | {value} |" for name, value, _ in rows)
        body = f"{lead}\n\n| Scheme | {title} |\n| --- | --- |\n{table}"
    date = normalize_date_footer(max((r[2] for r in rows), default=None))
    return {
        "type": "fact_store", "field": field, "text": body, "citation_url": CITATION_URL, "last_updated": date,
        "rendered": f"{body}\n\nSource: {CITATION_URL}\nLast updated from sources: {date}",
        "followups": _followups(field),
    }
