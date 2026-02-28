#!/bin/bash
# Monitor enrichment progress

echo "📊 Menu Enrichment Progress Monitor"
echo "===================================="
echo ""

# Check if process is running
if ps aux | grep -q "[a]utonomous_enrichment.py"; then
    echo "✅ Enrichment process is RUNNING"
else
    echo "⚠️  Enrichment process is NOT running"
fi

echo ""
echo "📈 Latest Logs:"
tail -15 /tmp/autonomous_enrichment.log 2>/dev/null | tail -10

echo ""
echo "💾 Checkpoint Logs:"
tail -20 enrichment.log 2>/dev/null | grep -E "(Checkpoint|Total|Batch)" | tail -5

echo ""
echo "📊 Database Status (via MCP):"
echo "Run: SELECT enrichment_status, COUNT(*) FROM public.menu GROUP BY enrichment_status;"
