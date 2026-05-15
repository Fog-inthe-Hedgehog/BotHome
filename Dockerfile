# Use the matching Python version from pyproject.toml
FROM python:3.13.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VIRTUALENVS_CREATE=false
ENV POETRY_NO_INTERACTION=1
ENV POETRY_CACHE_DIR="/var/cache/pypoetry"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && pip install --no-cache-dir "poetry>=1.7.0,<2.0.0" \
    && apt-get purge -y --auto-remove curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY . .
RUN poetry install --no-root --no-dev --no-interaction --no-ansi

CMD ["python", "main.py"]
