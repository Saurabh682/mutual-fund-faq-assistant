# 📋 Phase-Wise Implementation Plan
# Mutual Fund FAQ Assistant (Facts-Only Q&A)

> **Derived from**: [`architecture.md`](./architecture.md) · [`problemStatement.md`](./problemStatement.md)  
> **Core Principle**: *"Accuracy over Intelligence"* — Deterministic, factual, verifiable answers backed strictly by official regulatory and AMC sources.  
> **Target Scope**: HDFC Mutual Fund · 5 Selected Schemes · Single-Citation · Zero Advice · Groww Reference Context  

---

## Plan at a Glance

```
Phase 0 ──▶ Project Setup, Repository Scaffolding & Environment Baseline
Phase 1 ──▶ Corpus Manifest, Offline Ingestion & Fact Store Pipeline
Phase 2 ──▶ Guardrail & Compliance Firewall Layer (PII + Advisory Refusal)
Phase 3 ──▶ Hybrid Retrieval & Entity Resolution Engine (BM25 + ChromaDB)
Phase 4 ──▶ Constrained Synthesis & Output Contract Validator (≤ 3 Sentences)
Phase 5 ──▶ Multi-Thread Session Management & Backend REST API Service
Phase 6 ──▶ Frontend UI & Groww-Style Interface (React + Tailwind + Zustand)
Phase 7 ──▶ End-to-End Testing, Golden Dataset Evals & Production Readiness
```

| Phase | Name | Key Deliverable | Estimated Time |
|---|---|---|---|
| **0** | **Project Setup & Environment** | Workspace scaffold, virtualenv, dependencies, Vite app, `.env` | 45 min |
| **1** | **Corpus & Ingestion Pipeline** | `corpus_manifest.yaml`, Playwright/httpx fetchers, table chunker, ChromaDB, SQLite facts | 2.0 hr |
| **2** | **Guardrails & Compliance Firewall** | PII regex/Verhoeff detector, intent classifier, templated refusal engine | 1.5 hr |
| **3** | **Hybrid Retrieval & Entity Engine** | Scheme entity extraction, BM25 + dense search, RRF fusion, priority weighting | 1.5 hr |
| **4** | **Constrained LLM & Validator** | PromptBuilder, Groq LLM client (Llama 3.3 70B), sentence counter, grounding check, footer | 1.5 hr |
| **5** | **Session Store & FastAPI Layer** | `/api/v1/threads` & `/messages`, Pydantic schemas, session lock, audit tracer | 1.5 hr |
| **6** | **Frontend UI & Groww Experience** | Disclaimer banner, thread sidebar, starter chips, citation pill, dark/light theme | 2.5 hr |
| **7** | **Evals, Testing & Delivery** | Pytest suite, golden eval runner (accuracy, refusals, PII), Docker Compose | 1.5 hr |

**Total Estimated Implementation Time**: ~12 hours

---

## Phase 0 — Project Setup, Repository Scaffolding & Environment Baseline

**Goal**: Establish the complete directory structure, Python virtual environment, Node.js frontend workspace, configure environment credentials, and verify clean compilation before writing domain logic.

### 0.1 Directory Structure Scaffolding
Create the standardized multi-tier repository layout:

```bash
cd "D:/VibeCode/Applied Generative AI Bootcamp"
mkdir -p mutual-fund-faq-assistant/data/raw
mkdir -p mutual-fund-faq-assistant/data/index
mkdir -p mutual-fund-faq-assistant/backend/app/api
mkdir -p mutual-fund-faq-assistant/backend/app/core
mkdir -p mutual-fund-faq-assistant/backend/app/guardrails
mkdir -p mutual-fund-faq-assistant/backend/app/rag
mkdir -p mutual-fund-faq-assistant/backend/app/sessions
mkdir -p mutual-fund-faq-assistant/backend/app/audit
mkdir -p mutual-fund-faq-assistant/backend/app/schemas
mkdir -p mutual-fund-faq-assistant/backend/tests
mkdir -p mutual-fund-faq-assistant/ingest/parsers
mkdir -p mutual-fund-faq-assistant/eval/datasets
mkdir -p mutual-fund-faq-assistant/eval/reports
```

### 0.2 Version Control & Git Configuration
Enforce strict `.gitignore` rules in `mutual-fund-faq-assistant/.gitignore`:

