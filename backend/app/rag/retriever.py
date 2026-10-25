"""Hybrid Retrieval Engine for Mutual Fund FAQ Assistant.

Executes hybrid search across ChromaDB (dense cosine) and BM25 (lexical keyword),
fused using Reciprocal Rank Fusion (RRF k=60) with strict metadata pre-filtering
on scheme_id to eliminate cross-scheme contamination.
"""

from __future__ import annotations

import os
import pickle
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import chromadb
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.guardrails.refusal import CANONICAL_LINKS, get_default_corpus_date, normalize_date_footer

_EMBEDDER_INSTANCE: Optional[SentenceTransformer] = None


def get_embedder() -> SentenceTransformer:
    """Singleton getter for SentenceTransformer embedding model."""
    global _EMBEDDER_INSTANCE
    if _EMBEDDER_INSTANCE is None:
        _EMBEDDER_INSTANCE = SentenceTransformer(settings.EMBEDDING_MODEL, device="cpu")
    return _EMBEDDER_INSTANCE


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    metadata: Dict[str, Any]
    score: float
    dense_sim: float
    bm25_score: float


@dataclass
class RetrievalResult:
    chunks: List[RetrievedChunk] = field(default_factory=list)
    primary_citation_url: str = CANONICAL_LINKS["ADVISORY"]
    primary_doc_date: str = ""
    is_out_of_corpus: bool = False
    max_similarity: float = 0.0


