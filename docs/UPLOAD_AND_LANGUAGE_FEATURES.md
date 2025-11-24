# File Upload & Auto Language Detection Features

## ✅ Changes Implemented

### 1. File Upload from Local Machine
- ✅ Frontend now supports direct file uploads (no URL needed)
- ✅ Drag-and-drop interface
- ✅ File preview before upload
- ✅ File validation (type and size)
- ✅ Backend endpoint `/api/v1/ocr/process-upload` for file uploads

### 2. Connection Error Handling
- ✅ Frontend checks backend connection on page load
- ✅ Visual connection status indicator
- ✅ Detailed error messages for connection issues
- ✅ Network error handling in API calls
- ✅ Timeout protection (5 seconds)

### 3. Automatic European Language Detection
- ✅ Detects 25+ European languages automatically
- ✅ Uses keyword matching and character analysis
- ✅ Re-runs OCR with detected language for better accuracy
- ✅ Falls back to English if detection fails

## 🌍 Supported Languages

The system auto-detects these European languages:
- **Western**: English, French, German, Spanish, Italian, Portuguese, Dutch
- **Scandinavian**: Swedish, Norwegian, Danish, Finnish
- **Eastern**: Polish, Russian, Ukrainian, Czech, Slovak, Romanian, Hungarian
- **Balkan**: Bulgarian, Croatian, Serbian
- **Baltic**: Estonian, Latvian, Lithuanian
- **Others**: Greek, Turkish

## 📁 Files Modified

### Frontend
- `components/ImageUpload.tsx` - File upload interface
- `lib/api.ts` - File upload API client with error handling
- `app/page.tsx` - Connection status monitoring

### Backend
- `app/routers/ocr.py` - New `/process-upload` endpoint
- `app/utils/language_detector.py` - Auto-detection logic
- `app/models.py` - Updated default language to "auto"

## 🔄 How It Works

### File Upload Flow
1. User selects image file from local machine
2. Frontend validates file (type, size)
3. Creates preview of image
4. Uploads file as FormData to backend
5. Backend processes with OCR
6. Returns extracted menu items

### Language Detection Flow
1. OCR runs initially with English (or auto)
2. Extracted text is analyzed for language hints
3. System detects most likely European language
4. OCR re-runs with detected language for accuracy
5. Returns results with detected language in metadata

### Connection Monitoring
1. Frontend checks backend health on page load
2. Shows connection status (🟡 checking / ✅ connected / ⚠️ disconnected)
3. Auto-checks every 30 seconds
4. Shows clear error messages if backend is down

## 🚀 Usage

### Frontend
```bash
cd menu-ocr-frontend
npm run dev
# Visit http://localhost:3000
```

### Backend
```bash
cd fastapi-menu-service
source venv/bin/activate
uvicorn app.main:app --reload
```

### Upload Process
1. Click "Upload Menu Image" area
2. Select image file from computer
3. Preview appears
4. Click "Process Image"
5. System auto-detects language
6. Results show extracted menu items

## 🧪 Testing

### Test Language Detection
```python
from app.utils.language_detector import detect_european_language

# French menu
text = "menu prix euros"
detected = detect_european_language(text)
# Returns: "fr"

# German menu
text = "der die das menu preis"
detected = detect_european_language(text)
# Returns: "de"
```

### Test File Upload
```bash
# Using curl
curl -X POST http://localhost:8000/api/v1/ocr/process-upload \
  -F "image=@menu.jpg" \
  -F "use_llm_enhancement=true" \
  -F "language=auto"
```

## 📝 API Endpoints

### File Upload Endpoint
```
POST /api/v1/ocr/process-upload

Form Data:
- image: File (required)
- use_llm_enhancement: bool (default: true)
- language: str (default: "auto")

Response:
{
  "success": true,
  "menu_items": [...],
  "metadata": {
    "detected_language": "fr"
  }
}
```

### URL Endpoint (Still Available)
```
POST /api/v1/ocr/process

Body:
{
  "image_url": "https://...",
  "use_llm_enhancement": true,
  "language": "auto"
}
```

## ⚠️ Error Messages

### Connection Errors
- "Connection error: Could not reach the server. Please check if the backend is running at http://localhost:8000"
- "Backend server is not reachable"
- Shows in UI with red warning banner

### File Errors
- "Please select an image file"
- "Image size exceeds 10MB limit"
- "File must be an image"

## 🔧 Configuration

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend
- Max file size: 10MB (configurable)
- Supported formats: JPG, PNG, JPEG, WEBP
- Auto-language detection: Enabled by default

## ✅ Features Summary

| Feature | Status | Notes |
|---------|--------|-------|
| Local file upload | ✅ | Drag-and-drop + click |
| Connection monitoring | ✅ | Real-time status |
| Error handling | ✅ | Detailed messages |
| Language detection | ✅ | 25+ European languages |
| File preview | ✅ | Before upload |
| File validation | ✅ | Type & size checks |

## 🎯 Next Steps

1. Test with various European menu images
2. Fine-tune language detection accuracy
3. Add support for more languages
4. Add language selection override option

