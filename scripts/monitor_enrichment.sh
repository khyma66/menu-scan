#!/bin/bash
# Monitor enrichment progress

echo "=== Menu Enrichment Monitor ==="
echo ""

# Check if process is running
if [ -f /tmp/enrichment.pid ]; then
    PID=$(cat /tmp/enrichment.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ Enrichment process is running (PID: $PID)"
    else
        echo "❌ Enrichment process is not running"
    fi
else
    echo "⚠️ No PID file found"
fi

echo ""
echo "=== Recent Logs ==="
tail -20 /tmp/enrichment.log 2>/dev/null || echo "No logs found"

echo ""
echo "=== Status from API ==="
curl -s http://localhost:8000/menu-enrichment/status | python3 -m json.tool 2>/dev/null || echo "API not available"

echo ""
echo "=== Ollama Status ==="
curl -s http://localhost:11434/api/tags | python3 -c "import sys, json; data=json.load(sys.stdin); print('Models:', ', '.join([m['name'] for m in data.get('models', [])]))" 2>/dev/null || echo "Ollama not accessible"

