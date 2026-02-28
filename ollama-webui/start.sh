#!/bin/bash
# Ollama Web UI Startup Script

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Ollama Web UI Launcher${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Ollama is running
echo -e "${YELLOW}Checking Ollama service...${NC}"
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${YELLOW}Ollama is not running. Starting Ollama...${NC}"
    /Applications/Ollama.app/Contents/Resources/ollama serve &
    sleep 3
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ollama started successfully${NC}"
    else
        echo -e "${YELLOW}⚠ Ollama may still be starting...${NC}"
    fi
else
    echo -e "${GREEN}✓ Ollama is already running${NC}"
fi

# Check if Python is available
echo ""
echo -e "${YELLOW}Checking Python environment...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}⚠ Python3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

# Check if virtual environment exists
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# Install dependencies
echo ""
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Set default port if not specified
PORT=${WEBUI_PORT:-8080}
OLLAMA_URL=${OLLAMA_URL:-http://localhost:11434}

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Starting Ollama Web UI...${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🌐 Web UI: http://localhost:${PORT}${NC}"
echo -e "${GREEN}📚 API Docs: http://localhost:${PORT}/docs${NC}"
echo -e "${GREEN}🤖 Ollama API: ${OLLAMA_URL}${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

# Start the web UI
export WEBUI_PORT=$PORT
export OLLAMA_URL=$OLLAMA_URL
python app.py
