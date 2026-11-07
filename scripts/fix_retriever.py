with open("backend/app/rag/retriever.py", "r", encoding="utf-8") as f:
    ret_code = f.read()

# 1. Ensure import re is at top
if "import re" not in ret_code:
    ret_code = ret_code.replace("import os\n", "import os\nimport re\n")

# 2. Update search early-exit condition
target_block = """        if scheme_id is None:
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

replacement_block = """        if scheme_id is None:
            if max_dense_sim < self.tau:
                return RetrievalResult(
                    chunks=[],
                    primary_citation_url=CANONICAL_LINKS["ADVISORY"],
                    is_out_of_corpus=True,
                    max_similarity=max_dense_sim,
                )
        else:
            # Low-similarity fast path & missing unindexed entity early exit (e.g. Tesla, Apple, Bitcoin, ESG)
            UNINDEXED_ENTITIES = {
                "tesla", "apple", "bitcoin", "ethereum", "crypto", "cryptocurrency",
                "doge", "nvidia", "microsoft", "amazon", "google", "meta", "esg",
                "dogecoin", "solana", "bnb", "usdt", "xrp", "cardano",
            }
            chunks_text = " ".join([d["text"].lower() for d in dense_docs.values()]) if dense_docs else ""
            query_lower = clean_query.lower()
            
            # Check if query specifically targets an unindexed external entity absent from chunks
            has_unindexed_target = any(
                ent in query_lower and ent not in chunks_text
                for ent in UNINDEXED_ENTITIES
            )
            has_bm25_hit = bool(bm25_scores and max(bm25_scores.values()) > 0.0)

            if has_unindexed_target or (max_dense_sim < 0.38 and not has_bm25_hit):
                return RetrievalResult(
                    chunks=[],
                    primary_citation_url=CANONICAL_LINKS["ADVISORY"],
                    is_out_of_corpus=True,
                    max_similarity=max_dense_sim,
                )"""

if target_block in ret_code:
    ret_code = ret_code.replace(target_block, replacement_block)
    with open("backend/app/rag/retriever.py", "w", encoding="utf-8") as f:
        f.write(ret_code)
    print("retriever.py fixed successfully with import re and UNINDEXED_ENTITIES check.")
else:
    print("Warning: target_block not found in retriever.py")
