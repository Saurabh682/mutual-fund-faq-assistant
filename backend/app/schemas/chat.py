"""Pydantic schemas for Multi-Thread Chat, Messages, and Session Management."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MessageDTO(BaseModel):
    id: str = Field(..., description="Unique message ID")
    role: str = Field(..., description="'user' | 'assistant'")
    type: str = Field(
        ...,
        description="'answer' | 'refusal' | 'pii_block' | 'clarification' | 'not_found' | 'fact_store' | 'llm_synthesis'",
    )
    text: str = Field(..., description="Body of the message")
    sentence_count: Optional[int] = Field(None, description="Sentence count of the response")
    citation_url: Optional[str] = Field(None, description="Canonical single citation URL")
    last_updated: Optional[str] = Field(None, description="Document freshness timestamp (YYYY-MM-DD)")
    rendered: Optional[str] = Field(None, description="Complete rendered message with citation and footer")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    latency_ms: Optional[float] = Field(None, description="Processing latency in milliseconds")


class ThreadSummaryDTO(BaseModel):
    id: str = Field(..., description="Unique thread ID")
    client_id: str = Field(..., description="Client identifier")
    title: str = Field(..., description="Thread title")
    last_scheme_id: Optional[str] = Field(None, description="Active scheme_id for conversation continuity")
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class ThreadDTO(BaseModel):
    id: str = Field(..., description="Unique thread ID")
    client_id: str = Field(..., description="Client identifier")
    title: str = Field(..., description="Thread title")
    last_scheme_id: Optional[str] = Field(None, description="Active scheme_id for conversation continuity")
    created_at: datetime
    updated_at: datetime
    messages: List[MessageDTO] = Field(default_factory=list)


class CreateThreadRequest(BaseModel):
    client_id: Optional[str] = Field("default_client", description="Client identifier")
    title: Optional[str] = Field("New Conversation", description="Initial thread title")


class ChatRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500, description="User question")


class MetaResponse(BaseModel):
    amc: str = "HDFC Mutual Fund"
    schemes: List[Dict[str, Any]]
    disclaimer: str = "Facts-only. No investment advice."
    starter_questions: List[str]
    last_refreshed: str
