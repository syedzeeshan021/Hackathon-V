# Customer Success FTE - Production Dockerfile
# Multi-stage build for optimized image size

# =============================================================================
# BUILD STAGE
# =============================================================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY production/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# =============================================================================
# PRODUCTION STAGE
# =============================================================================
FROM python:3.11-slim as production

# Security: Run as non-root user
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appgroup production/ ./production/
COPY --chown=appuser:appgroup database/ ./database/

# Set environment variables
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Default command (API server)
CMD ["uvicorn", "production.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# =============================================================================
# WORKER IMAGE (alternative target)
# =============================================================================
FROM production as worker

# Override command for worker process
CMD ["python", "production/workers/message_processor.py"]

# =============================================================================
# DEVELOPMENT IMAGE
# =============================================================================
FROM production as development

# Install development dependencies
RUN pip install --no-cache-dir --user \
    pytest \
    pytest-asyncio \
    pytest-cov \
    pytest-mock \
    httpx \
    uvicorn[standard]

# Enable reload for development
ENV ENVIRONMENT=development

CMD ["uvicorn", "production.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
