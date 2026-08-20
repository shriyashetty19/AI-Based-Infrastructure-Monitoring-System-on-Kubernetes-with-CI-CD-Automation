# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY ml/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/mluser/.local/bin:${PATH}" \
    PYTHONPATH="/app" \
    PORT=8001

# Create non-root user and group
RUN groupadd -g 10002 mlgroup && \
    useradd -u 10002 -g mlgroup -s /bin/bash -m mluser

# Copy installed python dependencies from builder
COPY --from=builder /root/.local /home/mluser/.local

# Copy ML application source code
COPY --chown=mluser:mlgroup ml/src /app/ml/src

USER mluser

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

CMD ["uvicorn", "ml.src.main:app", "--host", "0.0.0.0", "--port", "8001"]
