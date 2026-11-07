import sys
sys.path.insert(0, "backend")

from app.rag.retriever import HybridRetriever

retriever = HybridRetriever()

queries = [
    ("What is the portfolio allocation to Tesla in HDFC Top 100 Fund?", "hdfc_largecap_dg"),
    ("What is the ESG score of HDFC Multi Cap Fund?", "hdfc_multicap_dg"),
    ("How many shares of Apple does HDFC Small Cap own?", "hdfc_smallcap_dg"),
    ("Does HDFC Silver ETF FoF invest in Bitcoin or Ethereum?", "hdfc_silver_fof_dg"),
    ("What is the dividend yield of HDFC Top 100 in 2024?", "hdfc_largecap_dg"),
    ("What is the expense ratio of HDFC Mid-Cap Opportunities Fund?", "hdfc_midcap_dg"),
    ("What is the exit load for HDFC Small Cap Fund?", "hdfc_smallcap_dg"),
]

for q, sid in queries:
    res = retriever.search(q, scheme_id=sid)
    max_dense = res.max_similarity
    bm25_max = max([c.bm25_score for c in res.chunks]) if res.chunks else 0.0
    print(f"'{q[:50]}...': max_dense={max_dense:.3f} | bm25_max={bm25_max:.3f} | chunks={len(res.chunks)}")