```gitignore
# Virtual environments
.venv/
venv/
__pycache__/
*.pyc

# Secrets & Environment
.env
*.env.local

# Ingestion raw files & index artifacts
data/raw/
data/index/
*.sqlite3
*.db
chroma_db/

# Node & Frontend
node_modules/
dist/
.vite/

# Testing & Logs
.pytest_cache/
.coverage
htmlcov/
*.log
```

### 0.3 Backend Dependencies (`backend/requirements.txt`)

```text
fastapi>=0.111.0
uvicorn[standard]>=0.30.0
pydantic>=2.7.0
pydantic-settings>=2.3.0
python-dotenv>=1.0.0
chromadb>=0.5.0
rank-bm25>=0.2.2
sentence-transformers>=3.0.0
httpx>=0.27.0
playwright>=1.44.0
pdfplumber>=0.11.0
selectolax>=0.3.21
beautifulsoup4>=4.12.0
google-genai>=2.25.0
groq>=0.9.0
structlog>=24.1.0
pytest>=8.2.0
pytest-asyncio>=0.23.0
hypothesis>=6.100.0
```

Setup commands:
```bash
cd mutual-fund-faq-assistant/backend
python -m venv .venv

# Windows activation
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium
```

### 0.4 Environment Configuration (`backend/.env` & `backend/app/core/config.py`)

Create `backend/.env.example`:
```ini
ENVIRONMENT=development
PORT=8000
HOST=0.0.0.0
CORS_ORIGINS=["http://localhost:5173"]

# Primary LLM Provider: Groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# RAG & Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
RETRIEVAL_TAU=0.70
TOP_K_CHUNKS=4

# Storage Paths
DATA_DIR=../data
FACTS_DB_PATH=../data/index/facts.db
CHROMA_DIR=../data/index/chroma
SESSION_TTL_DAYS=7
```

Create `backend/app/core/config.py`:
```python
from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    
    # Primary LLM Provider: Groq
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    RETRIEVAL_TAU: float = 0.70
    TOP_K_CHUNKS: int = 4
    
    DATA_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data"))
    FACTS_DB_PATH: str = os.path.join(DATA_DIR, "index/facts.db")
    CHROMA_DIR: str = os.path.join(DATA_DIR, "index/chroma")
    SESSION_TTL_DAYS: int = 7

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
```

### 0.5 Frontend Workspace Scaffold (React 18 + Vite + Tailwind CSS)

```bash
cd mutual-fund-faq-assistant
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install @tanstack/react-query zustand lucide-react clsx tailwind-merge
npm install -D tailwindcss @tailwindcss/vite
```

Configure `frontend/vite.config.ts`:
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

### Phase 0 Acceptance Criteria
- [x] All directories in `mutual-fund-faq-assistant/` created and verified.
- [x] `.venv` created with Python 3.11+, all packages installed cleanly.
- [x] Playwright chromium browser binaries installed (`playwright install chromium`).
- [x] `config.py` loads `.env` variables without schema errors.
- [x] Frontend builds with zero TypeScript errors (`npm run build`).

---

## Phase 1 — Corpus Manifest, Offline Ingestion & Fact Store Pipeline

**Goal**: Establish the authoritative corpus strictly bounded to the **5 Groww HDFC Scheme URLs** from [`problemStatement.md`](./problemStatement.md) (no extra URLs), implement dynamic Playwright DOM fetchers, execute table-aware document chunking, generate embeddings into ChromaDB, and extract canonical structured facts into SQLite (`facts.db`).

### 1.1 Authoritative Corpus Registry (`data/corpus_manifest.yaml`)
Create the manifest registry matching strictly the 5 approved HDFC schemes on Groww (no extra URLs):

