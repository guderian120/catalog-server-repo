
# Official Python slim image (Debian-based)
FROM python:3.11-slim
# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies only when needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create and switch to a non-root user
WORKDIR /app

RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Install Python dependencies
COPY --chown=appuser requirements.txt .
RUN pip install --user -r requirements.txt

# Copy application code
COPY --chown=appuser . .

# Default command
CMD ["python", "app.py"]