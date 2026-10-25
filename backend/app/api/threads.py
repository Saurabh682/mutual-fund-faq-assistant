"""Thread & Session Management REST API Router."""

from __future__ import annotations

import time
import uuid
from typing import List, Optional
from fastapi import APIRouter, Header, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.audit.logger import record_audit_entry
from app.guardrails.intent import classify_intent
from app.guardrails.pii import PII_SECURITY_WARNING, scan_pii
from app.guardrails.refusal import (
    CANONICAL_LINKS,
    generate_refusal,
    get_default_corpus_date,
)
from app.guardrails.validator import split_sentences
from app.rag.entities import get_disambiguation_response, resolve_entities
from app.rag.facts import lookup_fact
from app.rag.retriever import HybridRetriever, get_not_found_response
from app.rag.synthesizer import ConstrainedSynthesizer
from app.schemas.chat import (
    ChatRequest,
    CreateThreadRequest,
    MessageDTO,
    ThreadDTO,
    ThreadSummaryDTO,
)
from app.sessions.store import SessionStore, get_thread_lock

router = APIRouter(prefix="/api/v1/threads", tags=["Threads & Chat Sessions"])

_store = SessionStore()
_retriever = HybridRetriever()
_synthesizer = ConstrainedSynthesizer()


@router.post("", response_model=ThreadDTO, status_code=status.HTTP_201_CREATED)
def create_thread(
    req: Optional[CreateThreadRequest] = None,
    x_client_id: Optional[str] = Header(None, alias="X-Client-Id"),
):
    """Creates a new isolated conversation thread."""
    client_id = (req.client_id if req and req.client_id else None) or x_client_id or "default_client"
    title = (req.title if req and req.title else None) or "New Conversation"
    return _store.create_thread(client_id=client_id, title=title)


@router.get("", response_model=List[ThreadSummaryDTO])
def list_threads(
    client_id: Optional[str] = Query(None),
    x_client_id: Optional[str] = Header(None, alias="X-Client-Id"),
):
    """Lists all threads belonging to the client ordered by last update."""
    effective_client_id = client_id or x_client_id or "default_client"
    return _store.list_threads(client_id=effective_client_id)


@router.get("/{thread_id}", response_model=ThreadDTO)
def get_thread(thread_id: str):
    """Retrieves full conversation history for a given thread."""
    thread = _store.get_thread(thread_id)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thread '{thread_id}' not found.",
        )
    return thread


@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_thread(thread_id: str):
    """Deletes a thread and its messages."""
    deleted = _store.delete_thread(thread_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thread '{thread_id}' not found.",
        )
    return None


