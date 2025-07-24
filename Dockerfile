FROM python:3.11-slim@sha256:6310ad99788c86b074f6277f2199636da09e0d3c25b176d4e58ab7c6d1fe110e

# Create application user
RUN useradd --create-home --system appuser

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    unzip \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright dependencies
RUN pip install playwright
RUN playwright install chromium
RUN playwright install-deps

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip==25.1.1
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy CA bundle before switching to USER appuser
COPY ./certs/ /certs
RUN chown -R appuser:appuser /certs
RUN chown -R appuser:appuser /app

# Create data directory
RUN mkdir -p /app/data && chown -R appuser:appuser /app/data

# Expose port
EXPOSE 8001

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl -f http://localhost:8000/health/live || exit 1

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
