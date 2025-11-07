# Menu OCR iOS App

A native iOS application that uses Apple's Vision framework for OCR to extract text from menu images and processes them using a FastAPI backend with Supabase authentication.

## Features

- 📷 Capture images using device camera
- 🖼️ Select images from photo library
- 🔍 OCR text recognition using Apple's Vision framework
- 🌐 Backend integration with FastAPI service
- 🔐 Supabase authentication (Email/Password)
- 📱 Native iOS UI with SwiftUI and UIKit
- 🔄 Real-time menu processing and display

## Tech Stack

- **Language**: Swift 5.0
- **Architecture**: MVVM with Combine
- **UI Framework**: UIKit with programmatic layout
- **OCR**: Apple's Vision framework
- **Networking**: URLSession with async/await
- **Authentication**: Supabase Swift SDK
- **Dependency Management**: Swift Package Manager

## Setup

### Prerequisites
- Xcode 15.0 or later
- iOS 15.0 or later
- Swift 5.0 or later

### Installation

1. **Clone and Open**:
   ```bash
   cd menu-ocr-ios
   open MenuOCR.xcworkspace
   ```

2. **Install Dependencies**:
   - The project uses Swift Package Manager
   - Supabase dependency will be automatically resolved

3. **Backend Setup**:
   - Ensure FastAPI backend is running
   - Update `SupabaseService.swift` with your Supabase credentials
   - Update `ApiService.swift` with your backend URL

4. **Run**:
   - Select a simulator or device
   - Build and run (Cmd + R)

## Architecture

```
MenuOCR/
├── Models/                 # Data models (MenuModels.swift)
├── Views/                  # UI ViewControllers
│   ├── LoginViewController.swift
│   ├── MainViewController.swift
│   └── DishTableViewCell.swift
├── ViewModels/             # Business logic
│   ├── MenuViewModel.swift
│   └── AuthViewModel.swift
├── Services/               # External integrations
│   ├── OcrService.swift    # Vision OCR
│   ├── ApiService.swift    # FastAPI client
│   └── SupabaseService.swift # Auth & DB
└── Utilities/              # Helpers
```

## Permissions

The app requires the following permissions in `Info.plist`:
- `NSCameraUsageDescription`: Camera access for capturing menu images
- `NSPhotoLibraryUsageDescription`: Photo library access for selecting images

## API Integration

The app communicates with the FastAPI backend through:
- `POST /ocr/process`: Process image for OCR
- `POST /dishes/extract`: Extract dishes from text

## Supabase Integration

- **Authentication**: Email/password sign in/up
- **Database**: User session management
- **Storage**: Potential for image storage (future feature)

## Building for App Store

1. **Code Signing**:
   - Create Apple Developer account
   - Generate provisioning profiles
   - Configure code signing in Xcode

2. **App Store Connect**:
   - Create app record
   - Upload screenshots and metadata
   - Configure in-app purchases if needed

3. **Build & Upload**:
   - Archive build (Product → Archive)
   - Upload using Xcode or Transporter

## Testing

- Unit tests for ViewModels and Services
- UI tests with Xcode's testing framework
- Integration tests for API calls
- Manual testing on multiple device sizes

## Contributing

1. Follow Swift coding guidelines
2. Use meaningful commit messages
3. Test on multiple iOS versions
4. Update documentation for new features

## Cross-Platform Sync

This iOS app is designed to work alongside the Android version, sharing:
- Same Supabase backend and authentication
- Same FastAPI endpoints and data models
- Consistent user experience across platforms