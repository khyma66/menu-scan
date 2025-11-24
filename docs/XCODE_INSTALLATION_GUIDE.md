# Xcode Installation and iOS App Building Guide

## Current Status
✅ Xcode Command Line Tools installed (version 2408)  
❌ Full Xcode application not installed  

## Step 1: Install Xcode from App Store

1. **App Store is now open** - Search for "Xcode" in the search bar
2. **Click on "Xcode"** (Apple's official Xcode app)
3. **Click "Get" or "Install"** to download Xcode
4. **Wait for download and installation** (this can take 30-60 minutes depending on your internet connection)
5. **Open Xcode** once installation is complete

## Step 2: Install Additional Components

After opening Xcode for the first time:
1. **Agree to the license agreement** when prompted
2. **Install additional components** when prompted (this includes iOS simulators)
3. **Enter your system password** when asked for authentication

## Step 3: Configure Xcode for iOS Development

1. **Open Xcode** → **Preferences** → **Locations**
2. **Select the latest Xcode version** as the Command Line Tools
3. **Go to Preferences** → **Components** to install iOS simulators

## Step 4: Build the Menu OCR iOS App

Once Xcode is installed, you can build the app using either:

### Option A: Using Xcode IDE (Recommended)
```bash
# Open the project in Xcode
open menu-ocr-ios/MenuOCR/MenuOCR.xcworkspace

# Or if you prefer to open from terminal
cd menu-ocr-ios
xed MenuOCR/MenuOCR.xcworkspace
```

### Option B: Using Command Line
```bash
# Navigate to iOS project directory
cd menu-ocr-ios

# Build for iOS simulator (recommended for testing)
xcodebuild -project MenuOCR/MenuOCR.xcodeproj -scheme MenuOCR -destination 'platform=iOS Simulator,name=iPhone 15,OS=latest' build

# Or for iOS device
xcodebuild -project MenuOCR/MenuOCR.xcodeproj -scheme MenuOCR -destination 'generic/platform=iOS' build
```

## Step 5: Run the App

### In Xcode:
1. **Select target device** (iPhone 15 simulator recommended)
2. **Click the Play button** (⌘+R) to build and run

### From command line:
```bash
# Install and run on simulator
xcodebuild -project MenuOCR/MenuOCR.xcodeproj -scheme MenuOCR -destination 'platform=iOS Simulator,name=iPhone 15,OS=latest' run
```

## Prerequisites Verification

Check if everything is ready:
```bash
# Verify Xcode installation
xcode-select --print-path

# List available simulators
xcrun simctl list devices

# Check iOS versions available
xcrun simctl list runtimes
```

## Project Dependencies

The iOS app uses:
- **Swift Package Manager** (built into Xcode)
- **Supabase Swift SDK** (will be downloaded automatically)
- **iOS 15.0+** minimum deployment target

## Troubleshooting

### Common Issues:
1. **"xcode-select: error"** - Means full Xcode app is not installed
2. **Simulator not found** - Install iOS simulators via Xcode
3. **Code signing issues** - Use automatic code signing for development
4. **Build errors** - Check that all source files are present

### Solution for xcode-select error:
```bash
# After installing full Xcode app
sudo xcode-select --reset
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer
```

## Next Steps After Installation

1. **Configure Supabase credentials** in the app
2. **Test with iOS simulator** first
3. **Test on real device** for camera functionality
4. **Deploy to TestFlight** for beta testing
5. **Submit to App Store** when ready

## App Features to Test

- 📷 **Camera functionality** (requires real device)
- 🖼️ **Photo library selection**
- 🔍 **OCR text recognition**
- 🌐 **Backend API integration**
- 🔐 **Supabase authentication**
- 📱 **Native iOS UI**

The app is designed to work with the existing FastAPI backend and Supabase database that are already running.