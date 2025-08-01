# AfterIDE Integration Tests Dockerfile
# Multi-stage build for running both backend and frontend integration tests

FROM node:18-alpine AS base

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    git \
    curl \
    bash

# Set working directory
WORKDIR /app

# Copy package files
COPY frontend/package*.json ./frontend/
COPY integration-tests/frontend/package*.json ./integration-tests/frontend/

# Install Node.js dependencies
RUN cd frontend && npm ci
RUN cd integration-tests/frontend && npm ci

# Install Python dependencies
COPY backend/requirements.txt ./backend/
RUN pip3 install --no-cache-dir -r backend/requirements.txt
RUN pip3 install --no-cache-dir pytest pytest-asyncio httpx websockets

# Copy source code
COPY . .

# Install Playwright browsers
RUN cd integration-tests/frontend && npx playwright install --with-deps

# Create test user
RUN adduser -D testuser

# Switch to test user
USER testuser

# Expose ports
EXPOSE 3004 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

# Default command
CMD ["bash", "integration-tests/run-all-tests.sh"] 