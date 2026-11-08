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

from collections import defaultdict, deque
import json
import time
from fastapi import Request
from fastapi.responses import JSONResponse

# Per-IP Rate Limiter: 20 requests per minute
_IP_REQUEST_TIMESTAMPS: dict[str, deque] = defaultdict(deque)

@app.middleware("http")
async def rate_limit_and_input_guard_middleware(request: Request, call_next):
    # 1. Per-IP Rate Limiting (20 req/min on /api/ endpoints)
    if request.url.path.startswith("/api/") and not request.url.path.endswith("/health"):
        client_ip = request.headers.get("x-forwarded-for") or (request.client.host if request.client else "127.0.0.1")
        now = time.time()
        ts_queue = _IP_REQUEST_TIMESTAMPS[client_ip]
        while ts_queue and ts_queue[0] <= now - 60.0:
            ts_queue.popleft()
        if len(ts_queue) >= 20:
            return JSONResponse(
                status_code=429,
                content={"error": "rate limit exceeded", "retry_after": 60},
                headers={"Retry-After": "60"},
            )
        ts_queue.append(now)

    # 2. Max Input Length Guard (1,000 characters)
    body_bytes = b""
    if request.method in ("POST", "PUT", "PATCH") and request.url.path.startswith("/api/"):
        body_bytes = await request.body()
        if body_bytes:
            try:
                body_json = json.loads(body_bytes.decode("utf-8", errors="replace"))
                query_val = body_json.get("query", "")
                if isinstance(query_val, str) and len(query_val) > 1000:
                    return JSONResponse(
                        status_code=400,
                        content={"error": "query too long", "max_chars": 1000},
                    )
            except Exception:
                pass

        async def receive():
            return {"type": "http.request", "body": body_bytes}

        request = Request(request.scope, receive=receive)

    return await call_next(request)


# CORS configuration - robust handling of list, comma-separated string, or wildcard
if isinstance(settings.CORS_ORIGINS, list):
    origins = settings.CORS_ORIGINS
elif isinstance(settings.CORS_ORIGINS, str):
    origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
else:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=("*" not in origins),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(guardrails_router)
app.include_router(rag_router)
app.include_router(threads_router)

@app.get("/health")
@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "llm_provider": "groq",
        "llm_model": settings.GROQ_MODEL,
        "amc": "HDFC Mutual Fund",
        "schemes_count": 5
    }

@app.get("/api/v1/facts/schemes")
def get_scheme_facts_list():
    """Returns verified statutory scheme facts directly from facts.db."""
    from app.rag.facts import get_all_scheme_facts_from_db
    return {"schemes": get_all_scheme_facts_from_db()}

@app.get("/api/v1/meta")
def get_metadata():
    return {
        "disclaimer": "Facts-only. No investment advice.",
        "amc": "HDFC Mutual Fund",
        "starter_questions": [
            "What is the exit load for HDFC Mid-Cap Opportunities Fund?",
            "What is the minimum SIP amount for HDFC Small Cap Fund?",
            "What is the lock-in period for ELSS mutual funds?"
        ],
        "schemes": [
            {"id": "hdfc_midcap_dg", "name": "HDFC Mid-Cap Opportunities Fund (Direct - Growth)"},
            {"id": "hdfc_smallcap_dg", "name": "HDFC Small Cap Fund (Direct - Growth)"},
            {"id": "hdfc_largecap_dg", "name": "HDFC Top 100 Fund (Direct - Growth)"},
            {"id": "hdfc_silver_fof_dg", "name": "HDFC Silver ETF FoF (Direct - Growth)"},
            {"id": "hdfc_multicap_dg", "name": "HDFC Multi Cap Fund (Direct - Growth)"}
        ]
    }

# Mount static frontend build in production if available
import os
from fastapi.staticfiles import StaticFiles

_static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.isdir(_static_dir):
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")