@router.post("/{thread_id}/messages", response_model=MessageDTO)
async def post_message(
    thread_id: str,
    req: ChatRequest,
    x_client_id: Optional[str] = Header(None, alias="X-Client-Id"),
):
    """Submits a user query into the specified thread session.

    Enforces per-thread lock serialization, session scheme continuity,
    upstream PII/intent guardrails, structured facts, hybrid retrieval,
    and output contract enforcement.
    """
    lock = await get_thread_lock(thread_id)
    async with lock:
        t0 = time.perf_counter()
        thread = _store.get_thread(thread_id)
        effective_cid = (x_client_id if isinstance(x_client_id, str) else None) or "default_client"
        if not thread:
            # Self-heal missing thread ID (e.g. across server restarts or client cache)
            thread = _store.create_thread(
                client_id=effective_cid,
                title="Conversation",
                thread_id=thread_id,
            )

        client_id = (x_client_id if isinstance(x_client_id, str) else None) or thread.client_id
        user_query = req.text.strip()

        # 1. PII Scan (Firewall Stage)
        has_pii, detected_types, redacted_query = scan_pii(user_query)

        # Append user message (store redacted text if PII was detected)
        user_msg = MessageDTO(
            id=f"msg_{uuid.uuid4().hex[:12]}",
            role="user",
            type="user_query",
            text=redacted_query if has_pii else user_query,
        )
        _store.append_message(thread_id, user_msg)

        if has_pii:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            doc_date = get_default_corpus_date()
            citation = CANONICAL_LINKS["ADVISORY"]
            rendered_warning = (
                f"{PII_SECURITY_WARNING}\n\n"
                f"Source: {citation}\n"
                f"Last updated from sources: {doc_date}"
            )
            asst_msg = MessageDTO(
                id=f"msg_{uuid.uuid4().hex[:12]}",
                role="assistant",
                type="pii_block",
                text=PII_SECURITY_WARNING,
                sentence_count=2,
                citation_url=citation,
                last_updated=doc_date,
                rendered=rendered_warning,
                latency_ms=elapsed_ms,
            )
            _store.append_message(thread_id, asst_msg)

            record_audit_entry(
                thread_id=thread_id,
                client_id=client_id,
                redacted_query=redacted_query,
                resolution_type="pii_block",
                intent="PII_BLOCKED",
                citation_url=citation,
                sentence_count=2,
                latency_ms=elapsed_ms,
                metadata={"detected_types": detected_types},
            )
            return asst_msg

        # Auto-update thread title if this is the first turn
        if len(thread.messages) <= 1:
            clean_title = user_query[:35] + ("..." if len(user_query) > 35 else "")
            _store.update_thread_title(thread_id, clean_title)

        # 2. Intent Classification (Compliance Stage)
        intent_res = classify_intent(user_query)
        if intent_res.is_refusal:
            refusal = generate_refusal(intent_res.intent)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            sentences = split_sentences(refusal["text"])

            asst_msg = MessageDTO(
                id=f"msg_{uuid.uuid4().hex[:12]}",
                role="assistant",
                type="refusal",
                text=refusal["text"],
                sentence_count=len(sentences),
                citation_url=refusal["citation_url"],
                last_updated=refusal["last_updated"],
                rendered=refusal["rendered"],
                latency_ms=elapsed_ms,
            )
            _store.append_message(thread_id, asst_msg)

            record_audit_entry(
                thread_id=thread_id,
                client_id=client_id,
                redacted_query=user_query,
                resolution_type="refusal",
                intent=intent_res.intent,
                citation_url=refusal["citation_url"],
                sentence_count=len(sentences),
                latency_ms=elapsed_ms,
            )
            return asst_msg

        # 3. Entity Resolution with Session Scheme Continuity (EC-ENT-02)
        entity_res = resolve_entities(
            user_query, session_scheme_id=thread.last_scheme_id
        )

        # Ambiguity Handling (EC-ENT-01)
        if entity_res.is_ambiguous:
            clarification = get_disambiguation_response()
            elapsed_ms = (time.perf_counter() - t0) * 1000
            sentences = split_sentences(clarification["text"])

            asst_msg = MessageDTO(
                id=f"msg_{uuid.uuid4().hex[:12]}",
                role="assistant",
                type="clarification",
                text=clarification["text"],
                sentence_count=len(sentences),
                citation_url=clarification["citation_url"],
                last_updated=clarification["last_updated"],
                rendered=clarification["rendered"],
                latency_ms=elapsed_ms,
            )
            _store.append_message(thread_id, asst_msg)

            record_audit_entry(
                thread_id=thread_id,
                client_id=client_id,
                redacted_query=user_query,
                resolution_type="clarification",
                intent="FACTUAL_AMBIGUOUS",
                field=entity_res.field,
                citation_url=clarification["citation_url"],
                sentence_count=len(sentences),
                latency_ms=elapsed_ms,
            )
            return asst_msg

        # 4. Structured Fact Store Fast Path
        fact_resp = lookup_fact(
            user_query, session_scheme_id=thread.last_scheme_id
        )
        if fact_resp:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            sentences = split_sentences(fact_resp["text"])
            matched_scheme = fact_resp.get("scheme_id")

            if matched_scheme:
                _store.update_thread_scheme(thread_id, matched_scheme)

            asst_msg = MessageDTO(
                id=f"msg_{uuid.uuid4().hex[:12]}",
                role="assistant",
                type="fact_store",
                text=fact_resp["text"],
                sentence_count=len(sentences),
                citation_url=fact_resp["citation_url"],
                last_updated=fact_resp["last_updated"],
                rendered=fact_resp["rendered"],
                latency_ms=elapsed_ms,
            )
            _store.append_message(thread_id, asst_msg)

            record_audit_entry(
                thread_id=thread_id,
                client_id=client_id,
                redacted_query=user_query,
                resolution_type="fact_store",
                intent="FACTUAL",
                scheme_id=matched_scheme,
                field=fact_resp.get("field"),
                citation_url=fact_resp["citation_url"],
                sentence_count=len(sentences),
                latency_ms=elapsed_ms,
            )
            return asst_msg

        # 5. Hybrid Retrieval Path (ChromaDB + BM25 + RRF)
        retrieval_res = _retriever.search(
            query=user_query,
            scheme_id=entity_res.scheme_id,
            top_k=4,
        )

        if retrieval_res.is_out_of_corpus or not retrieval_res.chunks:
            not_found = get_not_found_response()
            elapsed_ms = (time.perf_counter() - t0) * 1000
            sentences = split_sentences(not_found["text"])

            asst_msg = MessageDTO(
                id=f"msg_{uuid.uuid4().hex[:12]}",
                role="assistant",
                type="not_found",
                text=not_found["text"],
                sentence_count=len(sentences),
                citation_url=not_found["citation_url"],
                last_updated=not_found["last_updated"],
                rendered=not_found["rendered"],
                latency_ms=elapsed_ms,
            )
            _store.append_message(thread_id, asst_msg)

            record_audit_entry(
                thread_id=thread_id,
                client_id=client_id,
                redacted_query=user_query,
                resolution_type="not_found",
                intent="OUT_OF_CORPUS",
                scheme_id=entity_res.scheme_id,
                citation_url=not_found["citation_url"],
                sentence_count=len(sentences),
                latency_ms=elapsed_ms,
            )
            return asst_msg

        # Update active thread scheme if resolved
        if entity_res.scheme_id:
            _store.update_thread_scheme(thread_id, entity_res.scheme_id)

        # 6. Constrained LLM Synthesis with Output Contract Validation
        syn_res = _synthesizer.synthesize(
            query=user_query,
            context_chunks=retrieval_res.chunks,
            primary_url=retrieval_res.primary_citation_url,
            doc_date=retrieval_res.primary_doc_date,
        )

        elapsed_ms = (time.perf_counter() - t0) * 1000
        asst_msg = MessageDTO(
            id=f"msg_{uuid.uuid4().hex[:12]}",
            role="assistant",
            type="llm_synthesis",
            text=syn_res.text,
            sentence_count=syn_res.sentence_count,
            citation_url=syn_res.citation_url,
            last_updated=syn_res.last_updated,
            rendered=syn_res.rendered,
            latency_ms=elapsed_ms,
        )
        _store.append_message(thread_id, asst_msg)

        retrieved_ids = [c.chunk_id for c in retrieval_res.chunks]
        record_audit_entry(
            thread_id=thread_id,
            client_id=client_id,
            redacted_query=user_query,
            resolution_type="llm_synthesis",
            intent="PROCEDURAL_OR_FACTUAL",
            scheme_id=entity_res.scheme_id,
            field=entity_res.field,
            retrieved_chunk_ids=retrieved_ids,
            sentence_count=syn_res.sentence_count,
            citation_url=syn_res.citation_url,
            latency_ms=elapsed_ms,
            repaired=syn_res.repaired,
            repair_count=syn_res.repair_count,
        )
        return asst_msg