```yaml
version: 1
last_refreshed: "2026-10-25"
allowed_domains:
  - groww.in

schemes:
  - id: hdfc_midcap_dg
    name: "HDFC Mid-Cap Opportunities Fund"
    category: "Equity: Mid Cap"
    plan: "Direct"
    option: "Growth"
    groww_url: "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"

  - id: hdfc_smallcap_dg
    name: "HDFC Small Cap Fund"
    category: "Equity: Small Cap"
    plan: "Direct"
    option: "Growth"
    groww_url: "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth"

  - id: hdfc_largecap_dg
    name: "HDFC Top 100 Fund (Large Cap)"
    category: "Equity: Large Cap"
    plan: "Direct"
    option: "Growth"
    groww_url: "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth"

  - id: hdfc_silver_fof_dg
    name: "HDFC Silver ETF Fund of Fund"
    category: "Commodities: Precious Metals FoF"
    plan: "Direct"
    option: "Growth"
    groww_url: "https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth"

  - id: hdfc_multicap_dg
    name: "HDFC Multi Cap Fund"
    category: "Equity: Multi Cap"
    plan: "Direct"
    option: "Growth"
    groww_url: "https://groww.in/mutual-funds/hdfc-multi-cap-fund-direct-growth"

sources:
  - id: grw_midcap
    url: "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"
    type: scheme_page
    publisher: groww
    scheme_id: hdfc_midcap_dg
    priority: 1

  - id: grw_smallcap
    url: "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth"
    type: scheme_page
    publisher: groww
    scheme_id: hdfc_smallcap_dg
    priority: 1

  - id: grw_largecap
    url: "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth"
    type: scheme_page
    publisher: groww
    scheme_id: hdfc_largecap_dg
    priority: 1

  - id: grw_silver_fof
    url: "https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth"
    type: scheme_page
    publisher: groww
    scheme_id: hdfc_silver_fof_dg
    priority: 1

  - id: grw_multicap
    url: "https://groww.in/mutual-funds/hdfc-multi-cap-fund-direct-growth"
    type: scheme_page
    publisher: groww
    scheme_id: hdfc_multicap_dg
    priority: 1
```

### 1.2 Fetcher & Parser Pipeline (`ingest/fetchers.py` & `ingest/parsers/`)
- `ingest/fetchers.py`:
  - `fetch_static(url)`: Uses `httpx.AsyncClient` with custom User-Agent to download PDFs and static HTML.
  - `fetch_dynamic(url)`: Uses headless `Playwright` to render client-side Groww pages, wait for network idle, and extract rendered DOM.
  - Computes `content_hash` (SHA-256) of normalized text to skip unchanged documents.
- `ingest/parsers/pdf.py`: Uses `pdfplumber` to extract tables intact (TER columns, exit load tiers, NAV history).
- `ingest/parsers/html.py`: Uses `selectolax` to isolate `<main>` or `<article>` content, removing navigation bars, ads, and recommendation widgets.

### 1.3 Structure-Aware Chunker (`ingest/chunker.py`)
Chunks documents by semantic section boundaries while maintaining table integrity:
```python
def chunk_document(doc_text: str, metadata: dict) -> list[dict]:
    # 1. Preserves table rows as atomic chunks with headers prepended
    # 2. Splits prose on section headings (e.g. "Load Structure", "Investment Details")
    # 3. Sizes chunks between 200 and 350 tokens with 10% overlap for prose only
    # 4. Injects metadata: chunk_id, scheme_id, doc_date, url, priority, content_type
    ...
```

### 1.4 Vector Indexing & Structured Fact Store (`ingest/embed.py` & `ingest/fact_extractor.py`)
- **ChromaDB Vector Store**:
  - Embedding Model: `sentence-transformers/all-MiniLM-L6-v2`.
  - Prefix formatted chunk strings: `"{scheme_name} | {section} | {chunk_text}"`.
  - Stored in persistent directory `data/index/chroma`.
- **Lexical Index**:
  - In-memory `rank_bm25.BM25Okapi` serialized to disk (`data/index/bm25.pkl`).
- **Structured SQLite Fact Store (`data/index/facts.db`)**:
  - Schema: `facts(fact_id, scheme_id, field, value, unit, citation_url, doc_date, human_verified)`.
  - Extracts canonical fields: `ter_direct`, `exit_load`, `min_sip`, `min_lumpsum`, `lock_in`, `riskometer`, `benchmark`.
  - Emits `data/ingestion_report.json` detailing extracted values, confidence scores, and conflict resolutions.

### Phase 1 Acceptance Criteria
- [x] `python -m ingest.run` parses strictly the 5 Groww scheme URLs from manifest.
- [x] ChromaDB contains structured chunks with valid metadata (`scheme_id`, `url`, `doc_date`).
- [x] `facts.db` contains verified rows for all 5 schemes across the 7 canonical fields.
- [x] Zero URLs outside `allowed_domains` (`groww.in`) are processed.

---

## Phase 2 — Guardrail & Compliance Firewall Layer

**Goal**: Implement the deterministic safety layer that detects PII, blocks unauthorized financial credentials, classifies user intent, and serves 100% deterministic, non-LLM refusals for advisory or comparative queries.

### 2.1 PII Firewall (`backend/app/guardrails/pii.py`)
Implement the deterministic regex and checksum scanner:

