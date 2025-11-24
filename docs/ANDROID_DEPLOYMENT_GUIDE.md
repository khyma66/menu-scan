# Android Studio Deployment Guide - Menu OCR with Supabase & Render

## ✅ Build Status: SUCCESS

The Android project has been successfully built with all dependencies configured and retry logic implemented.

## 📦 What Was Configured

### 1. Dependencies Added
All necessary dependencies have been added to [`menu-ocr-android/app/build.gradle.kts`](menu-ocr-android/app/build.gradle.kts):

- ✅ **Supabase SDK** (GoTrue, Postgrest, Storage)
- ✅ **Ktor Client** for Supabase networking
- ✅ **Kotlin Serialization** for JSON handling
- ✅ **Retrofit** for Render API calls
- ✅ **OkHttp** with logging interceptor
- ✅ **ML Kit** for OCR
- ✅ **Coroutines** for async operations
- ✅ **Room Database** for local storage
- ✅ **Work Manager** for background tasks

### 2. New Files Created

#### Configuration
- [`AppConfig.kt`](menu-ocr-android/app/src/main/java/com/menuocr/AppConfig.kt) - Centralized configuration for Supabase and Render

#### Retry Logic
- [`RetryHelper.kt`](menu-ocr-android/app/src/main/java/com/menuocr/RetryHelper.kt) - Retry utility with 10-second delay

#### Services
- [`SupabaseClient.kt`](menu-ocr-android/app/src/main/java/com/menuocr/SupabaseClient.kt) - Supabase authentication and database operations
- [`ApiClient.kt`](menu-ocr-android/app/src/main/java/com/menuocr/ApiClient.kt) - Retrofit client for Render API
- [`PaymentService.kt`](menu-ocr-android/app/src/main/java/com/menuocr/PaymentService.kt) - Payment operations with retry

## 🔧 Configuration Steps

### Step 1: Update Supabase Credentials

Edit [`AppConfig.kt`](menu-ocr-android/app/src/main/java/com/menuocr/AppConfig.kt:14-18):

```kotlin
object Supabase {
    const val URL = "YOUR_SUPABASE_PROJECT_URL"  // e.g., https://xxxxx.supabase.co
    const val ANON_KEY = "YOUR_SUPABASE_ANON_KEY"  // Get from Supabase dashboard
}
```

**Where to find these:**
1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to Settings → API
4. Copy "Project URL" and "anon/public" key

### Step 2: Update Render API Endpoint

Edit [`AppConfig.kt`](menu-ocr-android/app/src/main/java/com/menuocr/AppConfig.kt:23):

```kotlin
object Render {
    const val BASE_URL = "YOUR_RENDER_DEPLOYMENT_URL"  // e.g., https://your-app.onrender.com
}
```

**Where to find this:**
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Select your web service
3. Copy the URL (e.g., `https://menu-ocr-api.onrender.com`)

### Step 3: Update Stripe Key (Optional)

If using payments, edit [`AppConfig.kt`](menu-ocr-android/app/src/main/java/com/menuocr/AppConfig.kt:38):

```kotlin
object Stripe {
    const val PUBLISHABLE_KEY = "pk_test_your_stripe_publishable_key"
}
```

## 🚀 Building and Running

### Option 1: Using Android Studio

1. **Open Project:**
   ```bash
   open -a "Android Studio" menu-ocr-android
   ```

2. **Sync Gradle:**
   - Android Studio will automatically sync
   - Or click "Sync Project with Gradle Files" in toolbar

3. **Build:**
   - Click "Build" → "Make Project" (⌘F9)
   - Or use "Build" → "Build Bundle(s) / APK(s)" → "Build APK(s)"

4. **Run:**
   - Click the green "Run" button (▶️)
   - Or press Ctrl+R
   - Select an emulator or connected device

### Option 2: Using Command Line

```bash
cd menu-ocr-android

# Set JAVA_HOME to Android Studio's JDK
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"

# Build debug APK
./gradlew assembleDebug

# Build release APK
./gradlew assembleRelease

# Install on connected device
./gradlew installDebug

# Run on connected device
./gradlew installDebug && adb shell am start -n com.menuocr/.MainActivity
```

### APK Location
After building, find the APK at:
```
menu-ocr-android/app/build/outputs/apk/debug/app-debug.apk
```

## 📱 Testing Connectivity

### Test Supabase Connection

```kotlin
// In your Activity or ViewModel
lifecycleScope.launch {
    val isAuth = SupabaseClient.isAuthenticated()
    Log.d("Supabase", "Authenticated: $isAuth")
    
    // Test sign up
    val result = SupabaseClient.signUp("test@example.com", "password123")
    result.onSuccess {
        Log.d("Supabase", "Sign up successful!")
    }.onFailure { error ->
        Log.e("Supabase", "Sign up failed: ${error.message}")
    }
}
```

