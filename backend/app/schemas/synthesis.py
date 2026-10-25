"""Pydantic schemas for LLM Synthesis and End-to-End Answering."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.rag import ChunkDetail


class SynthesisQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="User question")
    session_scheme_id: Optional[str] = Field(
        None, description="Active scheme_id from thread history for pronoun resolution"
    )


class SynthesisQueryResponse(BaseModel):
    query: str
    resolution_type: str = Field(
        ...,
        description="Path that resolved the answer: 'fact_store' | 'llm_synthesis' | 'refusal' | 'clarification' | 'not_found'",
    )
    scheme_id: Optional[str] = None
    scheme_name: Optional[str] = None
    field: Optional[str] = None
    text: str
    sentence_count: int
    citation_url: str
    last_updated: str
    rendered: str
    repaired: bool = False
    repair_count: int = 0
    latency_ms: float
    chunks: List[ChunkDetail] = Field(default_factory=list)
