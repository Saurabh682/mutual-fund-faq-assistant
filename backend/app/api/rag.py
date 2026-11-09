"""RAG, Entity Resolution, and Fact Store API Router."""

from __future__ import annotations

import re
import time
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.guardrails.pii import PII_SECURITY_WARNING, scan_pii
from app.guardrails.intent import classify_intent, classify_clause_level_intent
from app.guardrails.refusal import (
    CANONICAL_LINKS,
    generate_refusal,
    generate_help_response,
    get_default_corpus_date,
)
from app.guardrails.validator import split_sentences
from app.rag.entities import (
    get_disambiguation_response,
    get_external_amc_response,
    get_unsupported_plan_response,
    resolve_entities,
)
from app.rag.facts import lookup_fact, get_all_facts_for_scheme
from app.rag.glossary import lookup_glossary
from app.rag.procedures import lookup_procedure
from app.rag.followups import generate_followup_suggestions
from app.rag.retriever import HybridRetriever, get_not_found_response
from app.rag.synthesizer import ConstrainedSynthesizer
from app.schemas.rag import RetrievalQueryRequest, RetrievalQueryResponse
from app.schemas.synthesis import SynthesisQueryRequest, SynthesisQueryResponse

router = APIRouter(prefix="/api/v1/rag", tags=["RAG & Retrieval"])
_retriever = HybridRetriever()
_synthesizer = ConstrainedSynthesizer()


