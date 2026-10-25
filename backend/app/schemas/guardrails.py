"""Schemas for Guardrail & Compliance Firewall Layer."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GuardrailScanRequest(BaseModel):
    text: str = Field(..., min_length=1, description="User input text to scan.")


class GuardrailScanResponse(BaseModel):
    has_pii: bool
    detected_pii: List[str] = Field(default_factory=list)
    redacted_text: str
    intent: str
    is_refusal: bool
    is_compound: bool = False
    refusal_response: Optional[Dict[str, Any]] = None
    rendered_response: Optional[str] = None


class PIIBlockedResponse(BaseModel):
    error: str = "PII_DETECTED"
    message: str
    detected_types: List[str]
    redacted_text: str
    rendered: str
