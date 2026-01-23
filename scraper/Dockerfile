# scraper/Dockerfile
FROM python:3.9-bullseye

WORKDIR /app

# Install system dependencies for Scrapy/Postgres
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 1. Install Playwright and its dependencies
RUN pip install scrapy-playwright
RUN playwright install --with-deps chromium

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .