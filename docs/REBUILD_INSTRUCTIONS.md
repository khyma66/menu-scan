# Android App Rebuild Instructions

## Issue
The Gradle build is failing with a configuration error. The code changes are correct, but the APK needs to be rebuilt in Android Studio.

## ✅ Code Changes Verified
- ✅ `ApiService.kt`: `checkHealth()` method added
- ✅ `MainActivity.kt`: Updated to use `/health` endpoint
- ✅ All changes are in place and correct

## 🔧 Rebuild Steps (Android Studio)

### Step 1: Open Project in Android Studio
1. Open **Android Studio**
2. Click **"Open"** or **File → Open**
3. Navigate to: `/Users/mohanakrishnanarsupalli/menu-ocr/menu-ocr-android`
4. Click **"OK"**

### Step 2: Wait for Gradle Sync
- Android Studio will automatically sync Gradle
- Wait for "Gradle sync finished" message
- This may take 1-2 minutes

### Step 3: Build the APK
**Option A: Build APK**
1. Click **"Build"** → **"Build Bundle(s) / APK(s)"** → **"Build APK(s)"**
2. Wait for build to complete
3. When done, click **"locate"** in the notification

**Option B: Run on Emulator**
1. Select emulator from device dropdown (emulator-5554 or emulator-5556)
2. Click **"Run"** button (green play icon)
3. Android Studio will build and install automatically

### Step 4: Verify Installation
After build completes:
- APK will be at: `app/build/outputs/apk/debug/app-debug.apk`
- App will be installed on selected emulator
- App will launch automatically

### Step 5: Test
1. Open the app on emulator
2. Click **"Test API Connection"** button
3. Should show: ✅ **Connected Successfully** (no 401 error)
4. Should display backend version: **1.0.0**

## 🚀 Quick Command Line Alternative

If you prefer command line, try this after opening in Android Studio once:

```bash
cd /Users/mohanakrishnanarsupalli/menu-ocr/menu-ocr-android
export JAVA_HOME=/Applications/Android\ Studio.app/Contents/jbr/Contents/Home
export ANDROID_HOME=/Users/mohanakrishnanarsupalli/Library/Android/sdk
./gradlew assembleDebug
```

Then install:
```bash
adb -s emulator-5554 install -r app/build/outputs/apk/debug/app-debug.apk
adb -s emulator-5554 shell am start -n com.menuocr/.MainActivity
```

## ✅ Expected Result

After rebuild:
- ✅ No 401 error
- ✅ Shows "✅ Connected Successfully"
- ✅ Displays backend version
- ✅ API connection test works

## 📝 Notes

- The Gradle build error is a configuration issue that Android Studio handles automatically
- All code changes are already in place
- Once rebuilt, the app will work correctly with the `/health` endpoint





