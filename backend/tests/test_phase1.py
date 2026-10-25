import os
import pickle
import sqlite3
import yaml
import json
import chromadb
from app.core.config import settings

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
MANIFEST_PATH = os.path.join(BASE_DIR, "data", "corpus_manifest.yaml")
FACTS_DB_PATH = os.path.join(BASE_DIR, "data", "index", "facts.db")
CHROMA_DIR = os.path.join(BASE_DIR, "data", "index", "chroma")
BM25_PATH = os.path.join(BASE_DIR, "data", "index", "bm25.pkl")
REPORT_PATH = os.path.join(BASE_DIR, "data", "ingestion_report.json")

def test_manifest_integrity():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    assert manifest["allowed_domains"] == ["groww.in"]
    assert len(manifest["sources"]) == 5

    expected_urls = {
        "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
        "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
        "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
        "https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth",
        "https://groww.in/mutual-funds/hdfc-multi-cap-fund-direct-growth"
    }

    manifest_urls = {s["url"] for s in manifest["sources"]}
    assert manifest_urls == expected_urls

def test_facts_db_contents():
    assert os.path.exists(FACTS_DB_PATH)
    conn = sqlite3.connect(FACTS_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(DISTINCT scheme_id) FROM facts")
    assert cursor.fetchone()[0] == 5

    required_fields = {"ter_direct", "exit_load", "min_sip", "min_lumpsum", "lock_in", "riskometer", "benchmark"}
    for scheme_id in ["hdfc_midcap_dg", "hdfc_smallcap_dg", "hdfc_largecap_dg", "hdfc_silver_fof_dg", "hdfc_multicap_dg"]:
        cursor.execute("SELECT field, value FROM facts WHERE scheme_id = ?", (scheme_id,))
        rows = dict(cursor.fetchall())
        for f in required_fields:
            assert f in rows, f"Missing field {f} in {scheme_id}"
            assert len(rows[f]) > 0

    conn.close()

def test_chroma_index():
    from ingest.embed import get_embedder
    assert os.path.exists(CHROMA_DIR)
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection("mutual_fund_facts")
    count = collection.count()
    assert count >= 30

    # Query ChromaDB with exact embedding model
    embedder = get_embedder()
    q_emb = embedder.encode(["What is the exit load for HDFC Mid Cap?"]).tolist()
    results = collection.query(query_embeddings=q_emb, n_results=3)
    assert len(results["ids"][0]) == 3
    assert any("midcap" in mid.lower() or "mid cap" in doc.lower() for mid, doc in zip(results["ids"][0], results["documents"][0]))

def test_bm25_index():
    assert os.path.exists(BM25_PATH)
    with open(BM25_PATH, "rb") as f:
        bm25_data = pickle.load(f)

    assert "bm25" in bm25_data
    assert len(bm25_data["chunks"]) >= 30

    query_tokens = "silver etf exit load".split()
    scores = bm25_data["bm25"].get_scores(query_tokens)
    top_idx = scores.argmax()
    best_chunk = bm25_data["chunks"][top_idx]
    assert "silver" in best_chunk["text"].lower()

def test_ingestion_report():
    assert os.path.exists(REPORT_PATH)
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        report = json.load(f)

    assert report["status"] == "success"
    assert report["total_sources"] == 5
    assert report["total_chunks"] >= 30
    assert len(report["schemes"]) == 5