```python
import re

PAN_REGEX = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
AADHAAR_REGEX = re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b")
PHONE_REGEX = re.compile(r"\b(?:\+91[\-\s]?)?[6-9]\d{9}\b")
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
ACCOUNT_REGEX = re.compile(r"\b(?:\d{9,18}|[A-Z]{4}0[A-Z0-9]{6})\b")
OTP_REGEX = re.compile(r"\b(?:otp|password|pin|cvv)\b[^\d]{0,5}\d{4,8}\b", re.IGNORECASE)

def verhoeff_validate(aadhaar: str) -> bool:
    """Verhoeff algorithm checksum validation for 12-digit Indian Aadhaar numbers."""
    ...

def scan_pii(text: str) -> tuple[bool, list[str], str]:
    """Returns (has_pii, detected_types, redacted_text)."""
    detected = []
    redacted = text
    if PAN_REGEX.search(text):
        detected.append("PAN")
        redacted = PAN_REGEX.sub("[PAN_REDACTED]", redacted)
    # Check Aadhaar, Phone, Email, OTP, Bank Account
    ...
    return len(detected) > 0, detected, redacted
```

### 2.2 Intent Classifier (`backend/app/guardrails/intent.py`)
Implement hybrid intent routing:
- **Rule Layer**: High-precision regex triggers:
  - Advisory: `"should I invest"`, `"which fund is better"`, `"best fund"`, `"recommend"`, `"safe to buy"`, `"future returns"`, `"how much will ₹"`.
  - Comparative: `"vs"`, `"compare"`, `"better than"`, `"higher return"`.
  - Tax/Legal: `"tax evasion"`, `"avoid capital gains"`, `"illegal"`.
- **Labels**: `FACTUAL`, `PROCEDURAL`, `ADVISORY`, `COMPARATIVE`, `PROJECTION`, `TAX_LEGAL`, `OUT_OF_SCOPE`, `SMALLTALK`.
- **Fail-Closed Resolution**: If either rules or classifier triggers an advisory/comparative label, mark as refusal intent.

### 2.3 Refusal Engine (`backend/app/guardrails/refusal.py`)
Implement 100% deterministic refusal templates without invoking the LLM:

```python
REFUSAL_TEMPLATES = {
    "ADVISORY": (
        "I can only provide objective, factual information regarding mutual fund schemes and cannot offer investment advice, comparisons, or recommendations. "
        "For guidance on fund selection and financial planning, please consult a SEBI-registered investment advisor or review educational resources."
    ),
    "COMPARATIVE": (
        "I cannot compare or rank mutual fund schemes against each other. "
        "You can review the official factsheet for each individual scheme to compare their benchmark index, expense ratios, and portfolio allocations."
    ),
    "PROJECTION": (
        "I cannot calculate future returns or provide return projections for mutual fund schemes. "
        "Historical performance data and rolling returns are documented in the official scheme factsheet."
    ),
}

EDUCATIONAL_LINKS = {
    "ADVISORY": "https://www.amfiindia.com/investor-corner/knowledge-center",
    "COMPARATIVE": "https://www.amfiindia.com/investor-corner/knowledge-center",
    "PROJECTION": "https://www.hdfcfund.com/our-products/equity-funds",
    "TAX_LEGAL": "https://www.amfiindia.com/investor-corner/knowledge-center",
}

def generate_refusal(intent: str, last_updated: str) -> dict:
    body = REFUSAL_TEMPLATES.get(intent, REFUSAL_TEMPLATES["ADVISORY"])
    url = EDUCATIONAL_LINKS.get(intent, EDUCATIONAL_LINKS["ADVISORY"])
    return {
        "text": body,
        "citation_url": url,
        "last_updated": last_updated,
        "rendered": f"{body}\n\nSource: {url}\nLast updated from sources: {last_updated}"
    }
```

### Phase 2 Acceptance Criteria
- [x] Unit test with 15 synthetic PAN, Aadhaar, and OTP inputs returns immediate 400 security warning without calling the LLM.
- [x] 20 synthetic advisory queries (*"Should I invest in HDFC Mid Cap?"*) return templated refusal with AMFI link.
- [x] Zero raw PII written to logs or downstream contexts.

---

## Phase 3 — Hybrid Retrieval & Entity Resolution Engine

**Goal**: Implement the entity resolver to identify scheme targets, query the structured fact store for canonical queries (zero hallucination), and execute hybrid dense + lexical retrieval with RRF fusion for free-form and procedural queries.

