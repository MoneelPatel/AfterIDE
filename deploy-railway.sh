#!/bin/bash

# AfterIDE Railway Deployment Script
# This script helps you deploy AfterIDE to Railway

set -e

echo "🚀 AfterIDE Railway Deployment Script"
echo "======================================"

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

# Check if Railway CLI is installed
check_railway_cli() {
    if ! command -v railway &> /dev/null; then
        print_warning "Railway CLI not found. Installing..."
        npm install -g @railway/cli
        print_success "Railway CLI installed successfully"
    else
        print_success "Railway CLI is already installed"
    fi
}

# Check if user is logged in to Railway
check_railway_login() {
    if ! railway whoami &> /dev/null; then
        print_warning "Not logged in to Railway. Please login:"
        railway login
    else
        print_success "Already logged in to Railway"
    fi
}

# Initialize Railway project
init_railway_project() {
    print_status "Initializing Railway project..."
    
    if [ ! -f "railway.json" ]; then
        print_error "railway.json not found. Please run this script from the AfterIDE directory."
        exit 1
    fi
    
    if [ ! -f "railway.toml" ]; then
        print_error "railway.toml not found. Please run this script from the AfterIDE directory."
        exit 1
    fi
    
    print_success "Railway configuration files found"
}

# Deploy to Railway
deploy_to_railway() {
    print_status "Deploying to Railway..."
    
    # Check if project is already initialized
    if [ ! -f ".railway" ]; then
        print_status "Initializing new Railway project..."
        railway init
    fi
    
    print_status "Building and deploying services..."
    railway up
    
    print_success "Deployment completed!"
}

# Show deployment URLs
show_urls() {
    print_status "Getting deployment URLs..."
    
    echo ""
    echo "🌐 Your AfterIDE is now deployed!"
    echo "=================================="
    
    # Get service URLs
    BACKEND_URL=$(railway status --json | grep -o '"url":"[^"]*"' | head -1 | cut -d'"' -f4)
    FRONTEND_URL=$(railway status --json | grep -o '"url":"[^"]*"' | tail -1 | cut -d'"' -f4)
    
    if [ ! -z "$BACKEND_URL" ]; then
        echo "🔧 Backend API: $BACKEND_URL"
        echo "📚 API Docs: $BACKEND_URL/docs"
        echo "❤️  Health Check: $BACKEND_URL/health"
    fi
    
    if [ ! -z "$FRONTEND_URL" ]; then
        echo "🎨 Frontend: $FRONTEND_URL"
    fi
    
    echo ""
    print_success "Deployment successful! 🎉"
}

# Set environment variables
set_env_vars() {
    print_status "Setting environment variables..."
    
    # Generate a secure secret key
    SECRET_KEY=$(openssl rand -hex 32)
    POSTGRES_PASSWORD=$(openssl rand -base64 32)
    
    # Set environment variables
    railway variables set ENVIRONMENT=production
    railway variables set DEBUG=false
    railway variables set LOG_LEVEL=INFO
    railway variables set SECRET_KEY=$SECRET_KEY
    railway variables set POSTGRES_PASSWORD=$POSTGRES_PASSWORD
    
    print_success "Environment variables set successfully"
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    # Wait a bit for the database to be ready
    sleep 10
    
    # Run migrations
    railway run --service afteride-backend "cd backend && alembic upgrade head"
    
    print_success "Database migrations completed"
}

# Main deployment function
main() {
    echo ""
    print_status "Starting Railway deployment process..."
    
    # Check prerequisites
    check_railway_cli
    check_railway_login
    init_railway_project
    
    # Deploy
    deploy_to_railway
    
    # Set environment variables
    set_env_vars
    
    # Run migrations
    run_migrations
    
    # Show results
    show_urls
    
    echo ""
    echo "📋 Next Steps:"
    echo "1. Visit your frontend URL to test the application"
    echo "2. Check the health endpoint to verify backend is working"
    echo "3. Review the API documentation at /docs"
    echo "4. Monitor your deployment in the Railway dashboard"
    echo ""
    echo "📖 For more information, see RAILWAY_DEPLOYMENT.md"
}

# Help function
show_help() {
    echo "AfterIDE Railway Deployment Script"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  deploy     Deploy the application to Railway (default)"
    echo "  status     Show deployment status and URLs"
    echo "  logs       Show deployment logs"
    echo "  help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 deploy    # Deploy to Railway"
    echo "  $0 status    # Show deployment status"
    echo "  $0 logs      # Show logs"
}

# Parse command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "status")
        show_urls
        ;;
    "logs")
        railway logs
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac 