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

# Create data directory for SQLite database
RUN mkdir -p /app/data

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

# Default command runs the FastAPI backend
# Override with MODE=app to run Streamlit dashboard
CMD if [ "$MODE" = "app" ]; then \
    streamlit run src/app/dashboard.py --server.port 8501 --server.address 0.0.0.0; \
    else \
    uvicorn src.api.main:app --host 0.0.0.0 --port 8000; \
    fi
