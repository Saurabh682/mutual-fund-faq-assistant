---
title: Mutual Fund FAQ Assistant
emoji: 📈
colorFrom: green
colorTo: indigo
sdk: gradio
sdk_version: 5.20.0
app_file: app.py
pinned: false
license: mit
---

# 📊 Mutual Fund FAQ Assistant (Facts-Only Q&A)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19.0+-61DAFB.svg)](https://react.dev/)
[![Tailwind CSS v4](https://img.shields.io/badge/Tailwind-v4.0-38B2AC.svg)](https://tailwindcss.com/)
[![Groq LLM](https://img.shields.io/badge/LLM-Groq%20qwen3.8--27b-F55036.svg)](https://groq.com/)
[![Eval Benchmark](https://img.shields.io/badge/Golden%20Eval-59%2F59%20(100%25)-brightgreen.svg)](#-evaluation-benchmark-results)

> An AI-powered, retrieval-augmented generation (RAG) assistant for mutual fund schemes with Groww as the reference product context.
> Built on the foundational principle: **"Accuracy over Intelligence"** — deterministic, factual, verifiable answers backed strictly by official regulatory and AMC sources.

---

## 🎯 Target Schemes & Reference Corpus (HDFC Mutual Fund)

The assistant's corpus is strictly bounded to **5 official HDFC Mutual Fund Direct-Growth schemes** (no unverified external data sources):

1. **Mid-Cap**: [HDFC Mid-Cap Opportunities Fund (Direct - Growth)](https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth)
2. **Small-Cap**: [HDFC Small Cap Fund (Direct - Growth)](https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth)
3. **Large-Cap**: [HDFC Top 100 Fund (Direct - Growth)](https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth)
4. **Precious Metals FoF**: [HDFC Silver ETF FoF (Direct - Growth)](https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth)
5. **Multi-Cap**: [HDFC Multi Cap Fund (Direct - Growth)](https://groww.in/mutual-funds/hdfc-multi-cap-fund-direct-growth)

Official regulatory and investor guidance allowlist:
- [AMFI India Knowledge Center](https://www.amfiindia.com/investor-corner/knowledge-center)
- [SEBI Investor Protection & Riskometer Circulars](https://sebi.gov.in)
- [CAMS Online Statement Services](https://www.camsonline.com)

---

## 🛡️ Response Contract & SEBI Regulatory Invariants

Every assistant response adheres to the strict **5-Point Response Contract**:

1. **Sentence Count Ceiling**: $\le 3$ sentences maximum. Period-protection regex guarantees decimal NAVs (e.g. `₹102.50`) and abbreviations (e.g. `Rs.`, `vs.`) do not split sentences prematurely.
2. **Single Canonical Citation**: Exactly 1 verified official source URL from the whitelist appended as `Source: <url>`.
3. **Standardized Date Footer**: Final line strictly matches `^Last updated from sources: \d{4}-\d{2}-\d{2}$`.
4. **Zero Investment Advice (SEBI Fail-Closed Gate)**: 100% deterministic, non-LLM refusals on advisory, comparative, projection, or tax evasion queries, redirecting users to the AMFI Knowledge Center.
5. **PII Firewall**: Immediate HTTP 400 rejection and zero logging on PAN, Aadhaar (Verhoeff checksum validated), bank accounts, IFSC, OTP, passwords, or folio numbers.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    User([Retail Investor / User]) --> UI[React 19 + Tailwind CSS Frontend]
    UI -->|POST /threads/{id}/messages| API[FastAPI Gateway :8000]

    subgraph Guardrails_In ["Input Guardrails Layer"]
        API --> PII[PII Firewall & Verhoeff Checksum]
        PII -->|PII Detected| HTTP400[HTTP 400 + Redacted Warning]
        PII -->|Clean Query| Intent[Intent Classifier]
        Intent -->|Advisory / Comparative / Tax| DetRefusal[Deterministic Refusal Engine]
    end

    subgraph Core_Orchestrator ["Orchestration & Retrieval"]
        Intent -->|Factual / Procedural| EntRes[Entity & Scheme Resolver]
        EntRes -->|Canonical Metric Hit| FactDB[(SQLite Fact Store facts.db)]
        EntRes -->|Passage Needed| HybridRet[Hybrid Retriever: ChromaDB + BM25 + RRF]
        HybridRet -->|Confidence < tau| SafeFallback[Out-of-Corpus Fallback]
    end

    subgraph Synthesis_Guardrails ["Synthesis & Output Validation"]
        FactDB --> DirectRender[O 1 Template Response]
        HybridRet --> GroqLLM[Groq LLM: qwen/qwen3.8-27b]
        GroqLLM --> OutputVal[5-Point Contract Validator]
        OutputVal -->|Pass| ValidOut[Response + Source + Date Footer]
        OutputVal -->|Violation| RepairLoop[LLM Repair Prompt Loop max 2]
    end

    ValidOut --> SessionStore[(SQLite Session Store sessions.db)]
    ValidOut --> AuditLog[Tamper-Evident Zero-PII Audit Log]
    ValidOut --> UI
    DetRefusal --> UI
    DirectRender --> UI
```

---

## 💻 Technology Stack

| Layer | Component | Choice | Rationale |
|---|---|---|---|
| **Frontend** | Framework | **React 19 + TypeScript + Vite** | Instant HMR, zero-bundle overhead, modern component model. |
| | Styling | **Tailwind CSS v4** | Dark/Light emerald terminal theme, WCAG 2.1 AA compliant. |
| | State | **Zustand** | Lightweight thread management, optimistic updates, zero boilerplate. |
| **Backend** | Framework | **FastAPI + Uvicorn** (Python 3.11+) | Async high-throughput REST API with automatic OpenAPI documentation. |
| | Guardrails | **Custom Regex + Verhoeff Algorithm** | Sub-millisecond deterministic PII firewall and compliance routing. |
| | LLM Engine | **Groq (`qwen/qwen3.8-27b`)** | Sub-second latency, deterministic temperature 0.0, factual phrasing. |
| | Embeddings | **`sentence-transformers/all-MiniLM-L6-v2`** | 384-dimensional dense vectors with sub-10ms local inference. |
| | Vector DB | **ChromaDB** | In-memory / persistent vector index with metadata pre-filtering. |
| | Keyword DB | **BM25 (`rank-bm25`)** | Lexical search combined with dense cosine via Reciprocal Rank Fusion ($k=60$). |
| | Fact Store | **SQLite (`facts.db`)** | Deterministic O(1) canonical metric retrieval ($< 15\text{ ms}$). |
| | Sessions | **SQLite (`sessions.db`)** | Multi-thread persistence with `asyncio.Lock` concurrency locks. |

---

## 📁 Repository Layout

```
mutual-fund-faq-assistant/
├── backend/
│   ├── app/
│   │   ├── api/              # API Routers (threads.py, rag.py, guardrails.py)
│   │   ├── audit/            # Tamper-evident zero-PII audit logger
│   │   ├── core/             # Pydantic BaseSettings & configuration
│   │   ├── guardrails/       # PII firewall, intent classifier, refusal engine, validator
│   │   ├── rag/              # Hybrid retriever, fact store, entities, synthesizer, prompts
│   │   ├── schemas/          # Pydantic request & response models
│   │   ├── sessions/         # Multi-thread SQLite session store with locking
│   │   └── main.py           # FastAPI entrypoint
│   ├── tests/                # 229 pytest unit & integration tests
│   ├── Dockerfile            # Python 3.11-slim production container
│   ├── pytest.ini            # Pytest configuration
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/       # Header, DisclaimerBanner, MessageFeed, Composer, etc.
│   │   ├── store/            # Zustand chatStore (threads, messages, streaming state)
│   │   ├── types/            # TypeScript interfaces
│   │   ├── api/client.ts     # Typed REST client
│   │   └── App.tsx           # Main application root
│   ├── nginx.conf            # Reverse proxy & static assets configuration
│   ├── Dockerfile            # Multi-stage Node.js build with Alpine Nginx
│   └── vite.config.ts        # Vite configuration with Tailwind CSS v4
├── data/
│   ├── corpus_manifest.yaml  # Canonical sources, scheme IDs, and refresh timestamps
│   ├── index/
│   │   ├── chroma/           # Dense ChromaDB vector collection
│   │   ├── bm25.pkl          # BM25 lexical index & chunk metadata
│   │   └── facts.db          # SQLite canonical facts table
│   └── audit.jsonl           # Persistent audit ledger
├── eval/
│   ├── datasets/             # 59-item golden benchmark evaluation dataset
│   ├── reports/              # Markdown evaluation scorecard & audit reports
│   └── run_eval.py           # Automated evaluation runner
├── docs/                     # Specifications (architecture, implementation, edge-cases, eval)
├── docker-compose.yml        # Orchestration compose file for backend and frontend
└── README.md                 # Project root documentation
```

---

## ⚡ Quick Start & Installation

### Prerequisites
- Python 3.11+
- Node.js 20+ & npm
- Groq API Key (`GROQ_API_KEY`)
- Docker & Docker Compose *(optional, for containerized run)*

### Option A: Local Development Run

#### 1. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # On Windows: .\.venv\Scripts\activate
pip install -r requirements.txt

# Configure Environment
cp .env.example .env
# Edit .env and insert your GROQ_API_KEY

# Start Backend Server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be available at: `http://localhost:8000/docs`

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Web Application will be live at: `http://localhost:5173`

---

### Option B: Docker Compose Deployment

```bash
# Set your Groq API Key
export GROQ_API_KEY="gsk_..."  # On Windows PowerShell: $env:GROQ_API_KEY="gsk_..."

# Build and start services
docker-compose up --build -d
```
- Web UI: `http://localhost`
- Backend API & Health: `http://localhost:8000/health`

---

## 🧪 Evaluation Benchmark Results

The system is continuously verified against a comprehensive 59-item Golden Evaluation Dataset (`eval/datasets/golden_mf_eval.jsonl`) covering all edge cases, compliance boundaries, and performance benchmarks.

### Executive Metric Scorecard

| Metric | Target | Result | Status |
|---|---|---|---|
| **Overall Benchmark Accuracy** | $\ge 95\%$ | **100.0%** (59/59) | ✅ **PASS** |
| **Advisory Refusal Recall** | $100\%$ | **100.0%** (7/7) | ✅ **PASS** |
| **Comparative Refusal Recall** | $100\%$ | **100.0%** (5/5) | ✅ **PASS** |
| **Projection Refusal Recall** | $100\%$ | **100.0%** (3/3) | ✅ **PASS** |
| **Tax/Legal Evasion Refusal** | $100\%$ | **100.0%** (2/2) | ✅ **PASS** |
| **PII Detection & Redaction** | $100\%$ | **100.0%** (5/5, 0 Leaks) | ✅ **PASS** |
| **Output Contract Adherence** | $100\%$ | **100.0%** ($\le 3$ sentences, 1 URL, valid date) | ✅ **PASS** |
| **Out-of-Corpus Fallback** | $100\%$ | **100.0%** (5/5) | ✅ **PASS** |
| **Ambiguity Disambiguation** | $100\%$ | **100.0%** (2/2) | ✅ **PASS** |
| **Fact Store Latency (p50)** | $< 50\text{ ms}$ | **7.0 ms** | ✅ **PASS** |
| **Overall Latency (p95)** | $< 2000\text{ ms}$ | **263.4 ms** | ✅ **PASS** |

### Running the Evaluation Suite
```bash
# Run full automated evaluation harness
cd mutual-fund-faq-assistant
$env:PYTHONPATH="backend"
python eval/run_eval.py

# Run full pytest test suite (229 tests)
pytest backend/tests -v
```

---

## 📡 API Usage Examples

### 1. Ask a Factual Question (Instant Fact Store Path)
```bash
curl -X POST http://localhost:8000/api/v1/rag/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the exit load for HDFC Mid-Cap Opportunities Fund?"}'
```
**Response:**
```json
{
  "query": "What is the exit load for HDFC Mid-Cap Opportunities Fund?",
  "resolution_type": "fact_store",
  "scheme_id": "hdfc_midcap_dg",
  "scheme_name": "HDFC Mid-Cap Opportunities Fund",
  "field": "exit_load",
  "text": "The exit load for HDFC Mid-Cap Opportunities Fund is Exit load of 1% if redeemed within 1 year.",
  "sentence_count": 1,
  "citation_url": "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
  "last_updated": "2026-10-23",
  "rendered": "The exit load for HDFC Mid-Cap Opportunities Fund is Exit load of 1% if redeemed within 1 year.\n\nSource: https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth\nLast updated from sources: 2026-10-23",
  "latency_ms": 6.8
}
```

### 2. Advisory Query (Deterministic Compliance Refusal)
```bash
curl -X POST http://localhost:8000/api/v1/rag/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Should I invest in HDFC Small Cap Fund?"}'
```
**Response:**
```json
{
  "query": "Should I invest in HDFC Small Cap Fund?",
  "resolution_type": "refusal",
  "text": "I can only provide objective, factual information regarding mutual fund schemes and cannot offer investment advice, comparisons, or recommendations. For guidance on fund selection and financial planning, please consult a SEBI-registered investment advisor or review educational resources.",
  "sentence_count": 2,
  "citation_url": "https://www.amfiindia.com/investor-corner/knowledge-center",
  "last_updated": "2026-10-25",
  "rendered": "I can only provide objective, factual information regarding mutual fund schemes and cannot offer investment advice, comparisons, or recommendations. For guidance on fund selection and financial planning, please consult a SEBI-registered investment advisor or review educational resources.\n\nSource: https://www.amfiindia.com/investor-corner/knowledge-center\nLast updated from sources: 2026-10-25"
}
```

### 3. PII Detection (Immediate HTTP 400 Block)
```bash
curl -X POST http://localhost:8000/api/v1/rag/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "My PAN is ABCPE1234F, show my account details."}'
```
**Response:**
```json
{
  "error": "PII_DETECTED",
  "message": "Security Alert: Personally Identifiable Information (PAN, Aadhaar, Account Numbers, OTP, Passwords, or Folio Numbers) was detected in your query. For your security, this query was rejected and no data has been logged.",
  "detected_types": ["PAN"],
  "redacted_text": "My PAN is [PAN_REDACTED], show my account details."
}
```

---

## ⚖️ License & Compliance Disclaimer

This software is designed solely for educational and informational purposes as a mutual fund facts Q&A assistant referencing Groww experience. It does not constitute investment advice, financial solicitation, or portfolio management. Mutual fund investments are subject to market risks; read all scheme related documents carefully.