### Test Render API Connection

```kotlin
// In your Activity or ViewModel
lifecycleScope.launch {
    try {
        val paymentService = ApiClient.getPaymentService()
        val health = paymentService.checkHealth()
        
        if (health.isSuccessful) {
            Log.d("Render", "API is healthy: ${health.body()}")
        } else {
            Log.e("Render", "API error: ${health.code()}")
        }
    } catch (e: Exception) {
        Log.e("Render", "Connection failed: ${e.message}")
    }
}
```

## 🔄 Retry Logic Features

All API calls automatically retry on failure with:
- **Delay:** 10 seconds between retries
- **Max Attempts:** 3 attempts
- **Logging:** Detailed logs for each attempt

Example usage:
```kotlin
// Automatic retry for payment operations
val result = paymentService.createPaymentIntent(request)

// Automatic retry for Supabase operations
val signInResult = SupabaseClient.signIn(email, password)
```

## 🐛 Troubleshooting

### Build Errors

**Issue:** `JAVA_HOME is set to an invalid directory`
```bash
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
```

**Issue:** Gradle sync fails
```bash
cd menu-ocr-android
./gradlew clean
./gradlew build --refresh-dependencies
```

### Runtime Errors

**Issue:** Network security error
- Add network security config in `AndroidManifest.xml`
- Allow cleartext traffic for development

**Issue:** Supabase connection fails
- Verify URL and anon key in `AppConfig.kt`
- Check internet permissions in `AndroidManifest.xml`
- Ensure device/emulator has internet connection

**Issue:** Render API timeout
- Check Render service is running
- Verify BASE_URL in `AppConfig.kt`
- Check firewall/network settings

## 📊 Monitoring

### View Logs

```bash
# View all logs
adb logcat

# Filter by tag
adb logcat -s RetryHelper
adb logcat -s SupabaseClient
adb logcat -s ApiClient

# Clear logs
adb logcat -c
```

### Check Network Traffic

Use Android Studio's Network Profiler:
1. Run app in debug mode
2. Open "Profiler" tab
3. Select "Network"
4. Monitor API calls and responses

## 🔐 Security Notes

### Before Production:

1. **Move secrets to BuildConfig:**
   ```kotlin
   // In build.gradle.kts
   buildConfigField("String", "SUPABASE_URL", "\"${project.findProperty("SUPABASE_URL")}\"")
   ```

2. **Enable ProGuard:**
   ```kotlin
   buildTypes {
       release {
           isMinifyEnabled = true
           proguardFiles(...)
       }
   }
   ```

3. **Use environment variables:**
   - Store secrets in `local.properties`
   - Add `local.properties` to `.gitignore`

4. **Enable SSL pinning** for production API calls

## 📝 Next Steps

### Recommended Testing Sequence:

1. ✅ **Build Verification** - COMPLETE
2. **Supabase Auth Test:**
   - Sign up new user
   - Sign in existing user
   - Check session persistence

3. **Render API Test:**
   - Health check endpoint
   - OCR processing
   - Payment intent creation

4. **End-to-End Test:**
   - Capture menu image
   - Process with OCR
   - Extract dishes
   - Save to Supabase
   - Create payment

5. **Retry Logic Test:**
   - Simulate network failure
   - Verify automatic retry
   - Check retry logs

### Performance Optimization:

- Enable R8 code shrinking
- Optimize image sizes
- Implement caching strategy
- Use WorkManager for background sync

## 📚 Additional Resources

- [Supabase Android Documentation](https://supabase.com/docs/reference/kotlin/introduction)
- [Retrofit Documentation](https://square.github.io/retrofit/)
- [Android Kotlin Coroutines](https://developer.android.com/kotlin/coroutines)
- [ML Kit Text Recognition](https://developers.google.com/ml-kit/vision/text-recognition)

## ✅ Deployment Checklist

- [x] Dependencies configured
- [x] Retry logic implemented
- [x] Supabase client created
- [x] Render API client created
- [x] Build successful
- [ ] Update Supabase credentials
- [ ] Update Render API endpoint
- [ ] Test Supabase connection
- [ ] Test Render API connection
- [ ] Run on emulator/device
- [ ] Verify retry logic
- [ ] Test end-to-end flow

---

**Build Date:** 2025-01-21  
**Status:** ✅ Ready for Configuration and Testing  
**APK:** `menu-ocr-android/app/build/outputs/apk/debug/app-debug.apk`