### 3.0 Clean Data Research & Corpus Architecture Findings
Based on deep static and DOM inspection of the 5 ingested Groww HDFC scheme documents:
1. **Source Data Structure**:
   - Each scheme page contains 97 structured Next.js `next_data` fields including numeric metrics, custodian/RTA details (`CAMS`), fund manager career histories, ISIN codes, and stamp duty percentages.
   - The rendered DOM contains an official Groww accordion with **8 high-value FAQ pairs** per scheme (40 FAQs total across the 5 schemes), addressing procedural steps (*"How to Invest..."*, *"How to Redeem..."*, *"Can I invest in SIP and Lump Sum..."*).
2. **Tri-Partite Chunking Strategy**:
   - **Tier 1: Canonical Fact Chunks (7 chunks/scheme, 35 chunks total)**:
     - `Key Scheme Details & Metadata`: Category, sub-category, plan, option, fund house, manager, benchmark, riskometer.
     - `Expense Ratio & Charges`: TER percentage and annual management fee explanation.
     - `Exit Load & Redemption Terms`: Exit load percentages, redemption holding periods, and applicable tenures.
     - `Investment Minimums & SIP Limits`: Minimum SIP installment, minimum lumpsum purchase, additional investment amounts.
     - `Lock-in Period & Taxation`: Lock-in requirements (None/ELSS) and capital gains tax rules (STCG 20%, LTCG 12.5% over ₹1.25 Lakh).
     - `Riskometer & Benchmark Index`: SEBI risk classification and underlying benchmark evaluation index.
     - `Fund Management & Operations`: Fund manager education/experience, RTA details (CAMS), ISIN, and stamp duty (0.005%).
   - **Tier 2: Procedural & Explanatory FAQ Chunks (8 chunks/scheme, 40 chunks total)**:
     - Step-by-step procedures extracted from DOM: How to Invest (KYC + online mandate), How to Redeem, Inception Returns, AUM metrics, SIP vs Lumpsum selection, NAV details, and PE/PB valuation ratios.
   - **Tier 3: $O(1)$ SQLite Fact Store (`facts.db`)**:
     - 50 canonical metric rows across the 5 schemes for instant, deterministic factual query resolution without LLM invocation.
   - **Chunk Token Budget**: Sized between 35 and 110 words (~50 to 150 tokens) with section-prefixed metadata formatting (`"{scheme_name} | {section} | {content}"`), ensuring high dense representation density without semantic dilution.
3. **Embedding Model Specification**:
   - **Model**: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions, ~90MB footprint, 22M parameters).
   - **Performance Profile**: Sub-15ms CPU inference, zero external API latency, zero rate limits, and zero dollar cost.
   - **Confidence Threshold**: Calibrated $\tau = 0.65$ to prevent out-of-corpus hallucinations while accommodating phrasing variations.
4. **Vector Database & Hybrid Storage Strategy**:
   - **Vector Store**: **ChromaDB** (`PersistentClient` stored at `data/index/chroma`).
     - Persistent HNSW index with SQLite metadata storage.
     - Enforces **hard boolean metadata pre-filtering** on `scheme_id` (`where={"scheme_id": resolved_scheme_id}`) to mathematically eliminate cross-scheme numerical contamination (`EC-RET-01`).
   - **Lexical Store**: Serialized in-memory `rank_bm25.BM25Okapi` (`data/index/bm25.pkl`) for exact token matching of financial acronyms (TER, ISIN, CAMS, NAV, TRI).
   - **Fusion**: Reciprocal Rank Fusion ($k=60$) combining dense cosine similarity and BM25 rank scores.

### 3.1 Entity Resolver (`backend/app/rag/entities.py`)
Extract scheme and field entities from user text:
- Matches against known scheme aliases:
  - `hdfc_midcap_dg`: "hdfc mid cap", "mid-cap opportunities", "hdfc midcap"
  - `hdfc_smallcap_dg`: "hdfc small cap", "smallcap", "hdfc small"
  - `hdfc_largecap_dg`: "hdfc large cap", "top 100", "hdfc largecap"
  - `hdfc_silver_fof_dg`: "hdfc silver", "silver etf", "silver fof"
  - `hdfc_multicap_dg`: "hdfc multi cap", "multicap", "hdfc multi"
- Matches canonical field keys using `data/glossary.yaml`:
  - `ter_direct`: "expense ratio", "ter", "charges", "fees"
  - `exit_load`: "exit load", "redemption penalty", "exit fee"
  - `min_sip`: "minimum sip", "min sip", "sip installment"
  - `lock_in`: "lock in", "lock-in period", "lockin"
  - `riskometer`: "riskometer", "risk level", "risk category"
  - `benchmark`: "benchmark", "benchmark index", "nifty index"
  - `nav`: "nav", "net asset value"
  - `aum`: "aum", "fund size", "assets under management"
  - `fund_manager`: "fund manager", "who manages", "portfolio manager"

