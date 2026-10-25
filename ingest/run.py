import os
import sys
import yaml
import json
import time
from datetime import datetime, timezone
from ingest.fetchers import check_domain_allowlist, fetch_groww_scheme
from ingest.parsers.html import parse_groww_scheme
from ingest.chunker import chunk_parsed_scheme
from ingest.fact_extractor import init_fact_store, store_scheme_facts
from ingest.embed import index_chunks

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def run_ingestion(force_refresh: bool = False):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    manifest_path = os.path.join(base_dir, "data", "corpus_manifest.yaml")
    cache_dir = os.path.join(base_dir, "data", "raw")
    facts_db_path = os.path.join(base_dir, "data", "index", "facts.db")
    chroma_dir = os.path.join(base_dir, "data", "index", "chroma")
    bm25_path = os.path.join(base_dir, "data", "index", "bm25.pkl")
    report_path = os.path.join(base_dir, "data", "ingestion_report.json")

    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting Phase 1 Ingestion Pipeline...")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    allowed_domains = manifest.get("allowed_domains", ["groww.in"])
    sources = manifest.get("sources", [])

    print(f"Loaded manifest with {len(sources)} sources. Allowed domains: {allowed_domains}")

    # Enforce strict 5 Groww URLs
    for s in sources:
        if not check_domain_allowlist(s["url"], allowed_domains):
            raise ValueError(f"CRITICAL: URL {s['url']} is not within allowed domains {allowed_domains}")

    init_fact_store(facts_db_path)

    all_chunks = []
    schemes_report = []
    start_time = time.time()

    for idx, s in enumerate(sources, start=1):
        scheme_id = s["scheme_id"]
        url = s["url"]
        print(f"\n({idx}/{len(sources)}) Ingesting {scheme_id} from {url}...")

        # 1. Fetch
        raw_data = fetch_groww_scheme(url, cache_dir, scheme_id, force_refresh=force_refresh)

        # 2. Parse
        parsed = parse_groww_scheme(raw_data)
        scheme_name = parsed["scheme_name"]
        facts = parsed["canonical_facts"]
        doc_date = parsed["doc_date"]

        # 3. Store Structured Facts
        store_scheme_facts(facts_db_path, scheme_id, facts, url, doc_date)

        # 4. Chunk
        chunks = chunk_parsed_scheme(parsed)
        all_chunks.extend(chunks)

        print(f"   [OK] Scheme: {scheme_name}")
        print(f"   [OK] Extracted Facts: TER={facts.get('ter_direct')}, ExitLoad={facts.get('exit_load')[:40]}..., MinSIP={facts.get('min_sip')}, Risk={facts.get('riskometer')}")
        print(f"   [OK] Generated {len(chunks)} semantic chunks")

        schemes_report.append({
            "scheme_id": scheme_id,
            "scheme_name": scheme_name,
            "url": url,
            "doc_date": doc_date,
            "chunks_count": len(chunks),
            "canonical_facts": facts
        })

    # 5. Embed and Index into ChromaDB + BM25
    print(f"\nIndexing {len(all_chunks)} chunks into ChromaDB & BM25...")
    index_chunks(all_chunks, chroma_dir, bm25_path)
    print("   [OK] ChromaDB dense vector indexing complete.")
    print("   [OK] BM25 lexical index built and pickled.")

    elapsed = round(time.time() - start_time, 2)
    report = {
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": elapsed,
        "total_sources": len(sources),
        "total_chunks": len(all_chunks),
        "schemes": schemes_report
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*70}")
    print(f"Phase 1 Ingestion Succeeded in {elapsed}s!")
    print(f"Total Sources: {len(sources)} | Total Chunks: {len(all_chunks)}")
    print(f"Ingestion Report written to {report_path}")
    print(f"{'='*70}")

if __name__ == "__main__":
    run_ingestion()
