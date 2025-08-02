#!/bin/bash

# AfterIDE Frontend HTTPS Fix Deployment Script
# This script deploys the frontend with HTTPS enforcement fixes

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

# Function to check if Railway CLI is installed
check_railway_cli() {
    if ! command -v railway >/dev/null 2>&1; then
        print_error "Railway CLI is not installed. Please install it first:"
        echo "npm install -g @railway/cli"
        exit 1
    fi
}

# Function to build frontend
build_frontend() {
    print_status "Building frontend..."
    
    cd frontend
    
    # Install dependencies
    print_status "Installing dependencies..."
    npm install
    
    # Build the application
    print_status "Building application..."
    npm run build
    
    cd ..
    
    print_success "Frontend build completed"
}

# Function to deploy to Railway
deploy_to_railway() {
    print_status "Deploying to Railway..."
    
    cd frontend
    
    # Check if we're logged in to Railway
    if ! railway whoami >/dev/null 2>&1; then
        print_error "Not logged in to Railway. Please run 'railway login' first."
        exit 1
    fi
    
    # Deploy to Railway
    print_status "Deploying frontend to Railway..."
    railway up
    
    cd ..
    
    print_success "Frontend deployed to Railway"
}

# Function to verify HTTPS enforcement
verify_https_enforcement() {
    print_status "Verifying HTTPS enforcement..."
    
    # Wait a moment for deployment to complete
    sleep 10
    
    # Test HTTPS enforcement
    if [ -f "integration-tests/test-https-enforcement.js" ]; then
        print_status "Running HTTPS enforcement test..."
        node integration-tests/test-https-enforcement.js
    else
        print_warning "HTTPS enforcement test script not found"
    fi
}

# Function to show deployment info
show_deployment_info() {
    print_success "Deployment completed!"
    echo ""
    echo "Frontend URL: https://after-ide-production.up.railway.app"
    echo "Backend URL: https://sad-chess-production.up.railway.app"
    echo ""
    echo "The HTTPS enforcement fixes have been deployed. The frontend should now:"
    echo "1. Always use HTTPS for API requests"
    echo "2. Convert any HTTP URLs to HTTPS automatically"
    echo "3. Prevent mixed content errors"
    echo ""
    echo "If you still see mixed content errors, please:"
    echo "1. Clear your browser cache"
    echo "2. Hard refresh the page (Ctrl+F5 or Cmd+Shift+R)"
    echo "3. Check the browser console for any remaining HTTP requests"
}

# Main execution
main() {
    print_status "Starting AfterIDE Frontend HTTPS Fix Deployment..."
    
    # Check prerequisites
    check_railway_cli
    
    # Build frontend
    build_frontend
    
    # Deploy to Railway
    deploy_to_railway
    
    # Verify HTTPS enforcement
    verify_https_enforcement
    
    # Show deployment info
    show_deployment_info
}

# Handle script interruption
trap 'print_error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@" 