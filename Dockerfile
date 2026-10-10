# timeglance: renders weekly sheets (WeasyPrint) and the year planner (CairoSVG).
FROM python:3.13-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Native libraries for WeasyPrint + CairoSVG, plus the fonts the templates reference.
RUN apt-get update && apt-get install -y --no-install-recommends \
      libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
      libffi8 shared-mime-info fonts-dejavu-core fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.8.2 /uv /uvx /bin/

WORKDIR /app

# Install dependencies first (cached from the lockfile), then the project itself.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev

EXPOSE 8753

# Default: the timeglance control panel (both planners). Override for a one-shot render, e.g.
#   docker compose run --rm timeglance timeglance-weekly
CMD ["timeglance", "--host", "0.0.0.0"]
