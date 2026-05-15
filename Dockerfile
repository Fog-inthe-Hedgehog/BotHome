# Use the matching Python version from pyproject.toml
FROM python:3.13.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VIRTUALENVS_CREATE=false
ENV POETRY_NO_INTERACTION=1
ENV POETRY_CACHE_DIR="/var/cache/pypoetry"

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-dev --no-interaction --no-ansi
COPY . .

CMD ["python", "app/main.py"]
