# Android Studio MCP Server Testing Guide

## Overview
This guide provides step-by-step instructions for testing the Menu OCR Android application with MCP server integration using Android Studio.

## Prerequisites

### 1. System Requirements
- macOS Sonoma 14.5+ (compatible with current setup)
- Android Studio Arctic Fox or later
- Java JDK 17 (required for Android development)
- Android SDK with API level 24+ support
- Physical Android device or Android emulator

### 2. Environment Setup
```bash
# Install Java JDK 17 if not present
brew install openjdk@17

# Set JAVA_HOME
export JAVA_HOME=$(/usr/libexec/java_home -v 17)

# Verify Java installation
java -version
javac -version
```

## Project Configuration

### 1. Android Studio Project Setup

1. **Open Project**: Launch Android Studio and open the `menu-ocr-android` project
2. **Sync Project**: Allow Gradle sync to complete
3. **SDK Configuration**: Ensure Android SDK API 34 is installed and configured

### 2. MCP Server Configuration

The project includes MCP server configuration in `mcp.json`:

```json
{
  "mcpServers": {
    "render": {
      "url": "https://mcp.render.com/mcp",
      "headers": {
        "Authorization": "Bearer <rnd_7YOAuj8CSc9XjDg0oRqaDPLZVIJZ>"
      }
    },
    "apify": {
      "url": "https://mcp.apify.com",
      "headers": {
        "Authorization": "Bearer <apify_api_fN0eoFyxQqYNBYWI96VQrmlVNc7JuA2Ra4OL>"
      }
    }
  }
}
```

### 3. Backend Service Setup

1. **Start FastAPI Backend**:
   ```bash
   cd fastapi-menu-service
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Verify Backend Health**:
   ```bash
   curl http://localhost:8000/health
   ```

## Testing Scenarios

### Test 1: Basic App Launch

1. **Run Application**:
   - Click "Run" button in Android Studio
   - Select target device (emulator or physical device)
   - Wait for app to launch

2. **Expected Results**:
   - App displays "Menu OCR - Enhanced Version" title
   - API status shows "FastAPI Backend: http://10.0.2.2:8000"
   - Status displays "Ready to test OCR functionality"

### Test 2: API Connectivity

1. **Test API Connection**:
   - Tap "Test API Connection" button
   - Wait for connection test to complete

2. **Expected Results**:
   - Green checkmark (✅) appears for successful connection
   - Toast message shows "API test completed successfully!"
   - Status shows "✅ API connection test successful!"

### Test 3: Image Capture and OCR

1. **Select Image Source**:
   - Tap "Capture Image" or "Select from Gallery"
   - Grant camera/storage permissions when prompted

2. **OCR Processing**:
   - Select an image containing menu text
   - Tap "Process with OCR" button

3. **Expected Results**:
   - Image appears in the ImageView
   - OCR results display in the result text area
   - Status shows "✅ OCR processing completed successfully!"

## Debugging Common Issues

### Issue 1: Build Failures

**Problem**: Gradle build fails due to Hilt dependencies

**Solution**: Hilt has been disabled in the current version
- Dependencies are commented out in `build.gradle.kts`
- Manual dependency management implemented in `MainActivity.kt`

### Issue 2: API Connection Fails

**Problem**: App cannot connect to FastAPI backend

**Solutions**:
1. Verify FastAPI server is running on port 8000
2. Check emulator networking: use `http://10.0.2.2:8000` (not `localhost`)
3. Verify cleartext traffic is enabled in AndroidManifest.xml
4. Check firewall settings

### Issue 3: Camera/Gallery Permissions

**Problem**: App crashes when accessing camera or gallery

**Solutions**:
1. Ensure permissions are granted in device settings
2. Check AndroidManifest.xml includes required permissions
3. Verify ImagePicker library is properly configured

### Issue 4: OCR Processing Fails

**Problem**: OCR processing shows error messages

**Solutions**:
1. Verify image is selected before processing
2. Check ML Kit dependencies are correctly configured
3. Ensure image format is supported (JPEG/PNG)

## MCP Server Integration Testing

### Test MCP Server Connectivity

```bash
# Test Render MCP Server
curl -X POST "https://mcp.render.com/mcp" \
  -H "Authorization: Bearer <rnd_7YOAuj8CSc9XjDg0oRqaDPLZVIJZ>" \
  -H "Content-Type: application/json" \
  -d '{"method": "ping"}'

# Test Apify MCP Server
curl -X POST "https://mcp.apify.com" \
  -H "Authorization: Bearer <apify_api_fN0eoFyxQqYNBYWI96VQrmlVNc7JuA2Ra4OL>" \
  -H "Content-Type: application/json" \
  -d '{"method": "ping"}'
```

### Integration with Android App

The Android app can be enhanced to use MCP servers for:
- Advanced OCR processing via external services
- Cloud-based image enhancement
- Translation services
- Data synchronization

## Performance Testing

### Memory Usage
- Monitor memory usage during OCR processing
- Verify proper bitmap cleanup
- Check for memory leaks in long-running sessions

### Network Performance
- Test API response times
- Measure image upload/download speeds
- Verify offline functionality

### Battery Impact
- Monitor battery usage during extended use
- Test power efficiency of ML Kit OCR
- Optimize background processing

## Security Testing

### Data Protection
- Verify image data encryption in transit
- Test secure API communication
- Check for data retention policies

### Authentication
- Test API key security
- Verify token-based authentication
- Check for session management

## Test Results Documentation

Use this template to document test results:

```
Test Case: [Test Name]
Date: [Test Date]
Device: [Device Information]
Android Version: [Version]
Status: [PASS/FAIL]
Issues Found: [Description]
Screenshots: [File paths]
```

## Next Steps

1. **Automated Testing**: Implement Espresso tests for UI automation
2. **Unit Tests**: Add JUnit tests for business logic
3. **Integration Tests**: Create end-to-end test scenarios
4. **Performance Monitoring**: Add analytics for real-world usage
5. **Beta Testing**: Deploy to Google Play Console for beta testing

## Support and Troubleshooting

For issues not covered in this guide:
1. Check Android Studio logcat for detailed error messages
2. Review FastAPI backend logs for server-side issues
3. Consult MCP server documentation for integration problems
4. Use Android Device Monitor for system-level debugging

---

**Last Updated**: 2025-11-14
**Version**: 1.0
**Tested With**: Android Studio 2023.3.1, Android API 34