class HybridRetriever:
    """Orchestrates dense ChromaDB / Pinecone search, lexical BM25 search, and RRF fusion."""

    def __init__(
        self,
        chroma_dir: str = settings.CHROMA_DIR,
        data_dir: str = settings.DATA_DIR,
        tau: float = settings.RETRIEVAL_TAU,
        vector_db_type: str = settings.VECTOR_DB_TYPE,
        pinecone_api_key: str = settings.PINECONE_API_KEY,
        pinecone_index_name: str = settings.PINECONE_INDEX_NAME,
    ):
        self.tau = tau
        self.vector_db_type = vector_db_type.lower()
        self.pinecone_index = None

        if self.vector_db_type == "pinecone":
            if pinecone_api_key:
                try:
                    from pinecone import Pinecone
                    pc = Pinecone(api_key=pinecone_api_key)
                    self.pinecone_index = pc.Index(pinecone_index_name)
                except Exception:
                    self.vector_db_type = "chroma"
            else:
                self.vector_db_type = "chroma"

        self.chroma_client = chromadb.PersistentClient(path=chroma_dir)
        self.collection = self.chroma_client.get_collection("mutual_fund_facts")

        # Load BM25 index
        bm25_path = os.path.join(data_dir, "index", "bm25.pkl")
        self.bm25 = None
        self.bm25_chunks = []
        if os.path.exists(bm25_path):
            try:
                with open(bm25_path, "rb") as f:
                    bm25_data = pickle.load(f)
                    self.bm25 = bm25_data.get("bm25")
                    self.bm25_chunks = bm25_data.get("chunks", [])
            except Exception:
                pass

    def search(
        self,
        query: str,
        scheme_id: Optional[str] = None,
        top_k: int = settings.TOP_K_CHUNKS,
    ) -> RetrievalResult:
        """Executes metadata-filtered hybrid search with RRF fusion.

        Args:
            query: User search query.
            scheme_id: Optional scheme filter to prevent cross-scheme contamination.
            top_k: Number of candidate chunks to return.

        Returns:
            RetrievalResult containing ranked chunks and primary citation URL.
        """
        embedder = get_embedder()
        clean_query = query.strip()
        query_embedding = embedder.encode([clean_query]).tolist()

        # 1. Metadata Pre-Filter (Eliminates 100% of cross-scheme contamination)
        dense_where = {"scheme_id": scheme_id} if scheme_id else None

        # Determine retrieval depth
        fetch_k = min(20, self.collection.count())
        if fetch_k == 0:
            return RetrievalResult(
                chunks=[],
                primary_citation_url=CANONICAL_LINKS["ADVISORY"],
                is_out_of_corpus=True,
                max_similarity=0.0,
            )

        # 2. Dense Vector Search (Pinecone or ChromaDB)
        dense_ranks: Dict[str, int] = {}
        dense_sims: Dict[str, float] = {}
        dense_docs: Dict[str, Dict[str, Any]] = {}

        if self.vector_db_type == "pinecone" and self.pinecone_index is not None:
            filter_dict = {"scheme_id": {"$eq": scheme_id}} if scheme_id else None
            pine_res = self.pinecone_index.query(
                vector=query_embedding[0],
                filter=filter_dict,
                top_k=fetch_k,
                include_metadata=True,
            )
            for rank, match in enumerate(getattr(pine_res, "matches", []) or []):
                cid = match.id
                sim = max(0.0, float(getattr(match, "score", 0.0)))
                dense_ranks[cid] = rank
                dense_sims[cid] = sim
                meta = getattr(match, "metadata", {}) or {}
                dense_docs[cid] = {
                    "text": meta.get("text", ""),
                    "metadata": meta,
                }
        else:
            dense_res = self.collection.query(
                query_embeddings=query_embedding,
                where=dense_where,
                n_results=fetch_k,
            )
            if dense_res and dense_res["ids"] and len(dense_res["ids"][0]) > 0:
                for rank, cid in enumerate(dense_res["ids"][0]):
                    dist = (
                        dense_res["distances"][0][rank]
                        if dense_res.get("distances")
                        else 0.0
                    )
                    sim = max(0.0, 1.0 - dist)
                    dense_ranks[cid] = rank
                    dense_sims[cid] = sim
                    dense_docs[cid] = {
                        "text": dense_res["documents"][0][rank],
                        "metadata": dense_res["metadatas"][0][rank],
                    }

        max_dense_sim = max(dense_sims.values()) if dense_sims else 0.0

        # 3. Lexical BM25 Search
        bm25_ranks: Dict[str, int] = {}
        bm25_scores: Dict[str, float] = {}

        if self.bm25 and self.bm25_chunks:
            tokens = [t.lower() for t in clean_query.split() if t.isalnum()]
            if tokens:
                raw_bm25_scores = self.bm25.get_scores(tokens)
                # Filter by scheme_id if specified
                scored_chunks = []
                for idx, sc in enumerate(raw_bm25_scores):
                    chunk_meta = self.bm25_chunks[idx].get("metadata", {})
                    if scheme_id and chunk_meta.get("scheme_id") != scheme_id:
                        continue
                    scored_chunks.append((idx, sc))

                scored_chunks.sort(key=lambda x: x[1], reverse=True)
                for rank, (c_idx, b_score) in enumerate(scored_chunks[:fetch_k]):
                    cid = self.bm25_chunks[c_idx]["chunk_id"]
                    bm25_ranks[cid] = rank
                    bm25_scores[cid] = float(b_score)
                    if cid not in dense_docs:
                        dense_docs[cid] = {
                            "text": self.bm25_chunks[c_idx]["text"],
                            "metadata": self.bm25_chunks[c_idx]["metadata"],
                        }

        # 4. Confidence Threshold Check (EC-RET-02 & EVAL-P3.3)
        # When scheme_id is None (unindexed AMC or unrelated domain query), enforce strict
        # dense cosine similarity >= self.tau (0.70) to prevent false retrieval.
        # When scheme_id is provided, the query is bounded to a verified in-corpus scheme;
        # only reject if similarity is negligible (< 0.30) and lexical search finds no keyword match.
        if scheme_id is None:
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
                )

        # 5. Reciprocal Rank Fusion (RRF k=60)
        rrf_scores: Dict[str, float] = {}
        all_candidate_ids = set(dense_ranks.keys()) | set(bm25_ranks.keys())

        for cid in all_candidate_ids:
            score = 0.0
            if cid in dense_ranks:
                score += 1.0 / (60.0 + dense_ranks[cid])
            if cid in bm25_ranks:
                score += 1.0 / (60.0 + bm25_ranks[cid])
            rrf_scores[cid] = score

        # Rank candidates by fused score
        sorted_candidates = sorted(
            rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True
        )

        top_chunks: List[RetrievedChunk] = []
        for cid in sorted_candidates[:top_k]:
            doc_info = dense_docs[cid]
            top_chunks.append(
                RetrievedChunk(
                    chunk_id=cid,
                    text=doc_info["text"],
                    metadata=doc_info["metadata"],
                    score=rrf_scores[cid],
                    dense_sim=dense_sims.get(cid, 0.0),
                    bm25_score=bm25_scores.get(cid, 0.0),
                )
            )

        # 6. Primary Citation URL and Date Selection
        primary_url = CANONICAL_LINKS["ADVISORY"]
        primary_doc_date = get_default_corpus_date()
        if top_chunks:
            primary_chunk = top_chunks[0]
            primary_url = primary_chunk.metadata.get("url", primary_url)
            primary_doc_date = normalize_date_footer(
                primary_chunk.metadata.get("doc_date")
            )

        return RetrievalResult(
            chunks=top_chunks,
            primary_citation_url=primary_url,
            primary_doc_date=primary_doc_date,
            is_out_of_corpus=False,
            max_similarity=max_dense_sim,
        )


def get_not_found_response(last_updated: Optional[str] = None) -> Dict[str, Any]:
    """Generates deterministic safe fallback when query cannot be answered from corpus."""
    body = (
        "I could not find official information regarding this topic in our verified "
        "HDFC Mutual Fund records."
    )
    url = CANONICAL_LINKS["ADVISORY"]
    doc_date = last_updated or get_default_corpus_date()
    rendered = f"{body}\n\nSource: {url}\nLast updated from sources: {doc_date}"

    return {
        "text": body,
        "citation_url": url,
        "last_updated": doc_date,
        "rendered": rendered,
        "is_not_found": True,
    }
