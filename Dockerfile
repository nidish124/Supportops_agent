
# 1. Base image must match pyproject.toml requirement (>=3.12)
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

WORKDIR /app

COPY pyproject.toml .
# Copy lockfile if it exists; ensuring it allows installation
COPY uv.lock* .
RUN uv sync --frozen --no-dev

COPY . .

FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy the entire app directory (which includes the .venv created by uv inside /app)
COPY --from=builder /app /app

# Activate venv
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Expose API port
EXPOSE 8000

# Non-root user
RUN useradd --create-home appuser
USER appuser

# Start FastAPI server
CMD ["uvicorn", "app.main:app", "--host=0.0.0.0", "--port=8000", "--proxy-headers"]