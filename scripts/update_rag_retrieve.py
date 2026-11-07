with open("backend/app/api/rag.py", "r", encoding="utf-8") as f:
    code = f.read()

target = """    # 2. Intent Classifier (Compliance Firewall)
    intent_res = classify_intent(request.query)"""

replacement = """    # 1b. Clause-Level Intent Check for Compound Factual-plus-Advisory Queries
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
    intent_res = classify_intent(request.query)"""

if target in code:
    code = code.replace(target, replacement, 1)
    with open("backend/app/api/rag.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("retrieve_query updated successfully.")
else:
    print("target not found in rag.py")
