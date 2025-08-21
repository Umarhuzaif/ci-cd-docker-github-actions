# syntax=docker/dockerfile:1.7
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Create non-root user
RUN groupadd -g 10001 app && useradd -u 10001 -g app -m app

# Install dependencies
COPY ci-cd-docker-github-actions-starter/requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ci-cd-docker-github-actions-starter/app ./app

# Use non-root user
USER app

EXPOSE 5000

# Use gunicorn for production-grade HTTP serving
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app.app:app"]
