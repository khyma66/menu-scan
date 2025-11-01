#!/bin/bash

# Menu OCR Backend Setup Script

set -e

echo "🚀 Setting up Menu OCR Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "🔧 Activating virtual environment..."
source venv/bin/activate

echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f ".env" ]; then
    echo "📝 Copying environment template..."
    cp env.example .env
    echo "⚠️  Please edit .env with your credentials before running the server!"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your credentials"
echo "2. Run: source venv/bin/activate"
echo "3. Start server: uvicorn app.main:app --reload"
echo "4. Visit: http://localhost:8000/docs"