@router.post("/retrieve", response_model=RetrievalQueryResponse)
def retrieve_query(request: RetrievalQueryRequest):
    """Executes the complete retrieval pipeline:

    1. Scans for PII (returns 400 on detection).
    2. Classifies intent (returns deterministic refusal if advisory/comparative).
    3. Resolves entities (returns clarification if scheme is ambiguous).
    4. Fast O(1) Structured Fact Path via facts.db (sub-50ms).
    5. Hybrid Dense + Lexical RRF Retrieval across ChromaDB & BM25 with metadata pre-filtering.
    6. Triggers safe out-of-corpus fallback if confidence < tau.
    """
    t0 = time.perf_counter()

    # 1. PII Firewall
    has_pii, detected_types, redacted = scan_pii(request.query)
    if has_pii:
        doc_date = get_default_corpus_date()
        citation = CANONICAL_LINKS["ADVISORY"]
        rendered_warning = (
            f"{PII_SECURITY_WARNING}\n\n"
            f"Source: {citation}\n"
            f"Last updated from sources: {doc_date}"
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "PII_DETECTED",
                "message": PII_SECURITY_WARNING,
                "detected_types": detected_types,
                "redacted_text": redacted,
                "rendered": rendered_warning,
            },
        )

    # 1b. Clause-Level Intent Check for Compound Factual-plus-Advisory Queries
    compound_resp = classify_clause_level_intent(request.query, session_scheme_id=request.session_scheme_id)
    if compound_resp:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return RetrievalQueryResponse(
            query=request.query,
            resolution_type="compound",
            scheme_id=None,
            scheme_name=None,
            field=None,
            text=compound_resp["text"],
            citation_url=compound_resp["citation_url"],
            last_updated=compound_resp["last_updated"],
            rendered=compound_resp["rendered"],
            chunks=[],
            latency_ms=elapsed_ms,
        )

    # 2. Intent Classifier (Compliance Firewall)
    intent_res = classify_intent(request.query)
    if intent_res.is_refusal:
        refusal = generate_refusal(intent_res.intent)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return RetrievalQueryResponse(
            query=request.query,
            resolution_type="refusal",
            scheme_id=None,
            scheme_name=None,
            field=None,
            text=refusal["text"],
            citation_url=refusal["citation_url"],
            last_updated=refusal["last_updated"],
            rendered=refusal["rendered"],
            chunks=[],
            latency_ms=elapsed_ms,
        )

    # 2b. Help / Capabilities Stage
    if intent_res.intent in ("HELP", "SMALLTALK"):
        help_resp = generate_help_response()
        elapsed_ms = (time.perf_counter() - t0) * 1000
        sentences = split_sentences(help_resp["text"])
        return SynthesisQueryResponse(
            query=request.query,
            resolution_type="help",
            scheme_id=None,
            scheme_name=None,
            field=None,
            text=help_resp["text"],
            sentence_count=len(sentences),
            citation_url=help_resp["citation_url"],
            last_updated=help_resp["last_updated"],
            rendered=help_resp["rendered"],
            repaired=False,
            repair_count=0,
            chunks=[],
            latency_ms=elapsed_ms,
        )

    # 3. Entity Resolution
    entity_res = resolve_entities(request.query, session_scheme_id=request.session_scheme_id)

    # Structural comparison rule (Task 1): 2+ schemes named with no supported fact field
    if entity_res.is_multi_scheme_comparison:
        refusal = generate_refusal("COMPARATIVE")
        elapsed_ms = (time.perf_counter() - t0) * 1000
        sentences = split_sentences(refusal["text"])
        followups = generate_followup_suggestions(intent="COMPARATIVE", is_refusal=True)
        return SynthesisQueryResponse(
            query=request.query,
            resolution_type="refusal",
            scheme_id=None,
            scheme_name=None,
            field=None,
            text=refusal["text"],
            sentence_count=len(sentences),
            citation_url=refusal["citation_url"],
            last_updated=refusal["last_updated"],
            rendered=refusal["rendered"],
            repaired=False,
            repair_count=0,
            chunks=[],
            latency_ms=elapsed_ms,
            suggested_followups=followups,
        )

    # Unsupported Plan check (Regular Plan, IDCW)
    if entity_res.is_unsupported_plan:
        plan_resp = get_unsupported_plan_response(request.query)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return RetrievalQueryResponse(
            query=request.query,
            resolution_type="unsupported_plan",
            scheme_id=entity_res.scheme_id,
            scheme_name=entity_res.scheme_name,
            field=entity_res.field,
            text=plan_resp["text"],
            citation_url=plan_resp["citation_url"],
            last_updated=plan_resp["last_updated"],
            rendered=plan_resp["rendered"],
            chunks=[],
            latency_ms=elapsed_ms,
        )

    # External AMC check (strictly out-of-corpus)
    if entity_res.is_external_amc:
        external_resp = get_external_amc_response(request.query)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return RetrievalQueryResponse(
            query=request.query,
            resolution_type="external_amc",
            scheme_id=None,
            scheme_name=None,
            field=entity_res.field,
            text=external_resp["text"],
            citation_url=external_resp["citation_url"],
            last_updated=external_resp["last_updated"],
            rendered=external_resp["rendered"],
            chunks=[],
            latency_ms=elapsed_ms,
        )

    # Non-scheme procedures and glossary routing
    if entity_res.scheme_id is None:
        proc_match = lookup_procedure(request.query)
        if proc_match:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            return RetrievalQueryResponse(
                query=request.query,
                resolution_type="fact_store",
                scheme_id=None,
                scheme_name=None,
                field="procedure",
                text=proc_match["text"],
                citation_url=proc_match["citation_url"],
                last_updated=proc_match["last_updated"],
                rendered=proc_match["rendered"],
                chunks=[],
                latency_ms=elapsed_ms,
            )

        glossary_match = lookup_glossary(request.query)
        if glossary_match:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            sentences = split_sentences(glossary_match["text"])
            followups = generate_followup_suggestions(
                scheme_id=None,
                field=glossary_match.get("field"),
                intent="FACTUAL",
            )
            return RetrievalQueryResponse(
                query=request.query,
                resolution_type="fact_store",
                scheme_id=None,
                scheme_name=None,
                field=glossary_match.get("field"),
                text=glossary_match["text"],
                citation_url=glossary_match["citation_url"],
                last_updated=glossary_match["last_updated"],
                rendered=glossary_match["rendered"],
                chunks=[],
                latency_ms=elapsed_ms,
            )

    # AMC-level out-of-scope check (Rule: AMC named, no scheme, no supported topic)
    if entity_res.is_amc_out_of_scope:
        from app.rag.entities import get_amc_out_of_scope_response
        amc_resp = get_amc_out_of_scope_response()
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return RetrievalQueryResponse(
            query=request.query,
            resolution_type="not_found",
            scheme_id=None,
            scheme_name=None,
            field=None,
            text=amc_resp["text"],
            citation_url=amc_resp["citation_url"],
            last_updated=amc_resp["last_updated"],
            rendered=amc_resp["rendered"],
            chunks=[],
            latency_ms=elapsed_ms,
        )

    # Ambiguity check (EC-ENT-01)
    # AMC-level out-of-scope check (Rule: AMC named, no scheme, no supported topic)
    if entity_res.is_amc_out_of_scope:
        from app.rag.entities import get_amc_out_of_scope_response
        amc_resp = get_amc_out_of_scope_response()
        elapsed_ms = (time.perf_counter() - t0) * 1000
        sentences = split_sentences(amc_resp["text"])
        return SynthesisQueryResponse(
            query=request.query,
            resolution_type="out_of_scope",
            scheme_id=None,
            scheme_name=None,
            field=None,
            text=amc_resp["text"],
            sentence_count=len(sentences),
            citation_url=amc_resp["citation_url"],
            last_updated=amc_resp["last_updated"],
            rendered=amc_resp["rendered"],
            repaired=False,
            repair_count=0,
            chunks=[],
            latency_ms=elapsed_ms,
            suggested_followups=[],
        )

    if entity_res.is_ambiguous:
        clarification = get_disambiguation_response()
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return RetrievalQueryResponse(
            query=request.query,
            resolution_type="clarification",
            scheme_id=None,
            scheme_name=None,
            field=entity_res.field,
            text=clarification["text"],
            citation_url=clarification["citation_url"],
            last_updated=clarification["last_updated"],
            rendered=clarification["rendered"],
            chunks=[],
            latency_ms=elapsed_ms,
        )

    # 4. Structured Fact Store Path (O(1) SQLite fast path)
    fact_resp = lookup_fact(request.query, session_scheme_id=request.session_scheme_id)
    if fact_resp:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return RetrievalQueryResponse(
            query=request.query,
            resolution_type="fact_store",
            scheme_id=fact_resp.get("scheme_id"),
            scheme_name=entity_res.scheme_name,
            field=fact_resp.get("field"),
            text=fact_resp["text"],
            citation_url=fact_resp["citation_url"],
            last_updated=fact_resp["last_updated"],
            rendered=fact_resp["rendered"],
            chunks=[],
            latency_ms=elapsed_ms,
        )

    # 5. Hybrid Retrieval Path (ChromaDB + BM25 + RRF)
    retrieval_res = _retriever.search(
        query=request.query,
        scheme_id=entity_res.scheme_id,
        top_k=request.top_k,
    )

    elapsed_ms = (time.perf_counter() - t0) * 1000

    if retrieval_res.is_out_of_corpus or not retrieval_res.chunks:
        not_found = get_not_found_response()
        return RetrievalQueryResponse(
            query=request.query,
            resolution_type="not_found",
            scheme_id=entity_res.scheme_id,
            scheme_name=entity_res.scheme_name,
            field=entity_res.field,
            text=not_found["text"],
            citation_url=not_found["citation_url"],
            last_updated=not_found["last_updated"],
            rendered=not_found["rendered"],
            chunks=[],
            latency_ms=elapsed_ms,
        )

    top_chunk = retrieval_res.chunks[0]
    chunk_details = [
        {
            "chunk_id": c.chunk_id,
            "text": c.text,
            "metadata": c.metadata,
            "score": c.score,
            "dense_sim": c.dense_sim,
            "bm25_score": c.bm25_score,
        }
        for c in retrieval_res.chunks
    ]

    rendered_text = f"{top_chunk.text}\n\nSource: {retrieval_res.primary_citation_url}\nLast updated from sources: {get_default_corpus_date()}"

    return RetrievalQueryResponse(
        query=request.query,
        resolution_type="hybrid_retrieval",
        scheme_id=entity_res.scheme_id,
        scheme_name=entity_res.scheme_name,
        field=entity_res.field,
        text=top_chunk.text,
        citation_url=retrieval_res.primary_citation_url,
        last_updated=get_default_corpus_date(),
        rendered=rendered_text,
        chunks=chunk_details,
        latency_ms=elapsed_ms,
    )


