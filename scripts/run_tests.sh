#!/bin/bash

# AfterIDE Test Runner
# This script runs all tests for the AfterIDE project

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

echo -e "${BLUE}🚀 AfterIDE Test Suite${NC}"
echo "=========================="

# Function to run a test suite
run_test_suite() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "\n${YELLOW}Running: $test_name${NC}"
    echo "Command: $test_command"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ $test_name PASSED${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ $test_name FAILED${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Check if we're in the right directory (scripts folder)
if [ ! -f "run_terminal_tests.py" ]; then
    echo -e "${RED}❌ Error: Please run this script from the AfterIDE/scripts directory${NC}"
    exit 1
fi

# Install test dependencies if needed
if [ "$1" = "--install-deps" ]; then
    echo -e "${BLUE}📦 Installing test dependencies...${NC}"
    pip install -r ../config/test-requirements.txt
fi

# Run backend tests
run_test_suite "Backend Tests" "cd ../backend && python -m pytest tests/ -v --tb=short"

# Run frontend tests (if npm is available)
if command -v npm &> /dev/null; then
    if [ -d "../frontend" ]; then
        run_test_suite "Frontend Tests" "cd ../frontend && npm test -- --passWithNoTests"
    else
        echo -e "${YELLOW}⚠️  Frontend directory not found, skipping frontend tests${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  npm not found, skipping frontend tests${NC}"
fi

# Run comprehensive terminal tests
run_test_suite "Terminal Integration Tests" "python run_terminal_tests.py"

# Generate test report
echo -e "\n${BLUE}📊 Test Report${NC}"
echo "=============="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}⚠️  Some tests failed. Please check the output above.${NC}"
    exit 1
fi 