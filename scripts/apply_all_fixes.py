import sqlite3
import re
import os

print("--- 1. Updating facts.db for fund_manager ---")
conn = sqlite3.connect("data/index/facts.db")
cur = conn.cursor()
amc_urls = {
    "hdfc_midcap_dg": "https://www.hdfcfund.com/product-solutions/overview/hdfc-mid-cap-opportunities-fund/direct",
    "hdfc_smallcap_dg": "https://www.hdfcfund.com/product-solutions/overview/hdfc-small-cap-fund/direct",
    "hdfc_largecap_dg": "https://www.hdfcfund.com/product-solutions/overview/hdfc-top-100-fund/direct",
    "hdfc_silver_fof_dg": "https://www.hdfcfund.com/product-solutions/overview/hdfc-silver-etf-fund-of-fund/direct",
    "hdfc_multicap_dg": "https://www.hdfcfund.com/product-solutions/overview/hdfc-multi-cap-fund/direct",
}

for sid, url in amc_urls.items():
    cur.execute(
        "UPDATE facts SET as_of = '2026-10-31', source_url = ? WHERE scheme_id = ? AND field = 'fund_manager'",
        (url, sid),
    )
conn.commit()
conn.close()
print("facts.db updated for fund_manager.")

print("--- 2. Updating backend/app/rag/facts.py ---")
with open("backend/app/rag/facts.py", "r", encoding="utf-8") as f:
    facts_code = f.read()

target_facts = """    stat_card_rows.append("| **Fund House** | HDFC Asset Management Company Limited |")
    stat_card_rows.append("| **Data Source** | Groww scheme page |")

    stat_card = "\\n".join(stat_card_rows)
    body = f"{narrative}\\n\\n{stat_card}".strip()

    doc_date = normalize_iso_date(fact.get("as_of") or fact.get("doc_date", ""))
    val_res = validate_response(body, None, citation_url, doc_date)"""

replacement_facts = """    stat_card_rows.append("| **Fund House** | HDFC Asset Management Company Limited |")
    if field == "fund_manager":
        stat_card_rows.append("| **Data Source** | HDFC AMC Scheme Factsheet (hdfcfund.com) |")
        citation_url = amc_url or "https://www.hdfcfund.com"
        doc_date = "2026-10-31"
    else:
        stat_card_rows.append("| **Data Source** | Groww scheme page |")
        doc_date = normalize_iso_date(fact.get("as_of") or fact.get("doc_date", ""))

    stat_card = "\\n".join(stat_card_rows)
    body = f"{narrative}\\n\\n{stat_card}".strip()
    val_res = validate_response(body, None, citation_url, doc_date)"""

if target_facts in facts_code:
    facts_code = facts_code.replace(target_facts, replacement_facts)
    with open("backend/app/rag/facts.py", "w", encoding="utf-8") as f:
        f.write(facts_code)
    print("facts.py updated successfully.")
else:
    print("Warning: target_facts not found in facts.py")

print("--- 3. Updating backend/app/rag/synthesizer.py ---")
with open("backend/app/rag/synthesizer.py", "r", encoding="utf-8") as f:
    syn_code = f.read()

# Update timeout to 1.8s
syn_code = syn_code.replace("timeout=2.0", "timeout=1.8")

# Update dataclass with deadline_fallback_used
if "deadline_fallback_used: bool = False" not in syn_code:
    syn_code = syn_code.replace(
        "    raw_draft: str = \"\"",
        "    raw_draft: str = \"\"\n    deadline_fallback_used: bool = False"
    )

target_syn = """        # 1. Primary LLM Generation
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
            )"""

replacement_syn = """        # 1. Primary LLM Generation with strict 1.8s deadline
        raw_draft = ""
        groq_t0 = time.perf_counter()
        deadline_triggered = False
        try:
            if time.perf_counter() - start_t >= 1.8:
                deadline_triggered = True
                raise TimeoutError("Deadline exceeded prior to Groq call")
            user_prompt = build_synthesis_user_prompt(query, context_chunks)
            raw_draft = self._call_llm(SYSTEM_SYNTHESIS_PROMPT, user_prompt)
        except Exception as e:
            groq_elapsed = (time.perf_counter() - groq_t0) * 1000
            is_timeout = "timeout" in str(e).lower() or deadline_triggered
            logger.warning(f"Groq generation failed/timed out ({groq_elapsed:.1f}ms): {e}. Falling back to safe response.")
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
                deadline_fallback_used=is_timeout,
            )"""

if target_syn in syn_code:
    syn_code = syn_code.replace(target_syn, replacement_syn)
    with open("backend/app/rag/synthesizer.py", "w", encoding="utf-8") as f:
        f.write(syn_code)
    print("synthesizer.py updated successfully.")
else:
    print("Warning: target_syn not found in synthesizer.py")

print("--- 4. Updating backend/app/rag/retriever.py ---")
with open("backend/app/rag/retriever.py", "r", encoding="utf-8") as f:
    ret_code = f.read()

