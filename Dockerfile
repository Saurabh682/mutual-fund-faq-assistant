# Stage 1: Build the React 18 + Vite Frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python Runtime with FastAPI
FROM python:3.11-slim AS runner

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces uses UID 1000
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR /home/user/app

COPY backend/requirements.txt /home/user/app/backend/
RUN pip install --no-cache-dir -r /home/user/app/backend/requirements.txt

COPY --chown=user:user backend /home/user/app/backend
COPY --chown=user:user data /home/user/app/data

# Copy built frontend assets into FastAPI static directory
COPY --chown=user:user --from=frontend-builder /app/frontend/dist /home/user/app/backend/static

ENV PYTHONPATH="/home/user/app/backend"
ENV DATA_DIR="/home/user/app/data"
ENV HOST="0.0.0.0"
ENV PORT=7860
ENV ENVIRONMENT="production"

USER user
WORKDIR /home/user/app/backend

EXPOSE 7860

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
