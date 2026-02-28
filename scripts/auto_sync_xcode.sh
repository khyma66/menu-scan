#!/bin/bash

# Menu OCR - Advanced Xcode Auto Sync Script
# This script provides multiple ways to automatically sync Xcode with latest changes

set -e  # Exit on any error

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IOS_DIR="$PROJECT_DIR/menu-ocr-ios/MenuOCR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Xcode project needs update
check_for_updates() {
    log_info "Checking for updates..."

    # Fetch latest changes without merging
    git fetch origin main

    # Check if we're behind
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/main)

    if [ "$LOCAL" != "$REMOTE" ]; then
        log_info "Updates available. Local: $LOCAL, Remote: $REMOTE"
        return 0  # Updates available
    else
        log_info "Already up to date"
        return 1  # No updates
    fi
}

# Function to sync Xcode project
sync_xcode_project() {
    log_info "Syncing Xcode project..."

    # Navigate to iOS directory
    cd "$IOS_DIR"

    # Pull latest changes
    if git pull origin main; then
        log_success "Successfully pulled latest changes"

        # Show what changed
        log_info "Recent changes:"
        git log --oneline -3

        # Clean build artifacts
        log_info "Cleaning Xcode build artifacts..."
        rm -rf ~/Library/Developer/Xcode/DerivedData/MenuOCR-* 2>/dev/null || true

        # Optional: Update CocoaPods if Podfile exists
        if [ -f "Podfile" ]; then
            log_info "Updating CocoaPods..."
            pod install
        fi

        log_success "Xcode project synced successfully!"
        return 0
    else
        log_error "Failed to pull changes"
        return 1
    fi
}

# Function to setup Xcode pre-build script
setup_xcode_prebuild() {
    log_info "Setting up Xcode pre-build auto-sync..."

    # Create a pre-build script that can be added to Xcode
    cat > xcode_prebuild_sync.sh << 'EOF'
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
EOF

    chmod +x xcode_prebuild_sync.sh
    log_success "Created xcode_prebuild_sync.sh for Xcode integration"
}

# Function to setup git hooks
setup_git_hooks() {
    log_info "Setting up git hooks for auto-sync..."

    # Create post-merge hook
    mkdir -p .git/hooks
    cat > .git/hooks/post-merge << 'EOF'
#!/bin/bash

# Git Post-Merge Hook for Xcode Auto-Sync
echo "🔄 Git merge detected, checking if Xcode project needs sync..."

# Check if iOS files were changed
if git diff-tree -r --name-only HEAD~1 HEAD | grep -q "menu-ocr-ios/"; then
    echo "📱 iOS files changed, consider running: ./auto_sync_xcode.sh"
fi
EOF

    chmod +x .git/hooks/post-merge
    log_success "Created git post-merge hook"
}

# Main execution
case "${1:-}" in
    "--check")
        if check_for_updates; then
            echo "Updates available"
            exit 0
        else
            echo "No updates"
            exit 1
        fi
        ;;
    "--setup-xcode")
        setup_xcode_prebuild
        ;;
    "--setup-hooks")
        setup_git_hooks
        ;;
    "--quiet")
        # Quiet mode for automated scripts
        if check_for_updates > /dev/null 2>&1; then
            sync_xcode_project > /dev/null 2>&1
        fi
        ;;
    "--help"|"-h")
        echo "Menu OCR - Xcode Auto Sync Script"
        echo ""
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --check        Check for updates without syncing"
        echo "  --setup-xcode  Setup Xcode pre-build integration"
        echo "  --setup-hooks  Setup git hooks for auto-sync"
        echo "  --quiet        Run silently (for automation)"
        echo "  --help, -h     Show this help"
        echo ""
        echo "Without options, performs full sync with verbose output"
        ;;
    *)
        # Default: full sync
        if check_for_updates; then
            sync_xcode_project
        else
            log_info "No updates needed"
        fi
        ;;
esac