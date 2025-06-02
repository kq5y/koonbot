ARG PYTHON_VERSION="3.10.17"

FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION%.*}-bookworm-slim AS build

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=python${PYTHON_VERSION%.*}

WORKDIR /app
COPY ./pyproject.toml /app
COPY ./uv.lock /app

RUN --mount=type=cache,target=/root/.cache \
    set -ex && \
    cd /app && \
    uv sync --frozen --no-install-project

COPY ./bot /app

FROM python:${PYTHON_VERSION}-slim-bookworm

ENV PATH=/app/.venv/bin:$PATH

WORKDIR /app

COPY --from=build /app /app

WORKDIR /app/bot

CMD ["python", "-u", "main.py"]
