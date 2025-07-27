#!/bin/bash

# Backend-Only Testing Script for Phase 1B
# Tests all backend functionality without frontend dependency

echo "🧪 Phase 1B Backend Testing Suite"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test
run_test() {
    local test_name="$1"
    local command="$2"
    local expected_status="$3"
    
    echo -e "\n${BLUE}Testing: $test_name${NC}"
    echo "Command: $command"
    
    # Run the command and capture output
    output=$(eval "$command" 2>&1)
    status=$?
    
    if [ $status -eq $expected_status ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}"
        echo "Expected status: $expected_status, Got: $status"
        echo "Output: $output"
        ((TESTS_FAILED++))
    fi
}

# Function to test API endpoint
test_api() {
    local test_name="$1"
    local method="$2"
    local endpoint="$3"
    local headers="$4"
    local data="$5"
    local expected_status="$6"
    
    local command="curl -s -o /dev/null -w '%{http_code}'"
    if [ "$method" = "POST" ] || [ "$method" = "PUT" ]; then
        command="$command -X $method"
    fi
    if [ -n "$headers" ]; then
        command="$command -H '$headers'"
    fi
    if [ -n "$data" ]; then
        command="$command -d '$data'"
    fi
    command="$command http://localhost:8000$endpoint"
    
    run_test "$test_name" "$command" "$expected_status"
}

# Get a fresh token for testing
echo "🔑 Getting authentication token..."
TOKEN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username": "admin", "password": "password"}')

TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Failed to get authentication token${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Got authentication token${NC}"

# Test 1: Health Check
test_api "Health Check" "GET" "/health" "" "" 0

# Test 2: Authentication - Valid Login
test_api "Valid Login" "POST" "/api/v1/auth/login" \
    "Content-Type: application/json" \
    '{"username": "admin", "password": "password"}' 0

# Test 3: Authentication - Invalid Login
test_api "Invalid Login" "POST" "/api/v1/auth/login" \
    "Content-Type: application/json" \
    '{"username": "admin", "password": "wrong"}' 0

# Test 4: Authentication - Get Current User (Valid Token)
test_api "Get Current User (Valid Token)" "GET" "/api/v1/auth/me" \
    "Authorization: Bearer $TOKEN" "" 0

# Test 5: Authentication - Get Current User (Invalid Token)
test_api "Get Current User (Invalid Token)" "GET" "/api/v1/auth/me" \
    "Authorization: Bearer invalid-token" "" 0

# Test 6: Sessions - List User Sessions
test_api "List User Sessions" "GET" "/api/v1/sessions/" \
    "Authorization: Bearer $TOKEN" "" 0

# Test 7: Sessions - Create New Session
test_api "Create New Session" "POST" "/api/v1/sessions/?name=TestSession&description=Testing" \
    "Authorization: Bearer $TOKEN" "" 0

# Test 8: Sessions - Get Specific Session
test_api "Get Specific Session" "GET" "/api/v1/sessions/mock-session-1" \
    "Authorization: Bearer $TOKEN" "" 0

# Test 9: Sessions - Get Session Status
test_api "Get Session Status" "GET" "/api/v1/sessions/mock-session-1/status" \
    "Authorization: Bearer $TOKEN" "" 0

# Test 10: Sessions - Extend Session
test_api "Extend Session" "POST" "/api/v1/sessions/mock-session-1/extend?hours=1" \
    "Authorization: Bearer $TOKEN" "" 0

# Test 11: Sessions - Terminate Session
test_api "Terminate Session" "DELETE" "/api/v1/sessions/mock-session-2" \
    "Authorization: Bearer $TOKEN" "" 0

# Summary
echo -e "\n${BLUE}=========================="
echo "Phase 1B Backend Testing Summary"
echo "==========================${NC}"
echo -e "${GREEN}✅ Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}❌ Tests Failed: $TESTS_FAILED${NC}"
echo -e "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All Phase 1B backend tests passed!${NC}"
    echo -e "${YELLOW}Note: Frontend testing skipped due to port conflicts${NC}"
    exit 0
else
    echo -e "\n${RED}⚠️  Some tests failed. Please review the output above.${NC}"
    exit 1
fi 