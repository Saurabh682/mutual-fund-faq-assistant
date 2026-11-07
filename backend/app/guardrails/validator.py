"""Output Contract Validator for Mutual Fund FAQ Assistant.

Enforces the strict 5-point Output Response Contract:
1. Sentence count ceiling (<= 3 sentences) with decimal & currency punctuation protection.
2. Banned evaluative lexicon check (zero opinion words: good, best, safe, lucrative, etc.).
3. Numeric Grounding Verification: All numbers and percentages in LLM drafts must exist verbatim in source context.
4. Programmatic single-citation URL attachment (strips any model-generated URLs).
5. Mandatory date footer invariant: 'Last updated from sources: <YYYY-MM-DD>'.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
import yaml

# Canonical regulatory and educational citation URLs
CANONICAL_LINKS: Dict[str, str] = {
    "ADVISORY": "https://www.amfiindia.com/investor-corner/knowledge-center",
    "COMPARATIVE": "https://www.amfiindia.com/investor-corner/knowledge-center",
    "PROJECTION": "https://www.amfiindia.com/investor-corner/knowledge-center",
    "TAX_LEGAL": "https://www.amfiindia.com/investor-corner/knowledge-center",
    "OUT_OF_SCOPE": "https://www.amfiindia.com/investor-corner/knowledge-center",
    "SMALLTALK": "https://www.amfiindia.com/investor-corner/knowledge-center",
    "HELP": "https://www.amfiindia.com/investor-corner/knowledge-center",
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


# Comprehensive Banned Lexicon (Evaluative, speculative, or advisory words)
BANNED_LEXICON = {
    "good", "great", "best", "better", "safe", "safest", "attractive",
    "lucrative", "recommended", "ideal", "strong", "weak", "should",
    "must invest", "guaranteed", "outperform", "superior", "profitable",
    "promising", "worthwhile", "loss-free", "risk-free", "undervalued",
    "overvalued", "stellar", "phenomenal", "advise", "suggest",
}

# Regex to identify URLs in text (leaves trailing punctuation like period or comma intact)
URL_PATTERN = re.compile(
    r"https?://[^\s\)]+(?<![.,;!?])|www\.[^\s\)]+(?<![.,;!?])|\[.*?\]\(.*?\)",
    re.I,
)

# Regex to identify numbers and percentages (e.g., 100, 0.74%, 20, 1.25, 5,000)
NUMBER_PATTERN = re.compile(r"\b\d+(?:,\d+)*(?:\.\d+)?%?")

# Date footer validation pattern
DATE_FOOTER_PATTERN = re.compile(r"^Last updated from sources: \d{4}-\d{2}-\d{2}$")


@dataclass
class ValidationResult:
    is_valid: bool
    text: str
    sentence_count: int
    citation_url: str
    last_updated: str
    rendered: str
    violation_reasons: List[str] = field(default_factory=list)
    repaired: bool = False


def split_sentences(text: str) -> List[str]:
    """Splits text on sentence boundaries while respecting currency and decimal punctuation.

    Prevents breaking numbers like '₹102.50' into fragments ('₹102' and '50')
    and preserves common abbreviations ('Rs.', 'Mr.', 'e.g.', 'i.e.').
    """
    if not text:
        return []

    # 1. Protect decimal points between digits: e.g. 102.50 -> 102<DOT>50
    cleaned = re.sub(r"(?<=\d)\.(?=\d)", "<DOT>", text)

    # 2. Protect abbreviations: e.g. Rs. -> Rs<ABBR_DOT>
    cleaned = re.sub(
        r"\b(Rs|Mr|Mrs|Ms|Dr|e\.g|i\.e|vs)\.",
        r"\1<ABBR_DOT>",
        cleaned,
        flags=re.IGNORECASE,
    )

    # 3. Split on sentence boundaries (. ! ?) followed by whitespace or end of string
    parts = re.split(r"(?<=[.!?])\s+", cleaned)

    # 4. Restore protected dots
    sentences = []
    for p in parts:
        restored = p.replace("<DOT>", ".").replace("<ABBR_DOT>", ".").strip()
        if restored:
            sentences.append(restored)

    return sentences


def strip_urls(text: str) -> str:
    """Strips any URLs or markdown links generated by the LLM (EC-LLM-03)."""
    clean = URL_PATTERN.sub("", text)
    # Clean up double spaces or orphan punctuation left behind
    clean = re.sub(r"\s{2,}", " ", clean).strip()
    return clean


def extract_normalized_numbers(text: str) -> Tuple[set, set]:
    """Extracts numbers from text and normalizes them for whole-number and float set matching.

    Eliminates substring false-positives (e.g. '0.7%' passing against '0.74%',
    or '1' passing against '100').
    """
    matches = NUMBER_PATTERN.findall(text)
    float_vals: set = set()
    raw_tokens: set = set()

    for m in matches:
        clean_m = m.strip().lower()
        raw_tokens.add(clean_m)
        raw_num = clean_m.replace(",", "").rstrip("%")
        try:
            val = float(raw_num)
            float_vals.add(round(val, 6))
        except ValueError:
            pass

    return float_vals, raw_tokens


def verify_numeric_grounding(
    draft_text: str, context_chunks: List[Any]
) -> Tuple[bool, List[str]]:
    """Verifies that every number or percentage in draft_text exists in source context (EC-LLM-02).

    Returns:
        Tuple of (is_grounded, ungrounded_numbers).
    """
    # Build consolidated context corpus
    corpus_parts = []
    for c in context_chunks:
        if isinstance(c, str):
            corpus_parts.append(c)
        elif isinstance(c, dict):
            corpus_parts.append(c.get("text", ""))
        elif hasattr(c, "text"):
            corpus_parts.append(getattr(c, "text", ""))

    context_str = " ".join(corpus_parts)

    # Extract all numbers from draft
    draft_numbers = NUMBER_PATTERN.findall(draft_text)
    if not draft_numbers:
        return True, []

    ctx_floats, ctx_raw = extract_normalized_numbers(context_str)

    ungrounded = []
    for num in draft_numbers:
        clean_num = num.strip().lower()
        raw_num = clean_num.replace(",", "").rstrip("%")

        # 1. Exact token match in context (e.g. '0.74%' or '15')
        if clean_num in ctx_raw or raw_num in ctx_raw:
            continue

        # 2. Strict float equality (e.g. 0.80 == 0.8, 5000.0 == 5,000)
        try:
            val = round(float(raw_num), 6)
            if val in ctx_floats:
                continue
        except ValueError:
            pass

        # 3. Currency and symbol prefix equivalents (e.g. ₹500 in context matches 500)
        if f"₹{raw_num}" in ctx_raw or f"rs.{raw_num}" in ctx_raw or f"rs. {raw_num}" in ctx_raw:
            continue

        ungrounded.append(num)

    return len(ungrounded) == 0, ungrounded


def check_banned_words(text: str) -> List[str]:
    """Detects banned evaluative or advisory words in draft text."""
    lower_text = text.lower()
    detected = []
    for word in BANNED_LEXICON:
        if re.search(r"\b" + re.escape(word) + r"\b", lower_text):
            detected.append(word)
    return detected


def safe_contract_fallback(
    primary_url: Optional[str] = None,
    doc_date: Optional[str] = None,
    reason: str = "DEFAULT",
) -> ValidationResult:
    """Generates the safe compliant fallback when a model draft violates the contract."""
    body = (
        "Official details regarding this topic can be verified directly in the scheme records."
    )
    url = primary_url or CANONICAL_LINKS["ADVISORY"]
    date_str = normalize_date_footer(doc_date)
    rendered = f"{body}\n\nSource: {url}\nLast updated from sources: {date_str}"

    return ValidationResult(
        is_valid=True,
        text=body,
        sentence_count=1,
        citation_url=url,
        last_updated=date_str,
        rendered=rendered,
        violation_reasons=[f"FALLBACK_{reason}"],
        repaired=True,
    )


def validate_response(
    draft_text: str,
    context_chunks: Optional[List[Any]] = None,
    primary_url: str = CANONICAL_LINKS["ADVISORY"],
    doc_date: Optional[str] = None,
) -> ValidationResult:
    """Executes the full 5-point contract validation gate on model output.

    Args:
        draft_text: Raw output from synthesizer or static template.
        context_chunks: Context chunks supplied to the model (None for deterministic static templates).
        primary_url: Verified canonical URL for the winning scheme or regulatory authority.
        doc_date: Document update timestamp (YYYY-MM-DD).

    Returns:
        ValidationResult with compliant text, sentence count, and programmatic footer.
    """
    effective_date = normalize_date_footer(doc_date)
    clean_draft = draft_text.strip()

    # 0. Handle NOT_FOUND or empty output
    if not clean_draft or clean_draft.upper() == "NOT_FOUND":
        not_found_body = (
            "I could not find official information regarding this topic in our verified "
            "HDFC Mutual Fund records."
        )
        url = CANONICAL_LINKS["ADVISORY"]
        rendered = f"{not_found_body}\n\nSource: {url}\nLast updated from sources: {effective_date}"
        return ValidationResult(
            is_valid=True,
            text=not_found_body,
            sentence_count=1,
            citation_url=url,
            last_updated=effective_date,
            rendered=rendered,
            violation_reasons=["NOT_FOUND_IN_CORPUS"],
        )

    # Separate narrative prose from optional markdown table
    if "\n\n|" in clean_draft:
        parts = clean_draft.split("\n\n|", 1)
        narrative = parts[0].strip()
        table = "|" + parts[1]
    else:
        narrative = clean_draft
        table = None

    # 1. Strip unauthorized model-generated URLs (EC-LLM-03)
    stripped_narrative = strip_urls(narrative)

    # 2. Split sentences and enforce <= 3 sentence ceiling (EC-LLM-01 & EC-VAL-01)
    sentences = split_sentences(stripped_narrative)
    repaired = False
    violation_reasons: List[str] = []

    if len(sentences) > 3:
        sentences = sentences[:3]
        repaired = True
        violation_reasons.append("SENTENCE_CEILING_EXCEEDED_TRUNCATED")

    valid_narrative = " ".join(sentences).strip()
    valid_text = f"{valid_narrative}\n\n{table}" if table else valid_narrative

    # 3. Check for banned evaluative lexicon
    banned_hits = check_banned_words(valid_narrative)
    if banned_hits:
        violation_reasons.append(f"BANNED_WORDS:{','.join(banned_hits)}")

    # 4. Numeric Grounding Verification (EC-LLM-02)
    # Only enforced when context_chunks is provided (dynamic LLM synthesis)
    if context_chunks is not None:
        is_grounded, ungrounded_numbers = verify_numeric_grounding(
            valid_narrative, context_chunks
        )
        if not is_grounded:
            violation_reasons.append(f"UNGROUNDED_NUMBERS:{','.join(ungrounded_numbers)}")

    # If any fatal violation occurred (banned words or ungrounded numbers)
    fatal_violations = [r for r in violation_reasons if not r.startswith("SENTENCE_CEILING")]
    if fatal_violations:
        return ValidationResult(
            is_valid=False,
            text=valid_text,
            sentence_count=len(sentences),
            citation_url=primary_url,
            last_updated=effective_date,
            rendered="",
            violation_reasons=violation_reasons,
            repaired=repaired,
        )

    # 5. Programmatic Citation and Mandatory Date Footer Attachment (EC-VAL-02)
    rendered = f"{valid_text}\n\nSource: {primary_url}\nLast updated from sources: {effective_date}"

    return ValidationResult(
        is_valid=True,
        text=valid_text,
        sentence_count=len(sentences),
        citation_url=primary_url,
        last_updated=effective_date,
        rendered=rendered,
        violation_reasons=violation_reasons,
        repaired=repaired,
    )
