#!/bin/bash

# Menu OCR Android - Complete Setup and Testing Script
# This script completes all next steps for Android deployment

set -e  # Exit on error

echo "========================================="
echo "Menu OCR Android - Complete Setup"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Update credentials
echo -e "${YELLOW}Step 1: Checking Configuration...${NC}"
echo ""
echo "Supabase URL: https://jlfqzcaospvspmzbvbxd.supabase.co"
echo "Supabase Dashboard: https://supabase.com/dashboard/project/jlfqzcaospvspmzbvbxd/settings/api"
echo ""
echo -e "${YELLOW}ACTION REQUIRED:${NC}"
echo "1. Go to Supabase Dashboard (link above)"
echo "2. Copy the 'anon/public' key"
echo "3. Update menu-ocr-android/app/src/main/java/com/menuocr/AppConfig.kt"
echo "   - Replace 'YOUR_SUPABASE_ANON_KEY_HERE' with your actual anon key"
echo "4. Update Render BASE_URL if you have deployed to Render"
echo ""
read -p "Press Enter when you've updated the credentials..."

# Step 2: Set JAVA_HOME
echo ""
echo -e "${YELLOW}Step 2: Setting up Java environment...${NC}"
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
echo "JAVA_HOME set to: $JAVA_HOME"

# Step 3: Clean and build
echo ""
echo -e "${YELLOW}Step 3: Building Android project...${NC}"
cd menu-ocr-android

# Clean previous builds
echo "Cleaning previous builds..."
./gradlew clean

# Build debug APK
echo "Building debug APK..."
./gradlew assembleDebug

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Build successful!${NC}"
    echo "APK location: app/build/outputs/apk/debug/app-debug.apk"
else
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi

# Step 4: Check for connected devices
echo ""
echo -e "${YELLOW}Step 4: Checking for Android devices...${NC}"
adb devices -l

# Step 5: Install APK
echo ""
echo -e "${YELLOW}Step 5: Installing APK...${NC}"
read -p "Do you want to install the APK on a connected device? (y/n): " install_choice

if [ "$install_choice" = "y" ] || [ "$install_choice" = "Y" ]; then
    ./gradlew installDebug
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ APK installed successfully!${NC}"
    else
        echo -e "${RED}✗ Installation failed${NC}"
        echo "Make sure a device is connected and USB debugging is enabled"
    fi
fi

# Step 6: Run the app
echo ""
echo -e "${YELLOW}Step 6: Launching app...${NC}"
read -p "Do you want to launch the app now? (y/n): " launch_choice

if [ "$launch_choice" = "y" ] || [ "$launch_choice" = "Y" ]; then
    adb shell am start -n com.menuocr/.MainActivity
    echo -e "${GREEN}✓ App launched!${NC}"
fi

# Step 7: Monitor logs
echo ""
echo -e "${YELLOW}Step 7: Monitoring logs...${NC}"
echo "You can monitor app logs with:"
echo "  adb logcat -s RetryHelper SupabaseClient ApiClient"
echo ""
read -p "Do you want to start monitoring logs now? (y/n): " logs_choice

if [ "$logs_choice" = "y" ] || [ "$logs_choice" = "Y" ]; then
    echo "Starting log monitor (Ctrl+C to stop)..."
    adb logcat -s RetryHelper SupabaseClient ApiClient PaymentService
fi

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Test Supabase authentication in the app"
echo "2. Test API connectivity to Render"
echo "3. Verify retry logic by simulating network failures"
echo ""
echo "Documentation:"
echo "- ANDROID_DEPLOYMENT_GUIDE.md - Complete deployment guide"
echo "- RETRY_LOGIC_IMPLEMENTATION_COMPLETE.md - Retry implementation details"
echo ""
