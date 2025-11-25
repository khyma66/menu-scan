#!/bin/bash

# Menu OCR - Xcode Integration Setup Script
# This script helps set up automatic Xcode syncing

set -e

echo "🎯 Setting up Xcode Auto-Sync Integration..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if scripts exist
check_scripts() {
    log_info "Checking sync scripts..."
    if [ ! -x "sync_xcode.sh" ]; then
        log_error "sync_xcode.sh not found or not executable"
        exit 1
    fi
    if [ ! -x "auto_sync_xcode.sh" ]; then
        log_error "auto_sync_xcode.sh not found or not executable"
        exit 1
    fi
    if [ ! -x "xcode_prebuild_sync.sh" ]; then
        log_error "xcode_prebuild_sync.sh not found or not executable"
        exit 1
    fi
    log_success "All sync scripts found and executable"
}

# Test sync functionality
test_sync() {
    log_info "Testing sync functionality..."
    if ./auto_sync_xcode.sh --check > /dev/null 2>&1; then
        log_success "Sync system working correctly"
    else
        log_warning "Sync test completed (may show 'no updates' which is normal)"
    fi
}

# Create Xcode build phase script
create_xcode_instructions() {
    log_info "Creating Xcode integration instructions..."

    cat > xcode_setup_instructions.txt << 'EOF'
XCODE AUTO-SYNC SETUP INSTRUCTIONS
===================================

Follow these steps to integrate auto-sync with Xcode:

1. OPEN XCODE PROJECT:
   - Open menu-ocr-ios/MenuOCR.xcworkspace in Xcode
   - Select the "MenuOCR" project in the Project Navigator

2. ADD PRE-BUILD SCRIPT:
   - Select the "MenuOCR" target
   - Go to "Build Phases" tab
   - Click "+" → "New Run Script Phase"
   - Move it to the top (before "Compile Sources")
   - Name it: "Auto Sync with Repository"
   - Add this script:

   # Auto-sync with latest repository changes
   export AUTO_SYNC_XCODE=true
   "${PROJECT_DIR}/auto_sync_xcode.sh" --quiet

3. SET ENVIRONMENT VARIABLE:
   - In Xcode menu: Product → Scheme → Edit Scheme
   - Select "Build" on the left
   - Click "Pre-actions"
   - Click "+" to add a new pre-action
   - Select your target and build configuration
   - Add environment variable:
     Name: AUTO_SYNC_XCODE
     Value: true

4. TEST THE SETUP:
   - Make a small change to any file
   - Commit and push to repository
   - In Xcode: Product → Clean Build Folder
   - Then: Product → Build
   - Check console for sync messages

5. VERIFY WORKING:
   - Look for these messages in Xcode console:
     🔄 Auto-syncing Xcode project...
     ✅ Xcode project auto-synced

TROUBLESHOOTING:
- If sync fails, check Xcode console for error messages
- Ensure git repository is properly configured
- Make sure all scripts are executable: chmod +x *.sh
- Check that you have push/pull permissions to the repository

ALTERNATIVE MANUAL SYNC:
- Run: ./sync_xcode.sh
- This will sync manually with verbose output
EOF

    log_success "Created xcode_setup_instructions.txt"
}

# Setup environment variables
setup_environment() {
    log_info "Setting up environment variables..."

    # Check if .bashrc or .zshrc exists
    if [ -f "$HOME/.zshrc" ]; then
        SHELL_RC="$HOME/.zshrc"
    elif [ -f "$HOME/.bashrc" ]; then
        SHELL_RC="$HOME/.bashrc"
    else
        log_warning "No shell configuration file found (.zshrc or .bashrc)"
        return
    fi

    # Check if already configured
    if grep -q "AUTO_SYNC_XCODE" "$SHELL_RC"; then
        log_info "Environment variable already configured in $SHELL_RC"
    else
        echo "" >> "$SHELL_RC"
        echo "# Menu OCR - Xcode Auto Sync" >> "$SHELL_RC"
        echo "export AUTO_SYNC_XCODE=true" >> "$SHELL_RC"
        log_success "Added AUTO_SYNC_XCODE=true to $SHELL_RC"
        log_info "Run 'source $SHELL_RC' to apply changes"
    fi
}

# Create desktop shortcut/alias
create_shortcuts() {
    log_info "Creating convenient shortcuts..."

    # Create alias for easy sync
    if [ -f "$HOME/.zshrc" ]; then
        if ! grep -q "alias sync-xcode" "$HOME/.zshrc"; then
            echo "" >> "$HOME/.zshrc"
            echo "# Xcode sync aliases" >> "$HOME/.zshrc"
            echo "alias sync-xcode='./sync_xcode.sh'" >> "$HOME/.zshrc"
            echo "alias check-xcode-updates='./auto_sync_xcode.sh --check'" >> "$HOME/.zshrc"
            log_success "Added sync aliases to .zshrc"
        fi
    fi

    # Create desktop shortcut script
    cat > sync_xcode_desktop.sh << 'EOF'
#!/bin/bash
# Desktop shortcut for Xcode sync
cd /path/to/menu-ocr  # <-- UPDATE THIS PATH
./sync_xcode.sh
EOF

    chmod +x sync_xcode_desktop.sh
    log_success "Created desktop sync script (update path inside)"
}

# Main setup process
main() {
    echo "🚀 Menu OCR - Xcode Auto-Sync Setup"
    echo "===================================="
    echo ""

    check_scripts
    echo ""

    test_sync
    echo ""

    create_xcode_instructions
    echo ""

    setup_environment
    echo ""

    create_shortcuts
    echo ""

    log_success "Xcode auto-sync setup completed!"
    echo ""
    echo "📋 NEXT STEPS:"
    echo "1. Follow instructions in: xcode_setup_instructions.txt"
    echo "2. Configure Xcode as described"
    echo "3. Test with: ./sync_xcode.sh"
    echo "4. Use aliases: sync-xcode, check-xcode-updates"
    echo ""
    echo "🎉 Your Xcode project will now auto-sync with repository changes!"
}

# Run main setup
main "$@"