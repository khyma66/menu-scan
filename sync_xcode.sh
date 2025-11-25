#!/bin/bash

# Menu OCR - Xcode Auto Sync Script
# This script automatically syncs the latest changes to Xcode project

echo "🔄 Syncing Xcode project with latest changes..."

# Navigate to the iOS project directory
cd menu-ocr-ios/MenuOCR

# Pull latest changes from git
echo "📥 Pulling latest changes from git..."
git pull origin main

# Check if there were any changes
if [ $? -eq 0 ]; then
    echo "✅ Successfully synced with latest changes"

    # Show what was updated
    echo "📋 Recent commits:"
    git log --oneline -5

    # Optional: Clean and rebuild if needed
    echo "🧹 Cleaning Xcode project..."
    xcodebuild clean -project MenuOCR.xcodeproj -scheme MenuOCR

    echo "🎉 Xcode project is now up to date!"
    echo "💡 Open MenuOCR.xcodeproj in Xcode and run the app"
else
    echo "❌ Failed to sync changes. Please check your git connection."
    exit 1
fi