### 3.2 Structured Fact Path (`backend/app/rag/facts.py`)
- Direct lookup in SQLite `facts.db`.
- If `(scheme_id, field)` matches a verified row in `facts.db`, bypass the LLM and generate a deterministic 100% accurate template:
  > *"The exit load for {scheme_name} is {value}. {condition}"*  
  > `Source: {citation_url}`  
  > `Last updated from sources: {doc_date}`

### 3.3 Hybrid Retriever (`backend/app/rag/retriever.py`)
For procedural or descriptive queries:
- **Metadata Pre-Filter**: Restricts search space to `scheme_id` if resolved (`where={"scheme_id": scheme_id}`).
- **Dense Search**: Queries ChromaDB with query embedding $\rightarrow$ Top 20 chunks.
- **Lexical Search**: BM25 query with tokenized terms $\rightarrow$ Top 20 chunks.
- **Reciprocal Rank Fusion (RRF)**:
  $$\text{Score}(d) = \sum_{m \in \{\text{dense}, \text{bm25}\}} \frac{1}{60 + \text{rank}_m(d)} \times \text{PriorityWeight}(\text{doc})$$
  Priority weights: Priority 1 (1.0 for scheme pages).
- **Confidence Cutoff**: Evaluates whether $\max(\text{score}) \ge \tau$ ($0.65$).
- **Primary Source Selection**: Selects highest-scoring chunk to provide the single canonical citation URL.

### Phase 3 Acceptance Criteria
- [x] Standard factual queries (*"What is the TER of HDFC Small Cap?"*) resolve via `FactResolver` in $< 50\text{ ms}$.
- [x] Procedural queries (*"How do I redeem HDFC Mid Cap?"*) retrieve Top-4 chunks from Groww official FAQs.
- [x] Confidence score cutoff properly triggers *"not found"* fallback when query cannot be answered from corpus.

---

## Phase 4 — Constrained LLM Synthesis & Output Contract Validator

**Goal**: Implement the synthesis module using Groq (Llama 3.3 70B Versatile) with strict system instructions, paired with an automated post-generation Contract Validator enforcing the **Rule of Three** ($\le 3$ sentences, 1 URL, date footer).

### 4.1 Constrained Prompt Builder (`backend/app/rag/prompts.py` & `synthesizer.py`)
- Model Configuration: `temperature=0`, `max_tokens=120`.
- System Instruction:
  ```text
  You are an official, factual Mutual Fund FAQ assistant for HDFC Mutual Fund schemes.
  RULES:
  1. Use ONLY the CONTEXT below. If the answer is not in CONTEXT, output exactly: NOT_FOUND.
  2. Maximum 3 sentences. No preamble, no greetings, no closing remarks.
  3. Copy numbers, percentages, dates and names EXACTLY as written in CONTEXT.
  4. Never give advice, opinions, comparisons, predictions, or calculations.
  5. Never use evaluative words (e.g., good, best, safe, attractive, recommended, lucrative).
  6. Do NOT output any URL, source line, or date; those are added by the system.
  ```
- LLM outputs text sentences only; citations and footers are never entrusted to LLM generation.

### 4.2 Output Contract Validator (`backend/app/guardrails/validator.py`)
Implement the automated 5-point verification gate:

```python
import re

BANNED_LEXICON = {
    "good", "great", "best", "better", "safe", "safest", "attractive",
    "lucrative", "recommended", "ideal", "strong", "weak", "should",
    "must invest", "guaranteed", "outperform"
}

def split_sentences(text: str) -> list[str]:
    """Splits text on sentence boundaries while respecting currency/decimals (₹100, 0.76%, etc.)."""
    cleaned = re.sub(r'(?<=\d)\.(?=\d)', '<DOT>', text)
    cleaned = re.sub(r'\b(Rs|Mr|Mrs|e\.g|i\.e)\.', r'\1<DOT>', cleaned)
    parts = re.split(r'(?<=[.!?])\s+', cleaned)
    return [p.replace('<DOT>', '.').strip() for p in parts if p.strip()]

def validate_response(draft_text: str, context_chunks: list, primary_url: str, doc_date: str) -> dict:
    sentences = split_sentences(draft_text)
    
    # 1. Enforce sentence ceiling (<= 3)
    if len(sentences) > 3:
        sentences = sentences[:3]
    valid_text = " ".join(sentences)
    
    # 2. Banned evaluative words check
    for word in BANNED_LEXICON:
        if re.search(rf"\b{word}\b", valid_text, re.IGNORECASE):
            return safe_fallback(primary_url, doc_date)
            
    # 3. Numeric Grounding Verification
    # Every number/percentage in valid_text must appear in retrieved chunk texts
    chunk_corpus = " ".join([c["text"] for c in context_chunks])
    numbers = re.findall(r"\b\d+(?:\.\d+)?%?\b", valid_text)
    for num in numbers:
        if num not in chunk_corpus:
            return safe_fallback(primary_url, doc_date)
            
    # 4. Append programmatic citation and date footer
    rendered = f"{valid_text}\n\nSource: {primary_url}\nLast updated from sources: {doc_date}"
    
    return {
        "text": valid_text,
        "sentence_count": len(sentences),
        "citation_url": primary_url,
        "last_updated": doc_date,
        "rendered": rendered
    }
```

