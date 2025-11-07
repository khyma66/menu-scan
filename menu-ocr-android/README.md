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

The app communicates with the FastAPI backend through:
- `POST /ocr/process`: Process image for OCR
- `POST /dishes/extract`: Extract dishes from text

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