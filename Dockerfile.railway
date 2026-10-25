# Stage 1: Build the React 18 + Vite Frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python Runtime with FastAPI
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