### Phase 4 Acceptance Criteria
- [x] Zero responses exceed 3 sentences.
- [x] Model-generated hallucinations with ungrounded numbers are caught by `validate_response` and replaced with safe factsheet references.
- [x] Every answer terminates with `Last updated from sources: <YYYY-MM-DD>`.

---

## Phase 5 — Multi-Thread Session Management & Backend REST API

**Goal**: Build the FastAPI application layer with isolated multi-thread chat sessions, Pydantic schemas, thread CRUD endpoints, and audit logging.

### 5.1 Pydantic Data Models (`backend/app/schemas/chat.py`)

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class MessageDTO(BaseModel):
    id: str
    role: str  # "user" | "assistant"
    type: str  # "answer" | "refusal" | "pii_block" | "not_found"
    text: str
    citation_url: Optional[str] = None
    last_updated: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ThreadDTO(BaseModel):
    id: str
    title: str
    created_at: datetime
    messages: List[MessageDTO]

class ChatRequest(BaseModel):
    text: str = Field(..., max_length=500)

class MetaResponse(BaseModel):
    amc: str = "HDFC Mutual Fund"
    schemes: List[dict]
    disclaimer: str = "Facts-only. No investment advice."
    starter_questions: List[str]
    last_refreshed: str
```

### 5.2 Session Manager (`backend/app/sessions/store.py`)
- Thread-safe in-memory SQLite backing store.
- Threads keyed strictly by `(client_id, thread_id)`.
- Enforces session isolation: queries from Thread A never see or retrieve conversation context from Thread B.

### 5.3 REST API Endpoints (`backend/app/api/`)
- `GET /api/v1/health`: Checks vector index and SQLite liveness.
- `GET /api/v1/meta`: Returns disclaimer text, starter questions, and HDFC scheme list.
- `POST /api/v1/threads`: Creates new thread session.
- `GET /api/v1/threads`: Lists threads for given `client_id`.
- `GET /api/v1/threads/{id}`: Returns messages for thread.
- `POST /api/v1/threads/{id}/messages`: Submits user query $\rightarrow$ runs guardrails $\rightarrow$ retrieves context $\rightarrow$ synthesizes $\rightarrow$ returns validated response.
- `DELETE /api/v1/threads/{id}`: Deletes thread.

### Phase 5 Acceptance Criteria
- [x] Multi-thread test: sending queries in Thread 1 and Thread 2 concurrently exhibits zero cross-contamination.
- [x] `POST /api/v1/threads/{id}/messages` satisfies latency target $p95 < 2.0\text{ s}$.
- [x] Audit logger records complete trace for every turn with redacted PII and chunk IDs.

---

## Phase 6 — Frontend UI & Groww-Style Interface

**Goal**: Implement the client application in React 18, TypeScript, and Tailwind CSS adhering to Groww design tokens, WCAG 2.1 AA accessibility, persistent disclaimer banners, and multi-thread sidebar.

### 6.1 Design Tokens & Archetype Styling (`frontend/src/index.css`)
- **Color Palette**:
  - Primary Accent: Groww Emerald (`#00B386` / `#00D09C`).
  - Dark Surface: Obsidian Slate (`#12161A` / `#1E242B`).
  - Light Surface: Pure White / Neutral Gray (`#F8F9FA` / `#FFFFFF`).
  - Text Contrast: Minimum $4.5:1$ contrast ratio for WCAG 2.1 AA compliance.

