# =====================================================================
# BUILDER STAGE
# Creates a virtual environment with all necessary dependencies.
# =====================================================================
FROM python:3.13-slim AS builder

# 1. Environment variables for a cleaner build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 2. Install build-time system dependencies more efficiently
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# 3. Install uv, a fast Python package installer
RUN pip install uv

# 4. Copy only dependency definition files first to leverage Docker cache
COPY pyproject.toml uv.lock* ./

# 5. Create a virtual environment and install dependencies into it
# This isolates dependencies and makes them easy to copy to the next stage.
RUN uv venv /opt/venv && \
    uv pip install --no-cache -r pyproject.toml --python /opt/venv/bin/python

# =====================================================================
# FINAL STAGE
# Creates the final, lightweight image for running the application.
# =====================================================================
FROM python:3.13-slim

# Install runtime system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and group
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup --no-create-home appuser

# Set working directory
WORKDIR /app

# 6. Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# 7. Copy application code and set ownership
# This is done *after* installing dependencies to leverage Docker cache.
COPY --chown=appuser:appgroup . .

# Activate the virtual environment by adding it to the PATH
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Switch to the non-root user
USER appuser

# Expose the application port
EXPOSE 8000

# Add healthcheck to monitor container health
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" \
    || exit 1

# Define the command to run the application
CMD ["python", "main.py"]