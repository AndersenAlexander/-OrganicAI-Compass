ARG PYTHON_IMAGE=python:3.12.10-slim-bookworm

FROM ${PYTHON_IMAGE} AS base
LABEL org.opencontainers.image.title="OrganicAI Compass Backend" \
      org.opencontainers.image.description="Production-compatible OrganicAI Compass FastAPI backend" \
      org.opencontainers.image.source="local" \
      org.opencontainers.image.licenses="Proprietary"
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    WEB_HOST=0.0.0.0 \
    WEB_PORT=8020 \
    WEB_WORKERS=1 \
    WEB_KEEPALIVE_SECONDS=5 \
    WEB_GRACEFUL_SHUTDOWN_SECONDS=30
WORKDIR /app

FROM base AS dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt requirements.txt
RUN python -m pip install --upgrade pip && python -m pip install --prefix=/install -r requirements.txt

FROM dependencies AS test
COPY requirements-dev.txt requirements-dev.txt
RUN python -m pip install --prefix=/install-dev -r requirements-dev.txt
COPY . .
RUN python -m compileall app

FROM base AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends curl libpq5 && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /usr/sbin/nologin organicai
COPY --from=dependencies /install /usr/local
COPY alembic.ini alembic.ini
COPY alembic alembic
COPY app app
RUN mkdir -p /app/tmp /app/backups/database && chown -R organicai:organicai /app
USER organicai
EXPOSE 8020
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 CMD curl -fsS "http://127.0.0.1:${WEB_PORT}/health/live" || exit 1
CMD ["sh", "-c", "exec uvicorn app.main:app --host ${WEB_HOST} --port ${WEB_PORT} --workers ${WEB_WORKERS} --timeout-keep-alive ${WEB_KEEPALIVE_SECONDS}"]
