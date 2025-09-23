#!/bin/bash
# Quick Test Runner - Fast verification of core functionality

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🚀 Quick Test - Forge Agent Automotive Lead Harmonizer"
echo "======================================================"

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
echo -e "${BLUE}📊 Processing automotive lead examples...${NC}"
python main.py harmonize examples/random_order_challenge.csv --output quick_test_output.csv

echo
echo -e "${BLUE}🔍 Verifying automotive lead data processing...${NC}"
if [[ -f "quick_test_output.csv" ]]; then
    echo -e "${GREEN}✅ Output file created successfully${NC}"

    # Check if the output has the correct automotive schema
    if head -1 quick_test_output.csv | grep -q "vehicle_make,vehicle_model,price,fuel_type,year,dealer_name,country,customer_name,customer_email,customer_phone,lead_source"; then
        echo -e "${GREEN}✅ Automotive schema validation passed${NC}"
        echo -e "${BLUE}📋 Sample output:${NC}"
        head -2 quick_test_output.csv
    else
        echo -e "${RED}❌ Schema validation failed${NC}"
    fi

    # Clean up
    rm -f quick_test_output.csv
else
    echo -e "${RED}❌ Output file not created${NC}"
    exit 1
fi

echo
echo -e "${GREEN}🎉 Quick automotive lead test completed successfully!${NC}"
echo "The Forge Agent system is ready for automotive lead data processing."