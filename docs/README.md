# Menu OCR Project Documentation

Welcome to the Menu OCR project documentation. This project provides AI-powered menu scanning and restaurant discovery capabilities.

## 📚 Documentation Index

### Core Documentation
- **[LOCAL_MODEL_WEBUI_GUIDE.md](LOCAL_MODEL_WEBUI_GUIDE.md)** - Guide for testing local LLM models with the web UI
- **[xcode_setup_instructions.txt](xcode_setup_instructions.txt)** - Instructions for setting up Xcode integration
- **[XCODE_SYNC_README.md](XCODE_SYNC_README.md)** - README for Xcode synchronization

## 🚀 Quick Start

### For Android Development
1. Open the project in Android Studio
2. Build and run the app on an emulator or device
3. Test the OCR functionality with menu images

### For Backend Development
1. Navigate to `fastapi-menu-service/`
2. Install dependencies: `pip install -r requirements.txt`
3. Run the server: `python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
4. Access API docs at: http://localhost:8000/docs

## 📱 App Features

### DoorDash-Style UI
- **Restaurant Discovery**: Browse and discover restaurants with filtering by cuisine
- **Menu OCR**: Scan menu images using AI-powered OCR technology
- **Google Drive Integration**: Sync and manage menu files in the cloud

### Key Features
- ✅ Modern, clean DoorDash-inspired interface
- ✅ Smooth animations and transitions
- ✅ Real-time restaurant filtering
- ✅ Multi-image OCR processing
- ✅ Google Drive integration (demo mode)
- ✅ Responsive design for various screen sizes

## 🔧 Technical Stack

### Android App
- **Language**: Kotlin
- **UI Framework**: Android XML Layouts
- **Networking**: Retrofit2
- **Image Processing**: ImagePicker library
- **Architecture**: MVVM with Fragments

### Backend Service
- **Framework**: FastAPI
- **OCR Engine**: Qwen Vision Model
- **Database**: Supabase (PostgreSQL)
- **LLM Provider**: Ollama (Local) / Kilocode (Cloud)

## 📁 Project Structure

```
menu-ocr/
├── menu-ocr-android/          # Android application
│   ├── app/
│   │   ├── src/main/
│   │   │   ├── java/com/menuocr/
│   │   │   │   ├── DoorDashMainActivity.kt
│   │   │   │   ├── RestaurantDiscoveryFragment.kt
│   │   │   │   ├── MenuOcrFragment.kt
│   │   │   │   └── GoogleDriveFragment.kt
│   │   │   └── res/
│   │   │       ├── layout/
│   │   │       ├── values/
│   │   │       └── drawable/
│   └── build.gradle.kts
├── fastapi-menu-service/      # Backend API service
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   ├── services/
│   │   └── models.py
│   └── requirements.txt
└── docs/                      # Documentation
    ├── README.md
    ├── LOCAL_MODEL_WEBUI_GUIDE.md
    └── xcode_setup_instructions.txt
```

## 🎨 UI Design System

### Color Palette
- **Primary**: DoorDash Red (#FF3008)
- **Secondary**: Orange (#FF6B35)
- **Accent**: Yellow (#F7931E)
- **Background**: Gray (#F9FAFB)
- **Text**: Dark Gray (#111827)

### Components
- **Cards**: Rounded corners (12dp), elevation (4dp)
- **Buttons**: Primary (filled), Secondary (outlined)
- **Tags**: Color-coded badges for restaurant features
- **Animations**: Smooth transitions with AccelerateDecelerateInterpolator

## 🔐 Configuration

### Environment Variables
Create a `.env` file in `fastapi-menu-service/`:

```env
# Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# LLM Provider
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:32b

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

## 🧪 Testing

### Local Model Testing
Use the web UI to test local LLM models:
1. Open `local-model-webui.html` in your browser
2. Enter a test prompt
3. Click "Test Model"
4. View the response and statistics

### API Testing
Use the FastAPI Swagger UI:
1. Navigate to http://localhost:8000/docs
2. Explore available endpoints
3. Test API calls directly from the browser

## 📝 Development Notes

### Adding New Features
1. Follow the existing MVVM architecture
2. Use DoorDash-style UI components
3. Add proper error handling
4. Include loading states and animations
5. Test on multiple screen sizes

### Code Style
- Kotlin for Android code
- Python for backend services
- Follow existing naming conventions
- Add comments for complex logic
- Use meaningful variable names

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
- Check the documentation in this folder
- Review the code comments
- Open an issue on GitHub

---

**Last Updated**: 2025-02-08
**Version**: 1.0.0
