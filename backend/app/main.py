from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.guardrails import router as guardrails_router
from app.api.rag import router as rag_router
from app.api.threads import router as threads_router

app = FastAPI(
    title="Mutual Fund FAQ Assistant API",
    description="Deterministic facts-only Q&A assistant for HDFC Mutual Fund schemes operating under SEBI guidelines.",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(guardrails_router)
app.include_router(rag_router)
app.include_router(threads_router)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "llm_provider": "groq",
        "llm_model": settings.GROQ_MODEL,
        "amc": "HDFC Mutual Fund",
        "schemes_count": 5
    }

@app.get("/api/v1/meta")
def get_metadata():
    return {
        "disclaimer": "Facts-only. No investment advice.",
        "amc": "HDFC Mutual Fund",
        "starter_questions": [
            "What is the exit load for HDFC Mid-Cap Opportunities Fund?",
            "What is the minimum SIP amount for HDFC Small Cap Fund?",
            "How do I download my Capital Gains statement on Groww?"
        ],
        "schemes": [
            {"id": "hdfc_midcap_dg", "name": "HDFC Mid-Cap Opportunities Fund (Direct - Growth)"},
            {"id": "hdfc_smallcap_dg", "name": "HDFC Small Cap Fund (Direct - Growth)"},
            {"id": "hdfc_largecap_dg", "name": "HDFC Top 100 Fund (Direct - Growth)"},
            {"id": "hdfc_silver_fof_dg", "name": "HDFC Silver ETF FoF (Direct - Growth)"},
            {"id": "hdfc_multicap_dg", "name": "HDFC Multi Cap Fund (Direct - Growth)"}
        ]
    }
