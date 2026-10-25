# 🚀 Railway Production Deployment Plan
# Mutual Fund FAQ Assistant

> **Target Platform**: [Railway.app](https://railway.app)  
> **Repository**: `mutual-fund-faq-assistant`  
> **Core Architecture**: FastAPI + ChromaDB/SQLite RAG Backend & React 18 / Tailwind CSS Frontend  
> **LLM Provider**: Groq (`openai/gpt-oss-120b`)  
> **Guiding Principle**: *"Accuracy over Intelligence"* with Zero-Downtime, Persistent Vector Storage, and Sub-50ms Statutory Fact Delivery.

---

## 1. Executive Deployment Architecture

Railway supports two battle-tested deployment architectures for this application. **Option 1 (Unified Container)** is recommended for simplest setup, zero CORS overhead, and maximum cost efficiency ($5/month developer tier).

```
                      [ USER BROWSER ]
                             │
                             ▼ (HTTPS)
                 https://<app>.up.railway.app
                             │
                 ┌───────────▼───────────┐
                 │  Railway Edge Router  │
                 └───────────┬───────────┘
                             │
       ┌─────────────────────┴─────────────────────┐
       │                                           │
┌──────▼─────────────────────────┐   ┌─────────────▼──────────────────┐
│ OPTION 1: Unified Container    │   │ OPTION 2: Split Microservices  │
│ (Dockerfile.railway)           │   │                                │
│                                │   │ ┌────────────────────────────┐ │
│ ┌────────────────────────────┐ │   │ │ Frontend Service (Nginx)   │ │
│ │ Vite React SPA (Static)    │ │   │ │ Port 80 (Public Domain)    │ │
│ └──────────────┬─────────────┘ │   │ └─────────────┬──────────────┘ │
│                │ Internal      │   │               │ Private DNS    │
│ ┌──────────────▼─────────────┐ │   │ ┌─────────────▼──────────────┐ │
│ │ FastAPI Python Engine      │ │   │ │ Backend Service (FastAPI)  │ │
│ │ Port $PORT (Dynamic)       │ │   │ │ Port 8000 (Internal/Public)│ │
│ └──────────────┬─────────────┘ │   │ └─────────────┬──────────────┘ │
│                │               │   │               │                │
└────────────────┼───────────────┘   └───────────────┼────────────────┘
                 │                                   │
                 ▼                                   ▼
        ┌──────────────────────────────────────────────────┐
        │        Railway Persistent Volume Mount           │
        │               Path: /app/data                    │
        │   ├── index/facts.db       (SQLite Fact Store)   │
        │   ├── index/chroma/        (Dense Vector DB)     │
        │   └── index/bm25.pkl       (Lexical Search)      │
        └──────────────────────────────────────────────────┘
```

---

## 2. Option 1: Unified All-in-One Container (Recommended)

In this configuration, a multi-stage Docker build builds the React Vite frontend and bundles it directly into FastAPI's static mount. FastAPI handles `/api/v1/*` and `/health`, while serving the Groww-styled SPA at root `/`.

### 2.1 Configuration Files

#### `railway.toml` (Repository Root)
```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile.railway"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 120
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

#### `Dockerfile.railway` (Repository Root)
```dockerfile
# Stage 1: Build React 18 + Vite Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python Runtime
FROM python:3.11-slim AS runner
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY data /app/data

# Copy built frontend assets into FastAPI static directory
COPY --from=frontend-builder /app/frontend/dist /app/backend/static

ENV PYTHONPATH="/app/backend"
ENV DATA_DIR="/app/data"
ENV HOST="0.0.0.0"
ENV PORT=8000
ENV ENVIRONMENT="production"

WORKDIR /app/backend
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

---

## 3. Option 2: Split Microservices Architecture

If you prefer scaling the frontend (Nginx) independently from the AI backend:

| Component | Railway Service Name | Source Directory / Dockerfile | Internal Network Address |
| :--- | :--- | :--- | :--- |
| **Backend** | `mutual-fund-backend` | `backend/Dockerfile` | `http://mutual-fund-backend.railway.internal:8000` |
| **Frontend** | `mutual-fund-frontend` | `frontend/Dockerfile` | Public domain via Railway edge |

### Frontend Reverse Proxy (`frontend/nginx.conf`)
Update `nginx.conf` proxy target to use Railway's private service DNS:
```nginx
location /api/ {
    proxy_pass http://mutual-fund-backend.railway.internal:8000/api/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

---

## 4. Environment Variables Reference

Configure these variables in the **Railway Dashboard** under `Service Settings -> Variables`:

| Variable Name | Required? | Production Value | Description |
| :--- | :---: | :--- | :--- |
| `GROQ_API_KEY` | **Yes** | `gsk_...` | Groq API Key for constrained synthesis |
| `GROQ_MODEL` | Optional | `openai/gpt-oss-120b` | Model slug (defaults to `openai/gpt-oss-120b`) |
| `GROQ_RPM_LIMIT` | Optional | `30` | Rate limiter: requests per minute |
| `GROQ_RPD_LIMIT` | Optional | `1000` | Rate limiter: requests per day |
| `GROQ_TPM_LIMIT` | Optional | `8000` | Rate limiter: tokens per minute |
| `GROQ_TPD_LIMIT` | Optional | `200000` | Rate limiter: tokens per day |
| `DATA_DIR` | Optional | `/app/data` | Absolute path to persistent facts & ChromaDB volume |
| `ENVIRONMENT` | Optional | `production` | Environment descriptor |
| `CORS_ORIGINS` | Optional | `*` | Allowed CORS origins for cross-domain clients |
| `PORT` | Auto | *Injected by Railway* | Bound automatically via `${PORT:-8000}` |

> [!CAUTION]
> Never commit `GROQ_API_KEY` into git or push `.env` files. Enter your key directly in Railway's secure dashboard.

---

## 5. Storage Persistence (Railway Volume)

The assistant uses an $O(1)$ SQLite fact database (`facts.db`) and ChromaDB vector files located under `data/index/`. To prevent losing refreshed index data when Railway redeploys or restarts containers:

1. In the Railway Project Canvas, select your Backend/Unified service.
2. Navigate to **Data** / **Volumes** tab.
3. Click **Add Volume**.
4. Set **Mount Path** to:
   ```text
   /app/data
   ```
5. Size allocation: `1 GB` (sufficient for hundreds of scheme embeddings and SQLite facts).

---

## 6. Step-by-Step Railway Deployment Guide

### Step 1: Push Code to GitHub
Ensure the project is committed and pushed to your GitHub repository:
```bash
git add .
git commit -m "feat: complete mutual fund faq assistant with phase 7 scheduler and railway config"
git push -u origin master
```

### Step 2: Create Railway Project
1. Open [railway.app/new](https://railway.app/new).
2. Select **Deploy from GitHub repo**.
3. Choose your repository: `Saurabh682/mutual-fund-faq-assistant`.

### Step 3: Configure Build & Deploy Settings
1. Railway detects `railway.toml` automatically.
2. Verify:
   - **Builder**: `DOCKERFILE`
   - **Dockerfile Path**: `Dockerfile.railway`

### Step 4: Add Environment Variables
1. Go to the service's **Variables** tab.
2. Click **New Variable** and add:
   ```env
   GROQ_API_KEY=gsk_...
   GROQ_MODEL=openai/gpt-oss-120b
   ENVIRONMENT=production
   ```

### Step 5: Attach Persistent Volume
1. Go to **Settings -> Volumes** or click **+ Add Volume**.
2. Mount path: `/app/data`.

### Step 6: Generate Public Domain
1. In the service's **Settings** tab under **Networking**:
2. Click **Generate Domain**.
3. Railway provisions an SSL-secured endpoint:
   `https://mutual-fund-faq-assistant-production.up.railway.app`

---

## 7. Verification & Health Checks

Once deployment finishes (`Deploying` $\rightarrow$ `Active`):

### 1. Health Endpoint Verification
```bash
curl -X GET "https://<your-railway-domain>/health"
```
**Expected Response (200 OK):**
```json
{
  "status": "healthy",
  "environment": "production",
  "llm_provider": "groq",
  "llm_model": "openai/gpt-oss-120b",
  "amc": "HDFC Mutual Fund",
  "schemes_count": 5
}
```

### 2. Live Fact Query Test
```bash
curl -X POST "https://<your-railway-domain>/api/v1/rag/ask" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the expense ratio and exit load of HDFC Small Cap Fund?"}'
```
**Expected Response (200 OK, Sub-50ms):**
```json
{
  "resolution_type": "fact_store",
  "text": "The Total Expense Ratio (TER) of HDFC Small Cap Fund (Direct Plan) is 0.8%.",
  "citation_url": "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth"
}
```

### 3. Frontend UI Browser Verification
Open `https://<your-railway-domain>/` in your browser. Verify:
- Groww-style obsidian theme renders cleanly.
- Statutory disclaimer banner is fixed at the top.
- Clicking any starter prompt returns a $\le 3$ sentence answer with citation link and freshness timestamp.

---

## 8. Synchronizing Daily Updates (Phase 7 CI Integration)

Your **Phase 7 GitHub Action** (`.github/workflows/daily-data-ingestion.yml`) runs daily at 10:00 AM IST to scrape fresh Groww data and commit updated indexes.

- **Option A (Default)**: The GitHub Action commits updated `data/index/` files with `[skip ci]`.
- **Option B (Railway Webhook)**: You can configure Railway's **Deploy Webhook** URL in GitHub Secrets (`RAILWAY_DEPLOY_WEBHOOK_URL`). At the end of the daily ingestion workflow, a `curl -X POST $RAILWAY_DEPLOY_WEBHOOK_URL` triggers Railway to refresh the live container with latest embeddings.

---

## 9. Troubleshooting & FAQ

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **Container crashes with Exit 137 (OOM)** | SentenceTransformer model download exceeds memory limit | Ensure container has at least 1 GB RAM allocation in Railway service settings. |
| **Application hangs on port binding** | Hardcoded port `8000` ignoring Railway's dynamic `$PORT` | The `Dockerfile.railway` uses `uvicorn app.main:app --port ${PORT:-8000}`. |
| **ChromaDB empty after redeploy** | Container filesystem is ephemeral without a Volume | Verify that `/app/data` is mounted to a Railway Volume under the **Volumes** tab. |
| **CORS errors in browser console** | Cross-origin requests blocked | If using Option 1 (Unified Container), API and frontend share the same origin (no CORS needed). For Option 2, set `CORS_ORIGINS=*`. |
| **Reasoning tokens consuming draft** | `openai/gpt-oss-120b` reasoning tokens starving max token limit | Sized to 260 completion tokens in `backend/app/rag/synthesizer.py`. |
