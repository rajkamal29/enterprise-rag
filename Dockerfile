FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN apt-get update \
    ; apt-get install -y --no-install-recommends ca-certificates curl \
    ; rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
COPY README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev

RUN groupadd --system appuser \
    ; useradd --system --gid appuser --create-home appuser \
    ; chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["/app/.venv/bin/uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
