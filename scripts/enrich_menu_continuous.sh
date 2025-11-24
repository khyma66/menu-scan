#!/bin/bash
# Continuous menu enrichment script using optimal batch processing

BATCH_SIZE=20
API_URL="http://localhost:8000/menu-enrichment"

echo "🚀 Starting optimal menu enrichment"
echo "Batch size: $BATCH_SIZE"
echo "API URL: $API_URL"
echo ""

# Check Ollama status
echo "📋 Checking Ollama status..."
OLLAMA_STATUS=$(curl -s "$API_URL/check-ollama")
echo "$OLLAMA_STATUS" | python3 -m json.tool

OLLAMA_AVAILABLE=$(echo "$OLLAMA_STATUS" | python3 -c "import sys, json; print(json.load(sys.stdin).get('ollama_available', False))")

if [ "$OLLAMA_AVAILABLE" != "True" ]; then
    echo "❌ Ollama is not available!"
    exit 1
fi

echo ""
echo "✅ Ollama is ready!"
echo ""

# Get initial status
echo "📊 Initial status:"
curl -s "$API_URL/status" | python3 -m json.tool
echo ""

# Start enrichment loop
OFFSET=0
TOTAL_PROCESSED=0
TOTAL_SUCCESS=0
TOTAL_FAILED=0
START_TIME=$(date +%s)

echo "🔄 Starting batch processing..."
echo "============================================================"

while true; do
    BATCH_START=$(date +%s)
    
    # Process batch
    RESULT=$(curl -s -X POST "$API_URL/enrich-batch?limit=$BATCH_SIZE&offset=$OFFSET&status_filter=pending")
    
    PROCESSED=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('result', {}).get('processed', 0))")
    SUCCESS=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('result', {}).get('success', 0))")
    FAILED=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('result', {}).get('failed', 0))")
    
    if [ "$PROCESSED" -eq 0 ]; then
        echo ""
        echo "✅ No more pending dishes to process!"
        break
    fi
    
    TOTAL_PROCESSED=$((TOTAL_PROCESSED + PROCESSED))
    TOTAL_SUCCESS=$((TOTAL_SUCCESS + SUCCESS))
    TOTAL_FAILED=$((TOTAL_FAILED + FAILED))
    OFFSET=$((OFFSET + BATCH_SIZE))
    
    BATCH_TIME=$(($(date +%s) - BATCH_START))
    ELAPSED=$(($(date +%s) - START_TIME))
    
    if [ $ELAPSED -gt 0 ]; then
        RATE=$(echo "scale=2; $TOTAL_PROCESSED / $ELAPSED" | bc)
        REMAINING=$((197430 - TOTAL_PROCESSED))
        ETA=$(echo "scale=1; $REMAINING / $RATE / 3600" | bc)
    else
        RATE=0
        ETA=0
    fi
    
    echo "📦 Batch: $PROCESSED processed ($SUCCESS success, $FAILED failed) in ${BATCH_TIME}s"
    echo "📊 Total: $TOTAL_PROCESSED processed | $TOTAL_SUCCESS success | $TOTAL_FAILED failed"
    echo "⚡ Rate: $RATE dishes/sec | ETA: ${ETA}h"
    echo "------------------------------------------------------------"
    
    # Checkpoint every 100 dishes
    if [ $((TOTAL_PROCESSED % 100)) -eq 0 ]; then
        echo ""
        echo "💾 Checkpoint at $TOTAL_PROCESSED dishes:"
        curl -s "$API_URL/status" | python3 -m json.tool
        echo ""
    fi
    
    # Brief pause
    sleep 1
done

# Final summary
TOTAL_TIME=$(($(date +%s) - START_TIME))
TOTAL_HOURS=$(echo "scale=2; $TOTAL_TIME / 3600" | bc)
AVG_RATE=$(echo "scale=2; $TOTAL_PROCESSED / $TOTAL_TIME" | bc)

echo ""
echo "============================================================"
echo "🎉 Enrichment completed!"
echo "📊 Final Statistics:"
echo "   Total processed: $TOTAL_PROCESSED"
echo "   Successful: $TOTAL_SUCCESS"
echo "   Failed: $TOTAL_FAILED"
echo "   Total time: ${TOTAL_HOURS} hours"
echo "   Average rate: ${AVG_RATE} dishes/sec"
echo ""
echo "📊 Final status:"
curl -s "$API_URL/status" | python3 -m json.tool



