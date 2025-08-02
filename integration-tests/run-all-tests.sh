#!/bin/bash

# AfterIDE Integration Tests Runner
# This script runs all integration tests for both backend and frontend

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to wait for a service to be ready
wait_for_service() {
    local url=$1
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for service at $url..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            print_success "Service at $url is ready!"
            return 0
        fi
        
        print_status "Attempt $attempt/$max_attempts - Service not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "Service at $url failed to start within timeout"
    return 1
}

# Function to setup test environment
setup_test_environment() {
    print_status "Setting up test environment..."
    
    # Check if required tools are installed
    if ! command_exists python3; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    if ! command_exists node; then
        print_error "Node.js is required but not installed"
        exit 1
    fi
    
    if ! command_exists npm; then
        print_error "npm is required but not installed"
        exit 1
    fi
    
    # Check if ports are available
    if port_in_use 8000; then
        print_warning "Port 8000 is already in use. Backend tests may fail."
    fi
    
    if port_in_use 3004; then
        print_warning "Port 3004 is already in use. Frontend tests may fail."
    fi
    
    print_success "Test environment setup complete"
}

# Function to install backend dependencies
install_backend_deps() {
    print_status "Installing backend dependencies..."
    
    cd backend
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    pip install -r requirements.txt
    pip install pytest pytest-asyncio httpx websockets
    
    cd ..
    
    print_success "Backend dependencies installed"
}

# Function to install frontend dependencies
install_frontend_deps() {
    print_status "Installing frontend dependencies..."
    
    cd frontend
    
    # Install npm dependencies
    npm install
    
    # Install Playwright
    npx playwright install
    
    cd ..
    
    print_success "Frontend dependencies installed"
}

# Function to run HTTPS enforcement tests
run_https_tests() {
    print_status "Running HTTPS enforcement tests..."
    
    # Run the HTTPS test script
    if [ -f "test-https-enforcement.js" ]; then
        node test-https-enforcement.js
        print_success "HTTPS enforcement tests completed"
    else
        print_warning "HTTPS enforcement test script not found, skipping..."
    fi
}

# Function to run backend tests
run_backend_tests() {
    print_status "Running backend integration tests..."
    
    cd backend
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Run tests with coverage
    python -m pytest ../integration-tests/backend/ -v --tb=short --cov=app --cov-report=html --cov-report=term
    
    cd ..
    
    print_success "Backend tests completed"
}

# Function to run frontend tests
run_frontend_tests() {
    print_status "Running frontend integration tests..."
    
    cd frontend
    
    # Run Playwright tests
    npx playwright test ../integration-tests/frontend/tests/ --reporter=html
    
    cd ..
    
    print_success "Frontend tests completed"
}

# Function to generate test report
generate_test_report() {
    print_status "Generating test report..."
    
    # Create reports directory
    mkdir -p reports
    
    # Combine test results
    echo "# AfterIDE Integration Test Report" > reports/integration-test-report.md
    echo "" >> reports/integration-test-report.md
    echo "Generated on: $(date)" >> reports/integration-test-report.md
    echo "" >> reports/integration-test-report.md
    
    # Add backend coverage report if exists
    if [ -f "backend/htmlcov/index.html" ]; then
        echo "## Backend Coverage Report" >> reports/integration-test-report.md
        echo "See: backend/htmlcov/index.html" >> reports/integration-test-report.md
        echo "" >> reports/integration-test-report.md
    fi
    
    # Add frontend test report if exists
    if [ -d "frontend/playwright-report" ]; then
        echo "## Frontend Test Report" >> reports/integration-test-report.md
        echo "See: frontend/playwright-report/index.html" >> reports/integration-test-report.md
        echo "" >> reports/integration-test-report.md
    fi
    
    print_success "Test report generated: reports/integration-test-report.md"
}

# Function to cleanup
cleanup() {
    print_status "Cleaning up..."
    
    # Kill any background processes
    pkill -f "uvicorn" || true
    pkill -f "vite" || true
    
    print_success "Cleanup complete"
}

# Main execution
main() {
    print_status "Starting AfterIDE Integration Tests..."
    
    # Setup
    setup_test_environment
    
    # Install dependencies
    install_backend_deps
    install_frontend_deps
    
    # Run tests
    run_backend_tests
    run_frontend_tests
    run_https_tests
    
    # Generate report
    generate_test_report
    
    # Cleanup
    cleanup
    
    print_success "All integration tests completed successfully!"
}

# Handle script interruption
trap cleanup EXIT

# Run main function
main "$@" 