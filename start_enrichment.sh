#!/bin/bash
# Start continuous menu enrichment

API_URL="http://localhost:8000/menu-enrichment"
BATCH_SIZE=20

echo "🚀 Starting Menu Enrichment Process"
echo "===================================="
echo ""

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend not ready after 30 seconds"
        exit 1
    fi
    sleep 1
done

# Check Ollama
echo ""
echo "📋 Checking Ollama..."
OLLAMA_CHECK=$(curl -s "$API_URL/check-ollama")
echo "$OLLAMA_CHECK" | python3 -m json.tool

# Start enrichment in background
echo ""
echo "🔄 Starting enrichment process..."
echo "Batch size: $BATCH_SIZE"
echo "Logs: /tmp/enrichment_progress.log"
echo ""

# Run enrichment loop
(
    OFFSET=0
    TOTAL_PROCESSED=0
    START_TIME=$(date +%s)
    
    while true; do
        RESULT=$(curl -s -X POST "$API_URL/enrich-batch?limit=$BATCH_SIZE&offset=$OFFSET&status_filter=pending")
        
        PROCESSED=$(echo "$RESULT" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('result', {}).get('processed', 0))" 2>/dev/null || echo "0")
        SUCCESS=$(echo "$RESULT" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('result', {}).get('success', 0))" 2>/dev/null || echo "0")
        FAILED=$(echo "$RESULT" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('result', {}).get('failed', 0))" 2>/dev/null || echo "0")
        
        if [ "$PROCESSED" -eq "0" ] || [ -z "$PROCESSED" ]; then
            echo "$(date): No more dishes to process" | tee -a /tmp/enrichment_progress.log
            break
        fi
        
        TOTAL_PROCESSED=$((TOTAL_PROCESSED + PROCESSED))
        OFFSET=$((OFFSET + BATCH_SIZE))
        
        ELAPSED=$(($(date +%s) - START_TIME))
        RATE=$(echo "scale=2; $TOTAL_PROCESSED / $ELAPSED" | bc 2>/dev/null || echo "0")
        
        echo "$(date): Processed $PROCESSED ($SUCCESS success, $FAILED failed) | Total: $TOTAL_PROCESSED | Rate: $RATE/sec" | tee -a /tmp/enrichment_progress.log
        
        # Checkpoint every 100
        if [ $((TOTAL_PROCESSED % 100)) -eq 0 ]; then
            STATUS=$(curl -s "$API_URL/status")
            echo "$(date): Checkpoint - $STATUS" | tee -a /tmp/enrichment_progress.log
        fi
        
        sleep 1
    done
    
    echo "$(date): ✅ Enrichment completed! Total: $TOTAL_PROCESSED" | tee -a /tmp/enrichment_progress.log
) &

ENRICHMENT_PID=$!
echo "Enrichment process started (PID: $ENRICHMENT_PID)"
echo "Monitor progress: tail -f /tmp/enrichment_progress.log"
echo ""
