# Brúixola — FastAPI text→SQL API, container for Render (managed deploy).
#
# Build CONTEXT = the REPO ROOT (not packages/ai), because the agent's catalog
# reads `semantic/metrics.yml` and the warehouse reads `data/marts/` / the
# fixtures, all of which live outside packages/ai. From the repo root:
#
#     docker build -f packages/ai/Dockerfile -t datapoble-ai .
#     docker run --rm -p 8000:8000 \
#         -e OPENROUTER_API_KEY=sk-... \      # the SECRET — only at runtime, never baked in
#         -e AI_DAILY_USD=1.0 -e AI_MONTHLY_USD=20.0 \
#         datapoble-ai
#
# On Render set the same env vars in the service config (OPENROUTER_API_KEY as a
# secret). Render injects $PORT; this image honours it (defaults to 8000 local).

FROM python:3.11-slim AS base

# Faster, quieter, no .pyc clutter; unbuffered logs for the platform log drain.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # The catalog walks up to find semantic/metrics.yml; pin it explicitly so the
    # layout is unambiguous inside the container.
    DATAPOBLE_ROOT=/app \
    # Local default; Render overrides PORT at runtime.
    PORT=8000

WORKDIR /app

# curl is only needed for the container HEALTHCHECK below; keep the layer tiny.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# 1) Install dependencies first (better layer caching). Copy only the package
#    metadata, install with the openrouter extra so the LLM path is available in
#    production. `.` here is packages/ai (copied next), so we stage the metadata.
COPY packages/ai/pyproject.toml packages/ai/README.md /app/packages/ai/

# 2) Copy the application code + everything the agent reads at runtime.
COPY packages/ai/ /app/packages/ai/
COPY semantic/ /app/semantic/
# Real marts when present; harmless if absent (the warehouse falls back to the
# package fixtures). Kept optional so the image builds before Sondeig ships them.
COPY data/ /app/data/

# 3) Install the package itself (+ openrouter client + uvicorn server). Editable
#    so the source layout (which the catalog/warehouse path logic relies on) is
#    preserved.
RUN pip install -e "/app/packages/ai[openrouter,server]"

# Run as a non-root user (defence in depth; the API is read-only anyway).
RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Liveness: hit the app's own /health (reports backend + cost-control state).
# Uses $PORT so it tracks whatever the platform assigns.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT}/health" || exit 1

# Bind 0.0.0.0:$PORT. `python -m datapoble_ai.api` calls uvicorn with the right
# host/port (see api._serve), so there is a single source of truth for the port.
CMD ["python", "-m", "datapoble_ai.api"]
