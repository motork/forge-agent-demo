#!/bin/bash
# Activation script for the Smart International Sales Data Harmonizer

echo "🌍 Smart International Sales Data Harmonizer"
echo "============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run setup first:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

echo "✅ Virtual environment activated"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env file and add your OpenAI API key"
else
    echo "✅ .env file found"
fi

echo ""
echo "🚀 Ready to harmonize! Try these commands:"
echo "   python main.py check      # Check system status"
echo "   python main.py demo       # Create sample data"
echo "   python main.py harmonize sample_sales_data.csv"
echo ""