# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including curl for health checks
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /tmp/afteride

# Make scripts executable
RUN chmod +x healthcheck.py
RUN chmod +x start.sh
RUN chmod +x main.py

# Add current directory to Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check - use the comprehensive healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=5 \
    CMD python healthcheck.py

# Run the application using the main.py entry point
CMD ["python", "main.py"] 