"""Constrained LLM Synthesizer for Mutual Fund FAQ Assistant.

Orchestrates answer generation using Groq API (Qwen 27B / Llama 70B),
passing drafts through the 5-point Output Contract Validator with up to 2
targeted repair iterations before failing closed to a verified fallback.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from groq import Groq

from app.core.config import settings
from app.guardrails.refusal import CANONICAL_LINKS, get_default_corpus_date
from app.guardrails.validator import (
    ValidationResult,
    safe_contract_fallback,
    validate_response,
)
from app.rag.prompts import (
    SYSTEM_SYNTHESIS_PROMPT,
    build_repair_prompt,
    build_synthesis_user_prompt,
)

logger = logging.getLogger(__name__)


@dataclass
class SynthesisResult:
    text: str
    sentence_count: int
    citation_url: str
    last_updated: str
    rendered: str
    is_valid: bool
    repaired: bool = False
    repair_count: int = 0
    violation_reasons: List[str] = field(default_factory=list)
    raw_draft: str = ""


class ConstrainedSynthesizer:
    """Orchestrates LLM generation with strict output contract enforcement."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_repairs: int = 2,
    ):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL
        self.max_repairs = max_repairs

        self.client: Optional[Groq] = None
        if self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize Groq client: {e}")

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Executes a single constrained completion call to Groq."""
        if not self.client:
            raise RuntimeError("Groq client not configured or API key missing.")

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
            max_tokens=120,
        )
        content = resp.choices[0].message.content or ""
        return content.strip()

    def synthesize(
        self,
        query: str,
        context_chunks: List[Any],
        primary_url: Optional[str] = None,
        doc_date: Optional[str] = None,
    ) -> SynthesisResult:
        """Synthesizes a contract-compliant factual answer from retrieved chunks.

        Args:
            query: User question.
            context_chunks: Retrieved context chunks.
            primary_url: Verified canonical source URL.
            doc_date: Document version date.

        Returns:
            SynthesisResult guaranteed to meet all contract rules.
        """
        citation_url = primary_url or CANONICAL_LINKS["ADVISORY"]
        effective_date = doc_date or get_default_corpus_date()

        # Fail closed immediately if no context is provided
        if not context_chunks:
            val_res = validate_response(
                "NOT_FOUND", context_chunks=[], primary_url=citation_url, doc_date=effective_date
            )
            return SynthesisResult(
                text=val_res.text,
                sentence_count=val_res.sentence_count,
                citation_url=val_res.citation_url,
                last_updated=val_res.last_updated,
                rendered=val_res.rendered,
                is_valid=True,
                repaired=False,
                repair_count=0,
                violation_reasons=val_res.violation_reasons,
                raw_draft="NOT_FOUND",
            )

        # 1. Primary LLM Generation
        raw_draft = ""
        try:
            user_prompt = build_synthesis_user_prompt(query, context_chunks)
            raw_draft = self._call_llm(SYSTEM_SYNTHESIS_PROMPT, user_prompt)
        except Exception as e:
            logger.warning(f"Groq generation failed: {e}. Falling back to safe response.")
            fallback = safe_contract_fallback(citation_url, effective_date, reason=f"API_ERROR_{type(e).__name__}")
            return SynthesisResult(
                text=fallback.text,
                sentence_count=fallback.sentence_count,
                citation_url=fallback.citation_url,
                last_updated=fallback.last_updated,
                rendered=fallback.rendered,
                is_valid=True,
                repaired=True,
                repair_count=0,
                violation_reasons=fallback.violation_reasons,
                raw_draft=raw_draft,
            )

        # 2. Contract Validation Gate
        val_res = validate_response(
            raw_draft, context_chunks, primary_url=citation_url, doc_date=effective_date
        )

        if val_res.is_valid:
            return SynthesisResult(
                text=val_res.text,
                sentence_count=val_res.sentence_count,
                citation_url=val_res.citation_url,
                last_updated=val_res.last_updated,
                rendered=val_res.rendered,
                is_valid=True,
                repaired=val_res.repaired,
                repair_count=0,
                violation_reasons=val_res.violation_reasons,
                raw_draft=raw_draft,
            )

        # 3. Targeted Repair Loop (up to max_repairs attempts)
        current_draft = raw_draft
        repair_attempts = 0

        for attempt in range(1, self.max_repairs + 1):
            repair_attempts = attempt
            violation_summary = "; ".join(val_res.violation_reasons)
            repair_prompt = build_repair_prompt(
                query, context_chunks, current_draft, violation_summary
            )

            try:
                current_draft = self._call_llm(SYSTEM_SYNTHESIS_PROMPT, repair_prompt)
            except Exception as e:
                logger.warning(f"Repair attempt {attempt} failed: {e}")
                break

            val_res = validate_response(
                current_draft,
                context_chunks,
                primary_url=citation_url,
                doc_date=effective_date,
            )

            if val_res.is_valid:
                return SynthesisResult(
                    text=val_res.text,
                    sentence_count=val_res.sentence_count,
                    citation_url=val_res.citation_url,
                    last_updated=val_res.last_updated,
                    rendered=val_res.rendered,
                    is_valid=True,
                    repaired=True,
                    repair_count=repair_attempts,
                    violation_reasons=val_res.violation_reasons,
                    raw_draft=current_draft,
                )

        # 4. Fail Closed Fallback if repairs still fail contract
        fallback = safe_contract_fallback(citation_url, effective_date, reason="REPAIR_EXHAUSTED")
        return SynthesisResult(
            text=fallback.text,
            sentence_count=fallback.sentence_count,
            citation_url=fallback.citation_url,
            last_updated=fallback.last_updated,
            rendered=fallback.rendered,
            is_valid=True,
            repaired=True,
            repair_count=repair_attempts,
            violation_reasons=fallback.violation_reasons,
            raw_draft=current_draft,
        )
