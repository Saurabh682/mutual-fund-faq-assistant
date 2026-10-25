"""Guardrail API Endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.guardrails.pii import PII_SECURITY_WARNING, scan_pii
from app.guardrails.intent import classify_intent
from app.guardrails.refusal import CANONICAL_LINKS, generate_refusal, get_default_corpus_date
from app.schemas.guardrails import GuardrailScanRequest, GuardrailScanResponse

router = APIRouter(prefix="/api/v1/guardrails", tags=["Guardrails"])


@router.post("/scan", response_model=GuardrailScanResponse)
def scan_query(request: GuardrailScanRequest):
    """Scan query for PII and classify intent.

    If PII is detected, returns HTTP 400 Bad Request with security warning.
    If intent is advisory/comparative/projection/tax_legal, returns deterministic refusal.
    """
    has_pii, detected_types, redacted = scan_pii(request.text)

    # 1. Deterministic PII Firewall Block (HTTP 400)
    if has_pii:
        doc_date = get_default_corpus_date()
        citation = CANONICAL_LINKS["ADVISORY"]
        rendered_warning = (
            f"{PII_SECURITY_WARNING}\n\n"
            f"Source: {citation}\n"
            f"Last updated from sources: {doc_date}"
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "PII_DETECTED",
                "message": PII_SECURITY_WARNING,
                "detected_types": detected_types,
                "redacted_text": redacted,
                "rendered": rendered_warning,
            },
        )

    # 2. Intent Classification
    intent_res = classify_intent(request.text)

    refusal_payload = None
    rendered = None

    if intent_res.is_refusal:
        refusal_payload = generate_refusal(intent_res.intent)
        rendered = refusal_payload["rendered"]

    return GuardrailScanResponse(
        has_pii=False,
        detected_pii=[],
        redacted_text=redacted,
        intent=intent_res.intent,
        is_refusal=intent_res.is_refusal,
        is_compound=intent_res.is_compound,
        refusal_response=refusal_payload,
        rendered_response=rendered,
    )
