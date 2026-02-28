# MenuOCR iOS App

A DoorDash-style iOS app for menu OCR and restaurant discovery.

## Features

### 1. Restaurant Discovery (Nearby Tab)
- **Location-based restaurant search** using OpenStreetMap Overpass API
- **DoorDash-like UI** with:
  - Distance slider (1-20 miles)
  - Cuisine category filters
  - Restaurant cards with distance, tags, and delivery info
  - Search functionality
- **Real-time location** using CoreLocation

### 2. Menu OCR (OCR Tab)
- **Camera capture** for menu images
- **Gallery selection** with multi-image support
- **AI-powered OCR** via FastAPI backend
- **Menu item extraction** with dish names, prices, and descriptions
- **Export functionality** for extracted menu items

### 3. Health Conditions (Health Tab)
- **Health profile management** with:
  - Health conditions
  - Allergies
  - Dietary preferences
  - Medical notes
- **Backend sync** with FastAPI

## Architecture

```
MenuOCR/
├── Config/
│   └── AppConfig.swift          # API URLs and configuration
├── Models/
│   └── MenuModels.swift         # Data models
├── Services/
│   ├── ApiService.swift         # FastAPI communication
│   ├── OcrService.swift         # Vision + API OCR
│   ├── LocationService.swift    # CoreLocation wrapper
│   ├── OverpassApiService.swift # Restaurant data
│   ├── SupabaseService.swift    # Auth integration
│   └── PaymentService.swift     # Stripe integration
├── ViewModels/
│   ├── AuthViewModel.swift      # Auth state
│   ├── MenuViewModel.swift      # Menu state
│   └── PaymentViewModel.swift   # Payment state
├── Views/
│   ├── DoorDashTabBarController.swift  # Main tab bar
│   ├── RestaurantDiscoveryViewController.swift
│   ├── MenuOCRViewController.swift
│   ├── HealthConditionsViewController.swift
│   ├── ProfileViewController.swift
│   ├── LoginViewController.swift
│   └── DishTableViewCell.swift
└── Utils/
    └── RetryHelper.swift        # Network retry logic
```

## Requirements

- iOS 15.0+
- Xcode 14.0+
- Swift 5.0+

## Dependencies

The app uses native iOS frameworks:
- **UIKit** - UI framework
- **Vision** - Local OCR processing
- **CoreLocation** - Location services
- **PhotosUI** - Image picking

For Supabase integration, add the Supabase Swift SDK via Swift Package Manager:
```
https://github.com/supabase/supabase-swift
```

## Configuration

Update [`AppConfig.swift`](MenuOCR/Config/AppConfig.swift) with your API endpoints:

```swift
enum AppConfig {
    enum Supabase {
        static let url = "YOUR_SUPABASE_URL"
        static let anonKey = "YOUR_SUPABASE_ANON_KEY"
    }
    
    enum MenuOcrApi {
        static let baseURL = "https://your-api.onrender.com"
        static let localBaseURL = "http://localhost:8000"
        static let useLocal = false  // Set to true for local testing
    }
}
```

## Building

1. Open `MenuOCR.xcodeproj` in Xcode
2. Select your target device or simulator
3. Press ⌘B to build or ⌘R to run

## API Endpoints Used

- `GET /health` - Health check
- `POST /ocr/process` - OCR processing
- `GET /health/profile` - Get health profile
- `POST /health/profile` - Update health profile
- Overpass API for restaurant data

## Permissions Required

The app requires the following permissions (configured in Info.plist):

- **Camera** - To capture menu images
- **Photo Library** - To select menu images
- **Location (When In Use)** - To find nearby restaurants

## Testing

1. Start the FastAPI backend:
   ```bash
   cd fastapi-menu-service
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. Set `useLocal = true` in AppConfig.swift

3. Run the app in simulator or device

## Notes

- The app uses async/await for all network calls
- Retry logic is built into API calls
- Location services handle permission requests gracefully
- OCR uses Vision framework locally before sending to API for better results
