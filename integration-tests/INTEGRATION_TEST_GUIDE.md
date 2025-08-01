# AfterIDE Integration Testing Guide

This guide explains how to run and understand the integration tests for AfterIDE, which test the frontend and backend together to ensure they work seamlessly.

## Overview

The integration tests are designed to verify that:
- Frontend and backend communicate correctly
- Authentication flows work end-to-end
- File operations are synchronized between frontend and backend
- WebSocket connections handle real-time communication
- Session management works across the full stack
- Error handling is consistent between frontend and backend

## Test Structure

```
integration-tests/
├── backend/                    # Backend integration tests
│   ├── conftest.py            # Pytest configuration and fixtures
│   ├── test_auth_integration.py
│   ├── test_session_integration.py
│   ├── test_websocket_integration.py
│   └── test_file_integration.py
├── frontend/                   # Frontend E2E tests
│   ├── playwright.config.ts   # Playwright configuration
│   ├── package.json           # Frontend test dependencies
│   └── tests/
│       ├── auth.spec.ts       # Authentication E2E tests
│       ├── editor.spec.ts     # Editor functionality tests
│       └── terminal.spec.ts   # Terminal interaction tests
├── shared/                     # Shared test utilities
│   └── test_utils.py          # Common test helpers
├── docker/                     # Docker configuration
│   ├── Dockerfile             # Test environment container
│   └── docker-compose.yml     # Multi-service test setup
├── requirements.txt           # Python dependencies
├── pytest.ini                # Pytest configuration
├── run-all-tests.sh          # Main test runner script
└── README.md                 # This file
```

## Prerequisites

### System Requirements
- Python 3.8+
- Node.js 16+
- npm or yarn
- Docker (optional, for containerized testing)

### Backend Dependencies
```bash
cd AfterIDE/backend
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx websockets
```

### Frontend Dependencies
```bash
cd AfterIDE/frontend
npm install
npm install -D @playwright/test
npx playwright install
```

## Running Tests

### Option 1: Run All Tests (Recommended)
```bash
cd AfterIDE/integration-tests
./run-all-tests.sh
```

This script will:
1. Set up the test environment
2. Install dependencies
3. Run backend integration tests
4. Run frontend E2E tests
5. Generate test reports
6. Clean up resources

### Option 2: Run Backend Tests Only
```bash
cd AfterIDE/integration-tests/backend
pytest -v
```

### Option 3: Run Frontend Tests Only
```bash
cd AfterIDE/integration-tests/frontend
npx playwright test
```

### Option 4: Run Tests in Docker
```bash
cd AfterIDE/integration-tests/docker
docker-compose up --build
```

## Test Categories

### Backend Integration Tests

#### Authentication Tests (`test_auth_integration.py`)
- Login/logout flows
- Token validation
- CORS headers
- Error handling
- Session persistence

#### Session Management Tests (`test_session_integration.py`)
- Session creation and lifecycle
- Session configuration
- Status transitions
- Concurrent sessions

#### WebSocket Tests (`test_websocket_integration.py`)
- Connection establishment
- Real-time communication
- Error handling
- Connection cleanup
- Concurrent connections

#### File Operations Tests (`test_file_integration.py`)
- File CRUD operations
- Directory structure
- File upload/download
- Search functionality
- Concurrent access
- Size limits and validation

### Frontend E2E Tests

#### Authentication Tests (`auth.spec.ts`)
- Login page display
- Form validation
- Error handling
- Network failures
- Token expiration
- Loading states

#### Editor Tests (`editor.spec.ts`)
- Code editing
- File operations
- Syntax highlighting
- Auto-completion
- Multiple tabs
- Keyboard shortcuts

#### Terminal Tests (`terminal.spec.ts`)
- Command execution
- Output display
- History navigation
- File system operations
- Error handling
- Connection management

## Test Configuration

### Environment Variables
```bash
# Backend configuration
BACKEND_URL=http://localhost:8000
DATABASE_URL=sqlite:///./test.db
DEBUG=true

# Frontend configuration
FRONTEND_URL=http://localhost:3004
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# Test configuration
TEST_USER=testuser
TEST_PASSWORD=testpassword123
TEST_TIMEOUT=60
```

