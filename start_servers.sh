#!/bin/bash

# Start Backend and Frontend Servers

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     🚀 Starting Menu OCR Servers                             ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Start Backend
echo -e "${YELLOW}Starting Backend...${NC}"
cd fastapi-menu-service
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
echo "   URL: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo ""

# Wait a bit
sleep 3

# Start Frontend
echo -e "${YELLOW}Starting Frontend...${NC}"
cd ../menu-ocr-frontend
npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
echo "   URL: http://localhost:3000"
echo ""

# Save PIDs
cd ..
echo $BACKEND_PID > /tmp/backend.pid
echo $FRONTEND_PID > /tmp/frontend.pid

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     ✅ SERVERS RUNNING!                                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "📝 To stop servers:"
echo "   ./stop_servers.sh"
echo "   Or: kill $BACKEND_PID $FRONTEND_PID"
echo ""

# Wait for user interrupt
trap "echo ''; echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait

