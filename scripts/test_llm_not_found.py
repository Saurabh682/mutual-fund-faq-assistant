import sys
sys.path.insert(0, 'backend')
from app.rag.retriever import HybridRetriever
from app.rag.synthesizer import ConstrainedSynthesizer
from app.rag.entities import resolve_entities

ret = HybridRetriever()
syn = ConstrainedSynthesizer()

queries = [
    "What is the portfolio allocation to Tesla in HDFC Top 100 Fund?",
    "Does HDFC Small Cap Fund invest in Japanese government bonds?",
    "What is the portfolio turnover of HDFC Top 100?",
    "What are the SIP dates for HDFC Mid Cap?"
]

for q in queries:
    ent = resolve_entities(q)
    res = ret.search(q, scheme_id=ent.scheme_id)
    print(f"\n=== Query: {q} ===")
    print(f"Chunks found: {len(res.chunks)}, is_out_of_corpus: {res.is_out_of_corpus}")
    if res.chunks:
        chunks_text = [c.text for c in res.chunks]
        syn_res = syn.synthesize(q, context_chunks=chunks_text, primary_url=res.primary_citation_url)
        print(f"Raw Draft: {syn_res.raw_draft}")
        print(f"Text: {syn_res.text}")
        print(f"Valid: {syn_res.is_valid}")
