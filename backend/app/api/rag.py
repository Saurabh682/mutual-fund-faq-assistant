"""RAG, Entity Resolution, and Fact Store API Router."""

from __future__ import annotations

import time
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.guardrails.pii import PII_SECURITY_WARNING, scan_pii
from app.guardrails.intent import classify_intent
from app.guardrails.refusal import CANONICAL_LINKS, generate_refusal, get_default_corpus_date
from app.guardrails.validator import split_sentences
from app.rag.entities import get_disambiguation_response, resolve_entities
from app.rag.facts import lookup_fact
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

    # 3. Entity Resolution
    entity_res = resolve_entities(request.query, session_scheme_id=request.session_scheme_id)

    # External AMC check (strictly out-of-corpus)
    if entity_res.is_external_amc:
        not_found = get_not_found_response()
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return RetrievalQueryResponse(
            query=request.query,
            resolution_type="not_found",
            scheme_id=None,
            scheme_name=None,
            field=entity_res.field,
            text=not_found["text"],
            citation_url=not_found["citation_url"],
            last_updated=not_found["last_updated"],
            rendered=not_found["rendered"],
            chunks=[],
            latency_ms=elapsed_ms,
        )

    # Ambiguity check (EC-ENT-01)
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

    rendered_text = f"{top_chunk.text}\n\nSource: {retrieval_res.primary_citation_url}\nLast updated from sources: {retrieval_res.primary_doc_date}"

    return RetrievalQueryResponse(
        query=request.query,
        resolution_type="hybrid_retrieval",
        scheme_id=entity_res.scheme_id,
        scheme_name=entity_res.scheme_name,
        field=entity_res.field,
        text=top_chunk.text,
        citation_url=retrieval_res.primary_citation_url,
        last_updated=retrieval_res.primary_doc_date,
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

    # 2. Intent Classifier
    intent_res = classify_intent(request.query)
    if intent_res.is_refusal:
        refusal = generate_refusal(intent_res.intent)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        sentences = split_sentences(refusal["text"])
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
        )

    # 3. Entity Resolution
    entity_res = resolve_entities(request.query, session_scheme_id=request.session_scheme_id)

    # External AMC check (strictly out-of-corpus)
    if entity_res.is_external_amc:
        not_found = get_not_found_response()
        elapsed_ms = (time.perf_counter() - t0) * 1000
        sentences = split_sentences(not_found["text"])
        return SynthesisQueryResponse(
            query=request.query,
            resolution_type="not_found",
            scheme_id=None,
            scheme_name=None,
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
        )

    if entity_res.is_ambiguous:
        clarification = get_disambiguation_response()
        elapsed_ms = (time.perf_counter() - t0) * 1000
        sentences = split_sentences(clarification["text"])
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
        )

    # 4. Structured Fact Store Fast Path
    fact_resp = lookup_fact(request.query, session_scheme_id=request.session_scheme_id)
    if fact_resp:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        sentences = split_sentences(fact_resp["text"])
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
        )

    # 6. Constrained LLM Synthesis with Output Contract Validation
    syn_res = _synthesizer.synthesize(
        query=request.query,
        context_chunks=retrieval_res.chunks,
        primary_url=retrieval_res.primary_citation_url,
        doc_date=retrieval_res.primary_doc_date,
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

    return SynthesisQueryResponse(
        query=request.query,
        resolution_type="llm_synthesis",
        scheme_id=entity_res.scheme_id,
        scheme_name=entity_res.scheme_name,
        field=entity_res.field,
        text=syn_res.text,
        sentence_count=syn_res.sentence_count,
        citation_url=syn_res.citation_url,
        last_updated=syn_res.last_updated,
        rendered=syn_res.rendered,
        repaired=syn_res.repaired,
        repair_count=syn_res.repair_count,
        chunks=chunk_details,
        latency_ms=elapsed_ms,
    )
