"""Constrained LLM Synthesizer for Mutual Fund FAQ Assistant.

Orchestrates answer generation using Groq API (Qwen 27B / Llama 70B),
passing drafts through the 5-point Output Contract Validator with up to 2
targeted repair iterations before failing closed to a verified fallback.
"""

from __future__ import annotations

import logging
import random
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from groq import Groq

from app.core.config import settings
from app.guardrails.refusal import CANONICAL_LINKS, get_default_corpus_date
from app.guardrails.validator import (
    ValidationResult,
    safe_contract_fallback,
    split_sentences,
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
    deadline_fallback_used: bool = False


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
                self.client = Groq(api_key=self.api_key, timeout=1.8, max_retries=0)
            except Exception as e:
                logger.warning(f"Could not initialize Groq client: {e}")

    def _call_llm(self, system_prompt: str, user_prompt: str, deadline_t: float = 0.0) -> str:
        """Executes a single constrained completion call to Groq with rate-limit protection and reasoning_effort: low.

        Advisory queries NEVER reach this path (they are blocked before synthesizer is called).
        On Groq 429/rate-limit error: retries ONCE with jitter (50-150ms) if time_remaining >= 0.3s.
        """
        if not self.client:
            raise RuntimeError("Groq client not configured or API key missing.")

        token_ceiling = 200 if ("oss" in self.model or "120b" in self.model) else 120

        call_kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.0,
            "max_tokens": token_ceiling,
        }
        if "oss" in self.model or "120b" in self.model:
            call_kwargs["extra_body"] = {"reasoning_effort": "low"}

        def _do_create() -> str:
            try:
                resp = self.client.chat.completions.create(**call_kwargs)
            except Exception as e:
                if "reasoning_effort" in str(e):
                    call_kwargs.pop("extra_body", None)
                    resp = self.client.chat.completions.create(**call_kwargs)
                else:
                    raise e
            return (resp.choices[0].message.content or "").strip()

        try:
            return _do_create()
        except Exception as e:
            is_rate_limit = ("429" in str(e) or "rate_limit" in str(e).lower() or "rate limit" in str(e).lower())
            if is_rate_limit:
                time_remaining = deadline_t - time.perf_counter() if deadline_t else 0.3
                if time_remaining >= 0.3:
                    # Exactly ONE retry with jitter 50-150ms
                    time.sleep(random.uniform(0.05, 0.15))
                    return _do_create()
                # Not enough time left; let outer deadline handler fire
                raise
            raise

    def synthesize(
        self,
        query: str,
        context_chunks: List[Any],
        primary_url: Optional[str] = None,
        doc_date: Optional[str] = None,
        procedural: bool = False,
    ) -> SynthesisResult:
        """Synthesizes a contract-compliant factual answer from retrieved chunks.
        start_t = time.perf_counter()

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
        start_t = time.perf_counter()

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

        # HARD PRE-LLM INVARIANT (Task 1): Re-run decision-request check on query
        from app.guardrails.intent_head import classify_intent_head
        head_cat, _, _, _ = classify_intent_head(query)
        # procedural=True: classify_intent already ran the residual head veto, the raw query would re-refuse "How to invest in X"
        if head_cat == "DECISION_REQUEST" and not procedural:
            logger.warning(f"Hard pre-LLM invariant fired: blocked decision query '{query}' from Groq LLM.")
            refusal_body = "I can only provide objective, factual information regarding mutual fund schemes and cannot offer investment advice, comparisons, or recommendations."
            rendered_refusal = f"{refusal_body}\n\nSource: {CANONICAL_LINKS['ADVISORY']}\nLast updated from sources: {effective_date}"
            return SynthesisResult(
                text=refusal_body,
                sentence_count=1,
                citation_url=CANONICAL_LINKS["ADVISORY"],
                last_updated=effective_date,
                rendered=rendered_refusal,
                is_valid=True,
                repaired=False,
                repair_count=0,
                violation_reasons=["HARD_PRE_LLM_INVARIANT_DECISION_BLOCKED"],
                raw_draft=refusal_body,
                deadline_fallback_used=False,
            )

        # 1. Primary LLM Generation with strict 1.8s deadline
        raw_draft = ""
        groq_t0 = time.perf_counter()
        deadline_triggered = False
        try:
            if time.perf_counter() - start_t >= 1.8:
                deadline_triggered = True
                raise TimeoutError("Deadline exceeded prior to Groq call")
            user_prompt = build_synthesis_user_prompt(query, context_chunks)
            raw_draft = self._call_llm(SYSTEM_SYNTHESIS_PROMPT, user_prompt)
            # Strip any NOT_FOUND token so it never reaches the user
            cleaned_raw = re.sub(r"\bNOT_FOUND\b\.?", "", raw_draft, flags=re.I).strip()
            cleaned_raw = re.sub(r"\s{2,}", " ", cleaned_raw)
            if not cleaned_raw or raw_draft.strip().upper() == "NOT_FOUND":
                fallback = safe_contract_fallback(citation_url, effective_date, reason="NOT_FOUND")
                return SynthesisResult(
                    text=fallback.text,
                    sentence_count=fallback.sentence_count,
                    citation_url=fallback.citation_url,
                    last_updated=fallback.last_updated,
                    rendered=fallback.rendered,
                    is_valid=True,
                    repaired=False,
                    repair_count=0,
                    violation_reasons=fallback.violation_reasons,
                    raw_draft="NOT_FOUND",
                )
            raw_draft = cleaned_raw
        except Exception as e:
            groq_elapsed = (time.perf_counter() - groq_t0) * 1000
            exc_type = type(e).__name__
            is_timeout = isinstance(e, TimeoutError) or "timeout" in str(e).lower() or "deadline" in str(e).lower() or deadline_triggered
            is_rate_limit = ("429" in str(e) or "rate_limit" in str(e).lower() or "ratelimit" in str(e).lower())
            logger.warning(f"Groq call failed with exception {exc_type} ({groq_elapsed:.1f}ms): {e}. Falling back to safe response.")

            if is_timeout:
                extractive_answer = None
                if context_chunks:
                    top_text = context_chunks[0] if isinstance(context_chunks[0], str) else getattr(context_chunks[0], "text", "")
                    first_sent = split_sentences(top_text.split("\n")[0])[0] if top_text else ""
                    if first_sent and len(first_sent) > 20:
                        v_ext = validate_response(first_sent, context_chunks, primary_url=citation_url, doc_date=effective_date)
                        if v_ext.is_valid:
                            extractive_answer = v_ext

                if extractive_answer:
                    return SynthesisResult(
                        text=extractive_answer.text,
                        sentence_count=extractive_answer.sentence_count,
                        citation_url=extractive_answer.citation_url,
                        last_updated=extractive_answer.last_updated,
                        rendered=extractive_answer.rendered,
                        is_valid=True,
                        repaired=True,
                        repair_count=0,
                        violation_reasons=["EXTRACTIVE_TIMEOUT_FALLBACK"],
                        raw_draft=extractive_answer.text,
                        deadline_fallback_used=True,
                    )
                else:
                    timeout_msg = "Please try again shortly."
                    rendered = f"{timeout_msg}\n\nSource: {citation_url}\nLast updated from sources: {effective_date}"
                    return SynthesisResult(
                        text=timeout_msg,
                        sentence_count=1,
                        citation_url=citation_url,
                        last_updated=effective_date,
                        rendered=rendered,
                        is_valid=True,
                        repaired=True,
                        repair_count=0,
                        violation_reasons=[f"DEADLINE_TIMEOUT_{exc_type}"],
                        raw_draft=raw_draft,
                        deadline_fallback_used=True,
                    )

            if is_rate_limit:
                timeout_msg = "Please try again shortly."
                rendered = f"{timeout_msg}\n\nSource: {citation_url}\nLast updated from sources: {effective_date}"
                return SynthesisResult(
                    text=timeout_msg,
                    sentence_count=1,
                    citation_url=citation_url,
                    last_updated=effective_date,
                    rendered=rendered,
                    is_valid=True,
                    repaired=True,
                    repair_count=0,
                    violation_reasons=[f"RATE_LIMIT_{exc_type}"],
                    raw_draft=raw_draft,
                    deadline_fallback_used=True,
                )

            fallback = safe_contract_fallback(citation_url, effective_date, reason=f"API_ERROR_{exc_type}")
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
                deadline_fallback_used=False,
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

        # Fast deterministic truncation: If draft only exceeded sentence count, truncate to 3 sentences in O(1)
        if any("SENTENCE_COUNT" in v or "EXCEEDED" in v for v in val_res.violation_reasons) and not any(
            "BANNED" in v or "HALLUCINATED" in v or "REFUSAL" in v for v in val_res.violation_reasons
        ):
            sents = split_sentences(raw_draft)
            if len(sents) > 3:
                truncated_draft = " ".join(sents[:3])
                val_res_trunc = validate_response(
                    truncated_draft, context_chunks, primary_url=citation_url, doc_date=effective_date
                )
                if val_res_trunc.is_valid:
                    return SynthesisResult(
                        text=val_res_trunc.text,
                        sentence_count=val_res_trunc.sentence_count,
                        citation_url=val_res_trunc.citation_url,
                        last_updated=val_res_trunc.last_updated,
                        rendered=val_res_trunc.rendered,
                        is_valid=True,
                        repaired=True,
                        repair_count=0,
                        violation_reasons=val_res_trunc.violation_reasons,
                        raw_draft=raw_draft,
                    )

        # Hard latency deadline: fail-closed to prevent slow tail latency
        if (time.perf_counter() - start_t) > 1.8:
            logger.info("Latency deadline approaching; returning safe fallback.")
            extractive_answer = None
            if context_chunks:
                top_text = context_chunks[0] if isinstance(context_chunks[0], str) else getattr(context_chunks[0], "text", "")
                first_sent = split_sentences(top_text.split("\n")[0])[0] if top_text else ""
                if first_sent and len(first_sent) > 20:
                    v_ext = validate_response(first_sent, context_chunks, primary_url=citation_url, doc_date=effective_date)
                    if v_ext.is_valid:
                        extractive_answer = v_ext

            if extractive_answer:
                return SynthesisResult(
                    text=extractive_answer.text,
                    sentence_count=extractive_answer.sentence_count,
                    citation_url=extractive_answer.citation_url,
                    last_updated=extractive_answer.last_updated,
                    rendered=extractive_answer.rendered,
                    is_valid=True,
                    repaired=True,
                    repair_count=0,
                    violation_reasons=["EXTRACTIVE_TIMEOUT_FALLBACK"],
                    raw_draft=raw_draft,
                    deadline_fallback_used=True,
                )
            else:
                timeout_msg = "Please try again shortly; real-time verification timed out."
                rendered = f"{timeout_msg}\n\nSource: {citation_url}\nLast updated from sources: {effective_date}"
                return SynthesisResult(
                    text=timeout_msg,
                    sentence_count=1,
                    citation_url=citation_url,
                    last_updated=effective_date,
                    rendered=rendered,
                    is_valid=True,
                    repaired=True,
                    repair_count=0,
                    violation_reasons=["DEADLINE_TIMEOUT"],
                    raw_draft=raw_draft,
                    deadline_fallback_used=True,
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
