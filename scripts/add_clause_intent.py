with open("backend/app/guardrails/intent.py", "r", encoding="utf-8") as f:
    text = f.read()

clause_code = '''

def split_clauses(query: str) -> List[str]:
    """Splits a query into constituent clauses on conjunctions ('and', 'but', 'also') and punctuation ('?', ';')."""
    parts = re.split(r"\\s*(?:[?;]+\\s*|\\s+(?:and|but|also)\\s+)\\s*", query.strip(), flags=re.I)
    return [p.strip() for p in parts if p.strip()]


def classify_clause_level_intent(
    query: str, session_scheme_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Evaluates clause-level intent for compound factual-plus-advisory queries.

    Splits on conjunctions ('and', 'but', 'also') and punctuation ('?', ';').
    If a query has a factual component (from facts.db, procedures, or glossary)
    and an advisory/comparative/projection refusal component, returns a deterministic
    2-sentence compound response (1 fact sentence + 1 fixed compliance refusal sentence),
    completely bypassing the LLM. Zero phrase patches.
    """
    clauses = split_clauses(query)
    if len(clauses) < 2:
        return None

    # Lazy imports to avoid circular dependencies
    from app.rag.entities import resolve_entities
    from app.rag.facts import lookup_fact
    from app.rag.procedures import lookup_procedure
    from app.rag.glossary import lookup_glossary
    from app.guardrails.refusal import generate_compound_refusal
    from app.guardrails.validator import split_sentences

    full_ent = resolve_entities(query, session_scheme_id=session_scheme_id)
    active_scheme = full_ent.scheme_id or session_scheme_id

    fact_resp = None
    refusal_intent = None

    # Check whole-query intent first
    full_intent = classify_intent(query)
    if full_intent.is_refusal:
        refusal_intent = full_intent.intent

    for c in clauses:
        c_ent = resolve_entities(c, session_scheme_id=active_scheme)
        target_scheme = c_ent.scheme_id or active_scheme

        # Check factual lookup on clause
        if not fact_resp:
            f = lookup_fact(c, session_scheme_id=target_scheme)
            if f:
                fact_resp = f
            elif not target_scheme:
                p = lookup_procedure(c)
                if p:
                    fact_resp = p
                else:
                    g = lookup_glossary(c)
                    if g:
                        fact_resp = g

        # Check refusal intent on clause
        i_res = classify_intent(c)
        if i_res.is_refusal and not refusal_intent:
            refusal_intent = i_res.intent

    if fact_resp and refusal_intent:
        raw_text = fact_resp["text"].split("\\n\\n")[0]
        sentences = split_sentences(raw_text)
        first_sentence = sentences[0] if sentences else raw_text
        return generate_compound_refusal(
            factual_sentence=first_sentence,
            intent=refusal_intent,
            citation_url=fact_resp.get("citation_url") or fact_resp.get("source_url"),
            last_updated=fact_resp.get("last_updated"),
        )

    return None
'''

if "def split_clauses" not in text:
    text += clause_code
    with open("backend/app/guardrails/intent.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("Added split_clauses and classify_clause_level_intent to intent.py")
else:
    print("Already present in intent.py")
