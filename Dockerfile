# ──────────────────────────────────────────────────
# FLUXION — Container Image
# Multi-stage build for minimal footprint
# ──────────────────────────────────────────────────

FROM python:3.12-slim AS builder

WORKDIR /build

COPY pyproject.toml README.md LICENSE ./
COPY fluxion/ ./fluxion/

RUN pip install --no-cache-dir build && \
    python -m build --wheel

# ── Runtime ──────────────────────────────────────

FROM python:3.12-slim

LABEL maintainer="Fluxion Contributors"
LABEL description="Fluxion — The Intelligent Network Command Engine"
LABEL version="1.0.0"

RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /build/dist/*.whl /tmp/

RUN pip install --no-cache-dir /tmp/*.whl && \
    rm -f /tmp/*.whl

RUN useradd --create-home --shell /bin/bash fluxion
USER fluxion
WORKDIR /home/fluxion

ENTRYPOINT ["fluxion"]
CMD ["version"]