@router.post("/ask", response_model=SynthesisQueryResponse)
def ask_query(request: SynthesisQueryRequest):
    """Executes the complete end-to-end question answering pipeline:

    1. Scans for PII -> returns immediate 400 with warning.
    2. Classifies intent -> returns deterministic compliance refusal if advisory/comparative.
    3. Resolves entities -> returns clarification if scheme target is ambiguous.
    4. Structured Fact Store -> instant O(1) SQLite path for canonical metrics (< 50ms).
    5. Hybrid Retrieval -> retrieves top chunks with scheme pre-filtering.
    6. Safe Out-of-Corpus Fallback -> triggers when similarity is below confidence threshold.
    7. Constrained Synthesis -> Groq LLM synthesis validated against the 5-point contract
       with automatic repair loop (<= 3 sentences, zero banned words, grounded numbers, single URL).
    """
    t0 = time.perf_counter()

    # 1. PII Firewall
    has_pii, detected_types, redacted = scan_pii(request.query)
    if has_pii:
        doc_date = get_default_corpus_date()
        citation = CANONICAL_LINKS["ADVISORY"]
        rendered_warning = (
            f"{PII_SECURITY_WARNING}\n\n"
            f"Source: {citation}\n"
            f"Last updated from sources: {doc_date}"
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "PII_DETECTED",
                "message": PII_SECURITY_WARNING,
                "detected_types": detected_types,
                "redacted_text": redacted,
                "rendered": rendered_warning,
            },
        )

    # 1b. Clause-Level Intent Check for Compound Factual-plus-Advisory Queries
    compound_resp = classify_clause_level_intent(request.query, session_scheme_id=request.session_scheme_id)
    if compound_resp:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        sentences = split_sentences(compound_resp["text"])
        followups = generate_followup_suggestions(intent=compound_resp.get("intent", "ADVISORY"), is_refusal=True)
        return SynthesisQueryResponse(
            query=request.query,
            resolution_type="compound",
            scheme_id=None,
            scheme_name=None,
            field=None,
            text=compound_resp["text"],
            sentence_count=len(sentences),
            citation_url=compound_resp["citation_url"],
            last_updated=compound_resp["last_updated"],
            rendered=compound_resp["rendered"],
            repaired=False,
            repair_count=0,
            chunks=[],
            latency_ms=elapsed_ms,
            suggested_followups=followups,
        )

    # 2. Intent Classifier
    intent_res = classify_intent(request.query)
    if intent_res.is_refusal:
        refusal = generate_refusal(intent_res.intent)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        sentences = split_sentences(refusal["text"])
        followups = generate_followup_suggestions(intent=intent_res.intent, is_refusal=True)
        return SynthesisQueryResponse(
            query=request.query,
            resolution_type="refusal",
            scheme_id=None,
            scheme_name=None,
            field=None,
            text=refusal["text"],
            sentence_count=len(sentences),
            citation_url=refusal["citation_url"],
            last_updated=refusal["last_updated"],
            rendered=refusal["rendered"],
            repaired=False,
            repair_count=0,
            chunks=[],
            latency_ms=elapsed_ms,
            suggested_followups=followups,
        )

    # 2b. Help / Capabilities Stage
    if intent_res.intent in ("HELP", "SMALLTALK"):
        help_resp = generate_help_response()
        elapsed_ms = (time.perf_counter() - t0) * 1000
        sentences = split_sentences(help_resp["text"])
        followups = generate_followup_suggestions(intent=intent_res.intent)
        return SynthesisQueryResponse(
            query=request.query,
            resolution_type="help",
            scheme_id=None,
            scheme_name=None,
            field=None,
            text=help_resp["text"],
            sentence_count=len(sentences),
            citation_url=help_resp["citation_url"],
            last_updated=help_resp["last_updated"],
            rendered=help_resp["rendered"],
            repaired=False,
            repair_count=0,
            chunks=[],
            latency_ms=elapsed_ms,
            suggested_followups=followups,
        )

    # 3. Entity Resolution
    entity_res = resolve_entities(request.query, session_scheme_id=request.session_scheme_id)

    # Structural comparison rule (Task 1): 2+ schemes named with no supported fact field
    if entity_res.is_multi_scheme_comparison:
        refusal = generate_refusal("COMPARATIVE")
        elapsed_ms = (time.perf_counter() - t0) * 1000
        sentences = split_sentences(refusal["text"])
        followups = generate_followup_suggestions(intent="COMPARATIVE", is_refusal=True)
        return SynthesisQueryResponse(
            query=request.query,
            resolution_type="refusal",
            scheme_id=None,
            scheme_name=None,
            field=None,
            text=refusal["text"],
            sentence_count=len(sentences),
            citation_url=refusal["citation_url"],
            last_updated=refusal["last_updated"],
            rendered=refusal["rendered"],
            repaired=False,
            repair_count=0,
            chunks=[],
            latency_ms=elapsed_ms,
            suggested_followups=followups,
        )

    # Unsupported Plan check (Regular Plan, IDCW)
    if entity_res.is_unsupported_plan:
        plan_resp = get_unsupported_plan_response(request.query)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        sentences = split_sentences(plan_resp["text"])
        followups = generate_followup_suggestions(
            scheme_id=entity_res.scheme_id,
            field=entity_res.field,
            intent="FACTUAL",
            is_refusal=True,
        )
        return SynthesisQueryResponse(
            query=request.query,
            resolution_type="unsupported_plan",
            scheme_id=entity_res.scheme_id,
            scheme_name=entity_res.scheme_name,
            field=entity_res.field,
            text=plan_resp["text"],
            sentence_count=len(sentences),
            citation_url=plan_resp["citation_url"],
            last_updated=plan_resp["last_updated"],
            rendered=plan_resp["rendered"],
            repaired=False,
            repair_count=0,
            chunks=[],
            latency_ms=elapsed_ms,
            suggested_followups=followups,
        )

    # External AMC check (strictly out-of-corpus)
    if entity_res.is_external_amc:
        external_resp = get_external_amc_response(request.query)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        sentences = split_sentences(external_resp["text"])
        followups = generate_followup_suggestions(
            scheme_id=None,
            field=entity_res.field,
            intent="FACTUAL",
            is_refusal=True,
        )
        return SynthesisQueryResponse(
            query=request.query,
            resolution_type="external_amc",
            scheme_id=None,
            scheme_name=None,
            field=entity_res.field,
            text=external_resp["text"],
            sentence_count=len(sentences),
            citation_url=external_resp["citation_url"],
            last_updated=external_resp["last_updated"],
            rendered=external_resp["rendered"],
            repaired=False,
            repair_count=0,
            chunks=[],
            latency_ms=elapsed_ms,
            suggested_followups=followups,
        )

    # Non-scheme procedures and glossary routing
    if entity_res.scheme_id is None:
        proc_match = lookup_procedure(request.query)
        if proc_match:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            sentences = split_sentences(proc_match["text"])
            followups = generate_followup_suggestions(field="procedure")
            return SynthesisQueryResponse(
                query=request.query,
                resolution_type="fact_store",
                scheme_id=None,
                scheme_name=None,
                field="procedure",
                text=proc_match["text"],
                sentence_count=len(sentences),
                citation_url=proc_match["citation_url"],
                last_updated=proc_match["last_updated"],
                rendered=proc_match["rendered"],
                repaired=False,
                repair_count=0,
                chunks=[],
                latency_ms=elapsed_ms,
                suggested_followups=followups,
            )

        glossary_match = lookup_glossary(request.query)
        if glossary_match:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            sentences = split_sentences(glossary_match["text"])
            followups = generate_followup_suggestions(field=glossary_match.get("field"))
            return SynthesisQueryResponse(
                query=request.query,
                resolution_type="fact_store",
                scheme_id=None,
                scheme_name=None,
                field=glossary_match.get("field"),
                text=glossary_match["text"],
                sentence_count=len(sentences),
                citation_url=glossary_match["citation_url"],
                last_updated=glossary_match["last_updated"],
                rendered=glossary_match["rendered"],
                repaired=False,
                repair_count=0,
                chunks=[],
                latency_ms=elapsed_ms,
                suggested_followups=followups,
            )

    # AMC-level out-of-scope check (Rule: AMC named, no scheme, no supported topic)
    if entity_res.is_amc_out_of_scope:
        from app.rag.entities import get_amc_out_of_scope_response
        amc_resp = get_amc_out_of_scope_response()
        elapsed_ms = (time.perf_counter() - t0) * 1000
        sentences = split_sentences(amc_resp["text"])
        return SynthesisQueryResponse(
            query=request.query,
            resolution_type="out_of_scope",
            scheme_id=None,
            scheme_name=None,
            field=None,
            text=amc_resp["text"],
            sentence_count=len(sentences),
            citation_url=amc_resp["citation_url"],
            last_updated=amc_resp["last_updated"],
            rendered=amc_resp["rendered"],
            repaired=False,
            repair_count=0,
            chunks=[],
            latency_ms=elapsed_ms,
            suggested_followups=[],
        )

    if entity_res.is_ambiguous:
        clarification = get_disambiguation_response()
        elapsed_ms = (time.perf_counter() - t0) * 1000
        sentences = split_sentences(clarification["text"])
        followups = generate_followup_suggestions(intent="HELP")
        return SynthesisQueryResponse(
            query=request.query,
            resolution_type="clarification",
            scheme_id=None,
            scheme_name=None,
            field=entity_res.field,
            text=clarification["text"],
            sentence_count=len(sentences),
            citation_url=clarification["citation_url"],
            last_updated=clarification["last_updated"],
            rendered=clarification["rendered"],
            repaired=False,
            repair_count=0,
            chunks=[],
            latency_ms=elapsed_ms,
            suggested_followups=followups,
        )

    # 4. Structured Fact Store Fast Path
    fact_resp = lookup_fact(request.query, session_scheme_id=request.session_scheme_id)
    if fact_resp:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        sentences = split_sentences(fact_resp["text"])
        followups = generate_followup_suggestions(
            scheme_id=fact_resp.get("scheme_id"),
            field=fact_resp.get("field"),
            intent="FACTUAL",
        )
        return SynthesisQueryResponse(
            query=request.query,
            resolution_type="fact_store",
            scheme_id=fact_resp.get("scheme_id"),
            scheme_name=entity_res.scheme_name,
            field=fact_resp.get("field"),
            text=fact_resp["text"],
            sentence_count=len(sentences),
            citation_url=fact_resp["citation_url"],
            last_updated=fact_resp["last_updated"],
            rendered=fact_resp["rendered"],
            repaired=False,
            repair_count=0,
            chunks=[],
            latency_ms=elapsed_ms,
            suggested_followups=followups,
        )

    # 5. Hybrid Retrieval
    retrieval_res = _retriever.search(
        query=request.query,
        scheme_id=entity_res.scheme_id,
        top_k=4,
    )

    if retrieval_res.is_out_of_corpus or not retrieval_res.chunks:
        not_found = get_not_found_response()
        elapsed_ms = (time.perf_counter() - t0) * 1000
        sentences = split_sentences(not_found["text"])
        followups = generate_followup_suggestions(
            scheme_id=entity_res.scheme_id,
            field=entity_res.field,
            is_refusal=True,
        )
        return SynthesisQueryResponse(
            query=request.query,
            resolution_type="not_found",
            scheme_id=entity_res.scheme_id,
            scheme_name=entity_res.scheme_name,
            field=entity_res.field,
            text=not_found["text"],
            sentence_count=len(sentences),
            citation_url=not_found["citation_url"],
            last_updated=not_found["last_updated"],
            rendered=not_found["rendered"],
            repaired=False,
            repair_count=0,
            chunks=[],
            latency_ms=elapsed_ms,
            suggested_followups=followups,
        )

    # HARD PRE-LLM INVARIANT (Task 1 & Task 2):
    # Re-run decision-request check on query and residual clause immediately before Groq call
    from app.guardrails.intent_head import classify_intent_head
    head_cat, sd, si, su = classify_intent_head(request.query)
    if head_cat == "DECISION_REQUEST":
        refusal = generate_refusal("ADVISORY")
        elapsed_ms = (time.perf_counter() - t0) * 1000
        sentences = split_sentences(refusal["text"])
        followups = generate_followup_suggestions(intent="ADVISORY", is_refusal=True)
        return SynthesisQueryResponse(
            query=request.query,
            resolution_type="refusal",
            scheme_id=None,
            scheme_name=None,
            field=None,
            text=refusal["text"],
            sentence_count=len(sentences),
            citation_url=refusal["citation_url"],
            last_updated=refusal["last_updated"],
            rendered=refusal["rendered"],
            repaired=False,
            repair_count=0,
            chunks=[],
            latency_ms=elapsed_ms,
            suggested_followups=followups,
        )

    if head_cat == "UNSUPPORTED_INFORMATION":
        not_found = get_not_found_response()
        elapsed_ms = (time.perf_counter() - t0) * 1000
        sentences = split_sentences(not_found["text"])
        followups = generate_followup_suggestions(
            scheme_id=entity_res.scheme_id,
            field=entity_res.field,
            is_refusal=True,
        )
        return SynthesisQueryResponse(
            query=request.query,
            resolution_type="not_found",
            scheme_id=entity_res.scheme_id,
            scheme_name=entity_res.scheme_name,
            field=entity_res.field,
            text=not_found["text"],
            sentence_count=len(sentences),
            citation_url=not_found["citation_url"],
            last_updated=not_found["last_updated"],
            rendered=not_found["rendered"],
            repaired=False,
            repair_count=0,
            chunks=[],
            latency_ms=elapsed_ms,
            suggested_followups=followups,
        )

    # 6. Constrained LLM Synthesis with Output Contract Validation
    context_texts = [c.text for c in retrieval_res.chunks]
    if entity_res.scheme_id:
        scheme_facts = get_all_facts_for_scheme(entity_res.scheme_id)
        if scheme_facts:
            fact_summary = f"Verified AMC Facts: TER={scheme_facts.get('ter_direct', '')}, Exit Load={scheme_facts.get('exit_load', '')}, Min SIP=Rs {scheme_facts.get('min_sip', '')}, Risk={scheme_facts.get('riskometer', '')}, Manager={scheme_facts.get('fund_manager', '')}."
            context_texts.insert(0, fact_summary)

    syn_res = _synthesizer.synthesize(
        query=request.query,
        context_chunks=context_texts,
        primary_url=retrieval_res.primary_citation_url,
        doc_date=get_default_corpus_date(),
    )

    elapsed_ms = (time.perf_counter() - t0) * 1000
    chunk_details = [
        {
            "chunk_id": c.chunk_id,
            "text": c.text,
            "metadata": c.metadata,
            "score": c.score,
            "dense_sim": c.dense_sim,
            "bm25_score": c.bm25_score,
        }
        for c in retrieval_res.chunks
    ]

    followups = generate_followup_suggestions(
        scheme_id=entity_res.scheme_id,
        field=entity_res.field,
        intent="FACTUAL",
    )

    clean_text = re.sub(r"\bNOT_FOUND\b\.?", "", syn_res.text, flags=re.I).strip()
    clean_rendered = re.sub(r"\bNOT_FOUND\b\.?", "", syn_res.rendered, flags=re.I).strip()
    clean_text = re.sub(r"\s{2,}", " ", clean_text)
    clean_rendered = re.sub(r"\s{2,}", " ", clean_rendered)

    res_type = (
        "not_found"
        if (
            "could not find" in syn_res.text.lower()
            or syn_res.raw_draft.strip().upper() == "NOT_FOUND"
            or not clean_text
        )
        else "llm_synthesis"
    )
    return SynthesisQueryResponse(
        query=request.query,
        resolution_type=res_type,
        scheme_id=entity_res.scheme_id,
        scheme_name=entity_res.scheme_name,
        field=entity_res.field,
        text=clean_text or syn_res.text,
        sentence_count=syn_res.sentence_count,
        citation_url=syn_res.citation_url,
        last_updated=syn_res.last_updated,
        rendered=clean_rendered or syn_res.rendered,
        repaired=syn_res.repaired,
        repair_count=syn_res.repair_count,
        deadline_fallback_used=syn_res.deadline_fallback_used,
        chunks=chunk_details,
        latency_ms=elapsed_ms,
        suggested_followups=followups,
    )
