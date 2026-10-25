"""Schemas for RAG, Entity Resolution, and Fact Store APIs."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RetrievalQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User search or FAQ question.")
    session_scheme_id: Optional[str] = Field(
        default=None, description="Active scheme_id from thread session for pronoun resolution."
    )
    top_k: int = Field(default=4, ge=1, le=10, description="Number of chunks to retrieve.")


class ChunkDetail(BaseModel):
    chunk_id: str
    text: str
    metadata: Dict[str, Any]
    score: float
    dense_sim: float
    bm25_score: float


class RetrievalQueryResponse(BaseModel):
    query: str
    resolution_type: str = Field(
        ..., description="Type of resolution: 'fact_store', 'hybrid_retrieval', 'clarification', 'not_found', 'refusal'"
    )
    scheme_id: Optional[str] = None
    scheme_name: Optional[str] = None
    field: Optional[str] = None
    text: str
    citation_url: str
    last_updated: str
    rendered: str
    chunks: List[ChunkDetail] = Field(default_factory=list)
    latency_ms: float = 0.0
