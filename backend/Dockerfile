# ==============================================================================
# OpsPilot Backend Dockerfile (Multi-stage production build)
# Non-root execution, minimal runtime image, baked-in health check
# ==============================================================================

# Stage 1: Build & wheels generation
FROM python:3.13-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir=/build/wheels -r requirements.txt && \
    pip wheel --no-cache-dir --wheel-dir=/build/wheels gunicorn

# Stage 2: Frontend builder
FROM node:20-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 3: Minimal production runtime
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend \
    PORT=8000

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built wheels and install
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* && \
    rm -rf /wheels

# Copy backend application code, operational scripts, and database migrations
COPY backend /app/backend
COPY scripts /app/scripts
COPY db /app/db

# Copy built frontend assets so FastAPI can serve /ui out of the box
COPY --from=frontend-builder /frontend/dist /app/frontend/dist


# Create dedicated non-root user (security hardening)
RUN groupadd -g 10001 opspilot && \
    useradd -u 10001 -g opspilot -s /bin/bash -m opspilot && \
    chown -R opspilot:opspilot /app

USER opspilot

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
