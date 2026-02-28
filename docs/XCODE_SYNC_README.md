# Xcode Auto-Sync Setup Guide

This guide shows you how to automatically sync your Xcode project with the latest changes from the repository.

## 🚀 Quick Start

### Option 1: Manual Sync (Simplest)
```bash
# Run this whenever you want to sync
./sync_xcode.sh
```

### Option 2: Advanced Auto-Sync (Recommended)
```bash
# Setup automatic syncing
./auto_sync_xcode.sh --setup-hooks
./auto_sync_xcode.sh --setup-xcode
```

## 📋 Available Scripts

### `sync_xcode.sh` - Basic Sync
- Pulls latest changes from git
- Cleans Xcode build artifacts
- Shows recent commits

### `auto_sync_xcode.sh` - Advanced Sync
Multiple options for different automation levels:

```bash
# Check for updates without syncing
./auto_sync_xcode.sh --check

# Setup Xcode pre-build integration
./auto_sync_xcode.sh --setup-xcode

# Setup git hooks for automatic sync on merge
./auto_sync_xcode.sh --setup-hooks

# Run silently (for automation scripts)
./auto_sync_xcode.sh --quiet

# Show help
./auto_sync_xcode.sh --help
```

## 🔧 Xcode Integration Setup

### Method 1: Pre-Build Script (Recommended)

1. **Setup the script:**
   ```bash
   ./auto_sync_xcode.sh --setup-xcode
   ```

2. **Add to Xcode:**
   - Open your project in Xcode
   - Go to **MenuOCR Target** → **Build Phases**
   - Click **+** → **New Run Script Phase**
   - Add this script:
   ```bash
   export AUTO_SYNC_XCODE=true
   "${PROJECT_DIR}/auto_sync_xcode.sh" --quiet
   ```

3. **Set environment variable:**
   - In Xcode: **Product** → **Scheme** → **Edit Scheme**
   - **Build** → **Pre-actions**
   - Add environment variable: `AUTO_SYNC_XCODE = true`

### Method 2: Git Hooks (Automatic)

```bash
./auto_sync_xcode.sh --setup-hooks
```

This creates a git post-merge hook that notifies you when iOS files change.

### Method 3: Manual Integration

Add this to your build process:
```bash
# In your CI/CD or build script
if [ "$AUTO_SYNC_ENABLED" = "true" ]; then
    ./auto_sync_xcode.sh --quiet
fi
```

## 🎯 What Gets Synced

- ✅ **Swift files** (.swift)
- ✅ **Storyboards** (.storyboard)
- ✅ **XIB files** (.xib)
- ✅ **Asset catalogs** (.xcassets)
- ✅ **Configuration files** (Info.plist, etc.)
- ✅ **Dependencies** (Podfile updates)

## 🔄 Sync Process

1. **Fetch** latest changes from remote
2. **Compare** local vs remote commits
3. **Pull** changes if available
4. **Clean** Xcode derived data
5. **Update** CocoaPods (if needed)
6. **Report** sync status

## 🚨 Troubleshooting

### Sync Fails
```bash
# Check git status
git status

# Check remote connection
git remote -v

# Manual pull
cd menu-ocr-ios/MenuOCR
git pull origin main
```

### Xcode Build Issues After Sync
```bash
# Clean build folder
rm -rf ~/Library/Developer/Xcode/DerivedData/MenuOCR-*

# Clean and rebuild in Xcode
# Product → Clean Build Folder
# Product → Build
```

### Permission Issues
```bash
# Make scripts executable
chmod +x sync_xcode.sh
chmod +x auto_sync_xcode.sh
```

## 📊 Status Indicators

- 🔄 **Syncing...** - Pulling latest changes
- ✅ **Success** - Sync completed successfully
- ❌ **Failed** - Sync encountered errors
- ⚠️ **Warning** - Non-critical issues

## 🎛️ Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AUTO_SYNC_XCODE` | Enable auto-sync in Xcode | `false` |
| `QUIET_MODE` | Suppress output | `false` |

## 📱 Usage Examples

### Before Opening Xcode
```bash
# Always sync before starting work
./sync_xcode.sh
open menu-ocr-ios/MenuOCR.xcworkspace
```

### In CI/CD Pipeline
```bash
#!/bin/bash
# ci_build.sh

# Sync code
./auto_sync_xcode.sh --quiet

# Build iOS app
xcodebuild -project menu-ocr-ios/MenuOCR/MenuOCR.xcodeproj \
           -scheme MenuOCR \
           -sdk iphoneos \
           -configuration Release \
           archive
```

### Development Workflow
```bash
# Check for updates
./auto_sync_xcode.sh --check

# If updates available, sync
./sync_xcode.sh

# Continue development
```

## 🔐 Security Notes

- Scripts only pull from configured remote
- No automatic pushing or force operations
- Safe to run multiple times
- Respects your git configuration

## 📞 Support

If you encounter issues:

1. Check the script output for error messages
2. Verify your git remote configuration
3. Ensure you have write access to the repository
4. Check Xcode and macOS versions

---

**Happy coding! 🎉** Your Xcode project will now stay automatically synchronized with the latest changes.