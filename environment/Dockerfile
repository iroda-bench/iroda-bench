FROM ghcr.io/astral-sh/uv:0.7.12 AS uv
FROM python:3.12.10-slim-bookworm

COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_PYTHON_DOWNLOADS=never
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev
ENV PATH="/app/.venv/bin:${PATH}"
COPY environment/example_agent.py ./
