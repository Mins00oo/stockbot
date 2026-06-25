# Stock Bot backend image (used later for deployment).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first for better layer caching.
COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install .

# App source.
COPY alembic.ini ./
COPY alembic ./alembic
COPY src ./src

# Make the src layout importable.
ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uvicorn", "stockbot.main:app", "--host", "0.0.0.0", "--port", "8000"]