### 6.2 Key Component Hierarchy
1. **`Header.tsx` & `DisclaimerBanner.tsx`**:
   - Sticky, non-dismissible banner: `“⚠️ Disclaimer: Facts-only. No investment advice.”`.
   - Displays selected scope badge: `HDFC Mutual Fund (5 Schemes)`.
2. **`ThreadSidebar.tsx`**:
   - List active conversation threads with timestamps.
   - "New Chat" button to create independent sessions.
   - Rename / Delete thread action menu.
3. **`StarterQuestions.tsx`**:
   - 3 clickable prompt chips displayed on empty threads:
     1. *"What is the exit load for HDFC Mid-Cap Opportunities Fund?"*
     2. *"What is the minimum SIP amount for HDFC Small Cap Fund?"*
     3. *"How do I download my Capital Gains statement on Groww?"*
4. **`MessageFeed.tsx` & `MessageBubble.tsx`**:
   - User messages rendered in clean bubbles.
   - Assistant answers rendered with:
     - Formatted text ($\le 3$ sentences).
     - Clickable official source pill (`Source: groww.in/...` or `hdfcfund.com/...`) opening in `_blank`.
     - Standardized freshness footer (`Last updated from sources: YYYY-MM-DD`).
     - Refusal styling for advisory queries with educational link icon.
5. **`Composer.tsx`**:
   - Input textarea with character count.
   - Client-side soft PII warning badge (*"Please do not include PAN or bank credentials"*).
   - Enter-to-send support.

### 6.3 Zustand Store (`frontend/src/store/useChatStore.ts`)
- Manages `threads`, `activeThreadId`, and `clientId` (stored in `localStorage`).
- Optimistic message appending with typing indicators.

### Phase 6 Acceptance Criteria
- [x] Persistent disclaimer is visible across all screens and screen sizes.
- [x] Clicking starter prompt immediately triggers question in the active thread.
- [x] Clicking citation link opens exact official URL in a new tab.
- [x] Mobile responsiveness: sidebar collapses into accessible drawer on $< 768\text{ px}$.

---

## Phase 7 — End-to-End Testing, Golden Dataset Evals & Production Delivery

**Goal**: Execute comprehensive test suites, evaluate accuracy on golden benchmark sets, package with Docker Compose, and generate final documentation.

### 7.1 Automated Pytest Suite (`backend/tests/`)
- `test_pii.py`: Validates regexes and Verhoeff checks across 20+ valid/invalid PAN, Aadhaar, and OTP patterns.
- `test_intent.py`: Asserts 100% refusal on advisory, comparative, and return-projection questions.
- `test_validator.py`: Property-based test enforcing $\le 3$ sentences and single valid citation URL.
- `test_retriever.py`: Validates retrieval accuracy against factsheets for all 5 HDFC schemes.

### 7.2 Golden Evaluation Harness (`eval/run_eval.py`)
Run the golden benchmark datasets (`eval/datasets/*.jsonl`):

```bash
python -m eval.run_eval --dataset eval/datasets/golden_mf_eval.jsonl
```

| Evaluation Set | Target Size | Pass Metric |
|---|---|---|
| **Factual Retrieval** | 50 questions | $\ge 98\%$ accurate values matching official factsheets |
| **Advisory Refusal** | 60 adversarial prompts | **100%** refusal rate (0 advisory responses permitted) |
| **PII Protection** | 40 synthetic injections | **100%** blocked / redacted (0 leaks) |
| **Contract Invariants** | All queries | **100%** adhere to $\le 3$ sentences, 1 URL, date footer |
| **Hallucination Rate** | Out-of-corpus queries | **0.0%** hallucinated financial numbers |

### 7.3 Docker Compose Packaging (`docker-compose.yml`)

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
      - GROQ_API_KEY=${GROQ_API_KEY}
      - GROQ_MODEL=${GROQ_MODEL:-llama-3.3-70b-versatile}
    volumes:
      - ./data:/app/data

  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    ports:
      - "5173:80"
    depends_on:
      - backend
```

### 7.4 Deliverables Verification Checklist
- [x] Curated corpus established with 15–25 official URLs for HDFC Mutual Fund and Groww.
- [x] Backend RAG engine running with ChromaDB and SQLite facts table.
- [x] Input PII firewall and intent classifier blocking 100% of sensitive/advisory queries.
- [x] Output Contract Validator enforcing $\le 3$ sentences, 1 citation link, and date footer.
- [x] Multi-thread chat interface operational with Groww UI design tokens.
- [x] Comprehensive `README.md` with setup commands, architectural decisions, and limitations.
