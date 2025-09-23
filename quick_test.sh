#!/bin/bash
# Quick Test Runner - Fast verification of core functionality

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🚀 Quick Test - Smart International Sales Data Harmonizer"
echo "======================================================="

# Check if in correct directory
if [[ ! -f "main.py" ]]; then
    echo -e "${RED}Error: Run from project root directory${NC}"
    exit 1
fi

# Activate virtual environment
if [[ -d "venv" ]]; then
    source venv/bin/activate
    echo -e "${GREEN}✅ Virtual environment activated${NC}"
else
    echo -e "${RED}❌ Virtual environment not found${NC}"
    exit 1
fi

# Run basic checks
echo -e "${BLUE}🔍 Checking system...${NC}"
python main.py check

echo
echo -e "${BLUE}🧪 Running basic tests...${NC}"
python tests/test_basic.py

echo
echo -e "${BLUE}📊 Creating and processing sample data...${NC}"
python main.py demo
python main.py harmonize sample_sales_data.csv

echo
echo -e "${GREEN}🎉 Quick test completed successfully!${NC}"
echo "The system is ready for use."