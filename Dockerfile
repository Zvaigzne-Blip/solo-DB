# ─────────────────────────────────────────────────────────────────────────────
# SoloHub — Dockerfile for Google Cloud Run
# Build: docker build -t solohub .
# Run locally: docker run -p 8080:8080 --env-file .env solohub
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.12-slim

# Prevent .pyc files and enable real-time log output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies for psycopg2 and cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev \
        gcc \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (Docker layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Collect static files into /app/staticfiles (served by WhiteNoise)
RUN python manage.py collectstatic --noinput

# Cloud Run injects $PORT (default 8080); gunicorn binds to it
EXPOSE 8080

# Run migrations then start gunicorn
CMD python manage.py migrate --noinput && \
    exec gunicorn \
    --bind :${PORT:-8080} \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    config.wsgi:application
