# AfterIDE Integration Tests

This directory contains integration tests that test the frontend and backend together to ensure they work seamlessly.

## Test Structure

- `backend/` - Backend integration tests using FastAPI TestClient
- `frontend/` - Frontend integration tests using Playwright for E2E testing
- `shared/` - Shared test utilities and fixtures
- `docker/` - Docker configuration for running integration tests

## Running Integration Tests

### Prerequisites

1. Install backend dependencies:
   ```bash
   cd AfterIDE/backend
   pip install -r requirements.txt
   pip install pytest-asyncio httpx
   ```

2. Install frontend dependencies:
   ```bash
   cd AfterIDE/frontend
   npm install
   npm install -D @playwright/test
   npx playwright install
   ```

### Running Tests

1. **Backend Integration Tests:**
   ```bash
   cd AfterIDE/integration-tests/backend
   pytest -v
   ```

2. **Frontend E2E Tests:**
   ```bash
   cd AfterIDE/integration-tests/frontend
   npx playwright test
   ```

3. **All Integration Tests:**
   ```bash
   cd AfterIDE/integration-tests
   ./run-all-tests.sh
   ```

## Test Scenarios

### Backend Integration Tests
- Authentication flow
- Session management
- File operations
- WebSocket connections
- Terminal commands
- API endpoint integration

### Frontend E2E Tests
- User login/logout
- Editor functionality
- Terminal interaction
- File management
- Real-time collaboration
- Error handling

## Configuration

Tests use separate test databases and configurations to avoid interfering with development data. See individual test files for specific configuration details. 