### Pytest Configuration
The `pytest.ini` file configures:
- Test discovery patterns
- Markers for test categorization
- Coverage reporting
- Timeout settings
- Parallel execution options

### Playwright Configuration
The `playwright.config.ts` file configures:
- Browser environments (Chrome, Firefox, Safari)
- Mobile viewports
- Test timeouts
- Screenshot and video capture
- Web server setup

## Test Utilities

### Shared Test Utilities (`shared/test_utils.py`)

#### TestDataManager
Manages temporary files and directories for testing.

#### WebSocketTestHelper
Provides utilities for WebSocket testing including message sending and receiving.

#### APITestHelper
Common API testing utilities like header creation and response validation.

#### FileTestHelper
File operation testing utilities including test file structure creation.

#### SessionTestHelper
Session management testing utilities.

#### PerformanceTestHelper
Performance testing utilities for measuring response times.

#### MockDataGenerator
Generates mock data for testing scenarios.

#### TestEnvironment
Manages test environment configuration.

## Test Reports

### Backend Coverage Report
After running tests, view the HTML coverage report:
```bash
open AfterIDE/backend/htmlcov/index.html
```

### Frontend Test Report
View Playwright test results:
```bash
cd AfterIDE/integration-tests/frontend
npx playwright show-report
```

### Combined Report
The test runner generates a combined report at:
```
AfterIDE/integration-tests/reports/integration-test-report.md
```

## Debugging Tests

### Backend Test Debugging
```bash
# Run with verbose output
pytest -v -s

# Run specific test
pytest test_auth_integration.py::TestAuthIntegration::test_login_success -v -s

# Run with debugger
pytest --pdb

# Run with coverage
pytest --cov=app --cov-report=html
```

### Frontend Test Debugging
```bash
# Run in headed mode
npx playwright test --headed

# Run with debugger
npx playwright test --debug

# Run specific test
npx playwright test auth.spec.ts --grep "should login successfully"

# Show test traces
npx playwright show-trace
```

## Continuous Integration

### GitHub Actions Example
```yaml
name: Integration Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Run Integration Tests
        run: |
          cd AfterIDE/integration-tests
          ./run-all-tests.sh
```

## Best Practices

### Writing Integration Tests

1. **Test Real Scenarios**: Focus on testing complete user workflows
2. **Use Descriptive Names**: Test names should clearly describe what they test
3. **Clean Up Resources**: Always clean up test data and temporary files
4. **Handle Async Operations**: Use proper async/await patterns
5. **Mock External Dependencies**: Mock external services to avoid flaky tests
6. **Test Error Conditions**: Include tests for error scenarios and edge cases

### Test Data Management

1. **Use Fixtures**: Leverage pytest fixtures for test data setup
2. **Isolate Tests**: Each test should be independent and not rely on others
3. **Clean State**: Reset state between tests to avoid interference
4. **Use Test Databases**: Use separate test databases to avoid affecting development data

### Performance Considerations

1. **Parallel Execution**: Use pytest-xdist for parallel test execution
2. **Test Timeouts**: Set appropriate timeouts to catch hanging tests
3. **Resource Cleanup**: Ensure proper cleanup to avoid resource leaks
4. **Mock Heavy Operations**: Mock operations that are slow or external

## Troubleshooting

### Common Issues

#### Backend Tests Fail
- Check if backend server is running
- Verify database connection
- Check authentication setup
- Review test environment variables

#### Frontend Tests Fail
- Ensure frontend dev server is running
- Check browser installation
- Verify API endpoints are accessible
- Review Playwright configuration

#### WebSocket Tests Fail
- Check WebSocket server is running
- Verify CORS configuration
- Check authentication tokens
- Review connection timeouts

#### Docker Tests Fail
- Check Docker daemon is running
- Verify port availability
- Check container resource limits
- Review Docker Compose configuration

### Getting Help

1. Check the test logs for detailed error messages
2. Review the test configuration files
3. Verify all dependencies are installed
4. Check if services are running on correct ports
5. Review the troubleshooting section in this guide

## Contributing

When adding new integration tests:

1. Follow the existing test structure and naming conventions
2. Add appropriate test markers
3. Include both positive and negative test cases
4. Add documentation for new test utilities
5. Update this guide if needed
6. Ensure tests pass in both local and CI environments 