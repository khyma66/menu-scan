#!/bin/bash
# Continuous enrichment loop using optimal batch size

BATCH_SIZE=50
MAX_BATCHES=${1:-1000}  # Default to 1000 batches, can override
API_URL="http://localhost:8000/menu-enrichment"

echo "=========================================="
echo "Menu Enrichment Loop"
echo "Batch size: $BATCH_SIZE"
echo "Max batches: $MAX_BATCHES"
echo "=========================================="

# Check Ollama
echo "Checking Ollama..."
curl -s "$API_URL/check-ollama" | python3 -m json.tool

# Check initial status
echo -e "\nInitial status:"
curl -s "$API_URL/status" | python3 -m json.tool

offset=0
batch_count=0

while [ $batch_count -lt $MAX_BATCHES ]; do
    batch_count=$((batch_count + 1))
    echo -e "\n=========================================="
    echo "Batch #$batch_count (offset: $offset)"
    echo "=========================================="
    
    result=$(curl -s -X POST "$API_URL/enrich-batch?limit=$BATCH_SIZE&offset=$offset")
    processed=$(echo "$result" | python3 -c "import sys, json; print(json.load(sys.stdin)['result'].get('processed', 0))" 2>/dev/null || echo "0")
    success=$(echo "$result" | python3 -c "import sys, json; print(json.load(sys.stdin)['result'].get('success', 0))" 2>/dev/null || echo "0")
    failed=$(echo "$result" | python3 -c "import sys, json; print(json.load(sys.stdin)['result'].get('failed', 0))" 2>/dev/null || echo "0")
    
    echo "Processed: $processed | Success: $success | Failed: $failed"
    
    if [ "$processed" = "0" ]; then
        echo "✅ No more dishes to process!"
        break
    fi
    
    offset=$((offset + BATCH_SIZE))
    
    # Brief pause between batches
    sleep 2
done

echo -e "\n=========================================="
echo "Final Status:"
echo "=========================================="
curl -s "$API_URL/status" | python3 -m json.tool

