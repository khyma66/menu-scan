# Menu OCR Android App

A native Android application that uses ML Kit for OCR to extract text from menu images and processes them using a FastAPI backend.

## Features

- 📷 Capture images using device camera
- 🖼️ Select images from gallery
- 🔍 OCR text recognition using Google ML Kit
- 🌐 Backend integration with FastAPI service
- 📱 Native Android UI with Material Design
- 🔄 Real-time menu processing and display

## Tech Stack

- **Language**: Kotlin
- **Architecture**: MVVM with ViewModels
- **Dependency Injection**: Hilt
- **Networking**: Retrofit + OkHttp
- **Image Processing**: ML Kit Text Recognition
- **UI**: View Binding + RecyclerView
- **Async**: Coroutines + Flow

## Setup

1. **Prerequisites**:
   - Android Studio Arctic Fox or later
   - Minimum SDK 24 (Android 7.0)
   - Target SDK 34 (Android 14)

2. **Clone and Open**:
   ```bash
   cd menu-ocr-android
   # Open in Android Studio
   ```

3. **Backend Setup**:
   - Ensure FastAPI backend is running on `http://10.0.2.2:8000` (Android emulator localhost)
   - For physical devices, update the base URL in `AppModule.kt`

4. **Build and Run**:
   - Sync project with Gradle files
   - Run on emulator or physical device

## Permissions

The app requires the following permissions:
- `CAMERA`: For capturing menu images
- `READ_EXTERNAL_STORAGE`: For selecting images from gallery
- `INTERNET`: For API communication

## Architecture

```
app/
├── di/                 # Dependency injection modules
├── viewmodel/          # ViewModels for business logic
├── MainActivity.kt     # Main UI controller
├── OcrProcessor.kt     # ML Kit OCR wrapper
├── ApiService.kt       # Retrofit API interface
├── DishAdapter.kt      # RecyclerView adapter
└── MenuApplication.kt  # Application class
```

## API Integration

The app communicates with the v3 Menu OCR backend through:
- `POST /v1/menus:scan`: Upload pages and enqueue OCR+health analysis
- `GET /v1/jobs/{job_id}`: Poll processing status
- `GET /v1/menus/{menu_id}/personalized`: Fetch personalized dish recommendations
- `GET /v1/user/health-profile`: Fetch user health profile
- `PUT /v1/user/health-profile`: Update user health profile

Legacy endpoints still exist in code for backward compatibility, but new flow uses the v3 routes.

## MCP Server (Android)

A lightweight MCP server was added at [scripts/android_mcp_server.py](../scripts/android_mcp_server.py) and registered in [config/mcp.json](../config/mcp.json) as `android-menu-ocr`.

### One-command local smoke test

From repo root:

`./scripts/smoke_test_v3_mcp.sh`

Optional authenticated run:

`SMOKE_TEST_BEARER_TOKEN=<supabase_access_token> ./scripts/smoke_test_v3_mcp.sh`

## Building for Release

1. **Generate Signed APK/AAB**:
   - Build → Generate Signed Bundle/APK
   - Create/upload keystore

2. **Play Store Requirements**:
   - Update version code/name in `build.gradle.kts`
   - Add store listing assets
   - Configure app content rating
   - Set up pricing and distribution

## Testing

- Unit tests for ViewModels and utilities
- Integration tests for API calls
- UI tests with Espresso
- Manual testing with various menu images

## Contributing

1. Follow Kotlin coding standards
2. Use meaningful commit messages
3. Test on multiple device sizes
4. Update documentation for new features