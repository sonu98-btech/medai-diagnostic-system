# ── Dockerfile ─────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libgomp1 && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

# Pre-generate models at build time
RUN python3 data/generate_dataset.py && python3 model/train.py

# Run with gunicorn (production WSGI)
EXPOSE 8080
ENV SECRET_KEY="change-me-in-production-use-32-char-secret"
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", \
     "--timeout", "120", "--access-logfile", "-", "app:app"]
