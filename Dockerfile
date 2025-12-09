# Multi-stage Dockerfile for BTC Sentiment Analysis
# Base: python:3.11-slim
# Supports both API (uvicorn) and APP (streamlit) modes via ARG/ENV

# ============================================================================
# Stage 1: Base image with dependencies
# ============================================================================
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    gcc \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Stage 2: Application image
# ============================================================================
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy installed packages from base stage
COPY --from=base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=base /usr/local/bin /usr/local/bin

# Copy application source code
COPY src/ /app/src/
COPY .env* /app/
COPY start.sh /app/

# Create data directory for SQLite database
RUN mkdir -p /app/data && chmod +x /app/start.sh

# ARG for build-time configuration (can be overridden at build time)
ARG MODE=api

# ENV for runtime configuration (can be overridden at runtime)
ENV MODE=${MODE}
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose ports
# 8000 for FastAPI backend
# 8501 for Streamlit dashboard
EXPOSE 8000 8501

# Use startup script that handles database setup
CMD ["/app/start.sh"]

