import time
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, "backend")

from app.rag.retriever import HybridRetriever, get_embedder
from app.rag.synthesizer import ConstrainedSynthesizer
from app.rag.entities import resolve_entities
from app.guardrails.refusal import get_default_corpus_date

retriever = HybridRetriever()
synthesizer = ConstrainedSynthesizer()
embedder = get_embedder()

slow_cases = [
    ("b12", "How does SEBI recommend categorizing large cap schemes like HDFC Top 100?"),
    ("b34", "Advise what the minimum additional purchase amount is for HDFC Multi Cap Direct Growth."),
]

print("=" * 80)
print("PROFILING BREAKDOWN FOR LIVE LLM SYNTHESIS CASES")
print("=" * 80)

for cid, query in slow_cases:
    t_total_0 = time.perf_counter()
    
    # 1. Entity resolution
    t_ent_0 = time.perf_counter()
    ent = resolve_entities(query)
    t_ent_ms = (time.perf_counter() - t_ent_0) * 1000
    
    # 2. Embedding
    t_emb_0 = time.perf_counter()
    query_emb = embedder.encode([query]).tolist()
    t_emb_ms = (time.perf_counter() - t_emb_0) * 1000
    
    # 3. Retrieval
    t_ret_0 = time.perf_counter()
    ret_res = retriever.search(query, scheme_id=ent.scheme_id, top_k=4)
    t_ret_ms = (time.perf_counter() - t_ret_0) * 1000
    
    # 4. Groq Synthesis
    context_texts = [c.text for c in ret_res.chunks]
    t_groq_0 = time.perf_counter()
    syn_res = synthesizer.synthesize(
        query=query,
        context_chunks=context_texts,
        primary_url=ret_res.primary_citation_url,
        doc_date=get_default_corpus_date(),
    )
    t_groq_ms = (time.perf_counter() - t_groq_0) * 1000
    
    t_total_ms = (time.perf_counter() - t_total_0) * 1000
    
    print(f"\nCase ID:       {cid}")
    print(f"Query:         \"{query}\"")
    print(f"Scheme ID:     {ent.scheme_id}")
    print(f"Embedding:     {t_emb_ms:.2f} ms")
    print(f"Retrieval:     {t_ret_ms:.2f} ms")
    print(f"Groq API:      {t_groq_ms:.2f} ms")
    print(f"Total Turn:    {t_total_ms:.2f} ms")
    print(f"Draft Text:    {syn_res.text}")
    print(f"Contract Valid:{syn_res.is_valid} | Repaired: {syn_res.repaired}")
    print(f"Deadline Used: {syn_res.deadline_fallback_used}")
