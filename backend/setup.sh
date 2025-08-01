#!/bin/bash

# AfterIDE Backend Setup Script
# Automatically sets up the backend environment with latest pip

echo "🚀 AfterIDE Backend Setup"
echo "========================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if command succeeded
check_success() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1 failed${NC}"
        exit 1
    fi
}

# Step 1: Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
    check_success "Virtual environment created"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

# Step 2: Activate virtual environment
echo -e "${YELLOW}🔄 Activating virtual environment...${NC}"
source venv/bin/activate
check_success "Virtual environment activated"

# Step 3: Upgrade pip to latest version (eliminates warning messages)
echo -e "${YELLOW}⬆️  Upgrading pip to latest version...${NC}"
python -m pip install --upgrade pip --quiet
check_success "Pip upgraded to latest version"

# Step 4: Install requirements
echo -e "${YELLOW}📋 Installing requirements...${NC}"
pip install -r requirements.txt --quiet
check_success "Requirements installed"

# Step 5: Run database migrations
echo -e "${YELLOW}🗃️  Running database migrations...${NC}"
alembic upgrade head
check_success "Database migrations completed"

# Step 6: Display setup completion
echo -e "\n${GREEN}🎉 Backend setup completed successfully!${NC}"
echo -e "${BLUE}📝 Summary:${NC}"
echo -e "   ✅ Virtual environment ready"
echo -e "   ✅ Pip upgraded to latest version"
echo -e "   ✅ All dependencies installed"
echo -e "   ✅ Database initialized"
echo ""
echo -e "${YELLOW}🚀 To start the backend server:${NC}"
echo -e "   source venv/bin/activate"
echo -e "   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo -e "${BLUE}💡 Note: Pip has been upgraded to eliminate version warnings!${NC}" 