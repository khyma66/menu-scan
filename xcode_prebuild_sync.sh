#!/bin/bash

# Xcode Pre-Build Auto Sync Script
# Add this script to Xcode Build Phases > Pre-actions

PROJECT_DIR="${PROJECT_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"

# Check if we should auto-sync (can be controlled by environment variable)
if [ "$AUTO_SYNC_XCODE" = "true" ]; then
    echo "🔄 Auto-syncing Xcode project..."

    # Run the sync script
    if "$PROJECT_DIR/auto_sync_xcode.sh" --quiet; then
        echo "✅ Xcode project auto-synced"
    else
        echo "⚠️  Auto-sync failed, but continuing build..."
    fi
fi
