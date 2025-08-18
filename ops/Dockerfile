# syntax=docker/dockerfile:1.7-labs
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# System deps
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl tini && \
    rm -rf /var/lib/apt/lists/*

# Non-root user
RUN useradd -ms /bin/bash app
USER app
WORKDIR /app

# Install deps first
COPY --chown=app:app pyproject.toml README.md ./
RUN --mount=type=cache,target=/home/app/.cache/pip \
    pip install --upgrade pip && pip install -e .

# Copy sources
COPY --chown=app:app src ./src

ENV PATH="/home/app/.local/bin:$PATH"

# Expose optional metrics/health port
EXPOSE 8000

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "-m", "talkative.run"]
