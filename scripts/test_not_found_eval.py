import sys, json
sys.path.insert(0, 'backend')
from app.rag.retriever import HybridRetriever
from app.rag.entities import resolve_entities

ret = HybridRetriever()

with open('eval/datasets/holdout_v2.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if not line.strip(): continue
        d = json.loads(line)
        if d.get('expected_behavior') == 'not_found':
            q = d['query']
            ent = resolve_entities(q)
            res = ret.search(q, scheme_id=ent.scheme_id)
            print(f"{d['id']}: sim={res.max_similarity:.4f}, out_of_corpus={res.is_out_of_corpus}")