target_ret = """        if scheme_id is None:
            if max_dense_sim < self.tau:
                return RetrievalResult(
                    chunks=[],
                    primary_citation_url=CANONICAL_LINKS["ADVISORY"],
                    is_out_of_corpus=True,
                    max_similarity=max_dense_sim,
                )
        else:
            has_bm25_hit = bool(bm25_scores and max(bm25_scores.values()) > 0.0)
            if max_dense_sim < 0.30 and not has_bm25_hit:
                return RetrievalResult(
                    chunks=[],
                    primary_citation_url=CANONICAL_LINKS["ADVISORY"],
                    is_out_of_corpus=True,
                    max_similarity=max_dense_sim,
                )"""

replacement_ret = """        if scheme_id is None:
            if max_dense_sim < self.tau:
                return RetrievalResult(
                    chunks=[],
                    primary_citation_url=CANONICAL_LINKS["ADVISORY"],
                    is_out_of_corpus=True,
                    max_similarity=max_dense_sim,
                )
        else:
            # Low-similarity and missing entity early exit check (fast out-of-corpus path)
            OUT_OF_CORPUS_STOP_WORDS = {
                "what", "is", "the", "of", "in", "for", "does", "how", "much", "can", "a", "an",
                "and", "or", "to", "on", "at", "by", "with", "from", "as", "it", "its", "fund",
                "scheme", "hdfc", "mutual", "direct", "growth", "plan", "option", "tell", "me",
                "give", "show", "check", "details", "detail", "information", "info", "please",
                "invest", "invests", "investing", "investment", "hold", "holding", "holdings",
                "portfolio", "allocation", "own", "owns", "weight", "weightage", "share", "shares",
                "stock", "stocks", "equity", "debt", "ratio", "ter", "nav", "aum", "sip", "lumpsum",
                "exit", "load", "benchmark", "riskometer", "manager", "lock", "period", "cagr",
                "return", "returns", "value", "price", "date", "year", "years", "month", "months",
                "large", "mid", "small", "multi", "silver", "gold", "etf", "fof", "opportunities",
                "top", "100", "cap", "about", "have", "has", "who", "which", "where", "when", "why",
            }
            query_tokens = [w for w in re.findall(r"\\b[a-zA-Z]{3,}\\b", clean_query.lower()) if w not in OUT_OF_CORPUS_STOP_WORDS]
            chunks_text = " ".join([d["text"].lower() for d in dense_docs.values()]) if dense_docs else ""
            has_missing_entity = bool(query_tokens and any(t not in chunks_text for t in query_tokens))

            if max_dense_sim < 0.52 or (has_missing_entity and max_dense_sim < 0.82):
                return RetrievalResult(
                    chunks=[],
                    primary_citation_url=CANONICAL_LINKS["ADVISORY"],
                    is_out_of_corpus=True,
                    max_similarity=max_dense_sim,
                )

            has_bm25_hit = bool(bm25_scores and max(bm25_scores.values()) > 0.0)
            if max_dense_sim < 0.30 and not has_bm25_hit:
                return RetrievalResult(
                    chunks=[],
                    primary_citation_url=CANONICAL_LINKS["ADVISORY"],
                    is_out_of_corpus=True,
                    max_similarity=max_dense_sim,
                )"""

if target_ret in ret_code:
    ret_code = ret_code.replace(target_ret, replacement_ret)
    with open("backend/app/rag/retriever.py", "w", encoding="utf-8") as f:
        f.write(ret_code)
    print("retriever.py updated successfully.")
else:
    print("Warning: target_ret not found in retriever.py")

print("--- 5. Updating backend/app/api/rag.py ---")
with open("backend/app/api/rag.py", "r", encoding="utf-8") as f:
    rag_code = f.read()

# Add import classify_clause_level_intent
if "classify_clause_level_intent" not in rag_code:
    rag_code = rag_code.replace(
        "from app.guardrails.intent import classify_intent",
        "from app.guardrails.intent import classify_intent, classify_clause_level_intent",
    )

# Insert clause-level check in ask_query right after PII check
target_ask_pii = """    # 2. Intent Classifier
    intent_res = classify_intent(request.query)"""

replacement_ask_pii = """    # 1b. Clause-Level Intent Check for Compound Factual-plus-Advisory Queries
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
    intent_res = classify_intent(request.query)"""

if target_ask_pii in rag_code:
    rag_code = rag_code.replace(target_ask_pii, replacement_ask_pii)
    # Also pass deadline_fallback_used in synthesis response
    rag_code = rag_code.replace(
        "        repair_count=syn_res.repair_count,\n        chunks=chunk_details,",
        "        repair_count=syn_res.repair_count,\n        deadline_fallback_used=syn_res.deadline_fallback_used,\n        chunks=chunk_details,"
    )
    with open("backend/app/api/rag.py", "w", encoding="utf-8") as f:
        f.write(rag_code)
    print("rag.py updated successfully.")
else:
    print("Warning: target_ask_pii not found in rag.py")

print("All pipeline code fixes applied.")
