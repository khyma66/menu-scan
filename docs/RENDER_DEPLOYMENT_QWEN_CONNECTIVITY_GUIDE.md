# Render Deployment & Qwen Connectivity Guide

**Date:** November 23, 2025  
**Purpose:** Deploy to Render with OpenRouter Qwen connectivity and test end-to-end

---

## 🚀 STEP 1: Deploy to Render

### Prerequisites
- GitHub repository with your code
- Render account (free tier available)

### Deployment Instructions

#### 1. **Connect Repository to Render**
1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select the `fastapi-menu-service` directory

#### 2. **Configure Service Settings**
```
Name: menu-ocr-api
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Root Directory: fastapi-menu-service
```

#### 3. **Set Environment Variables** (CRITICAL)
In Render dashboard → Environment section, add:

```env
# Supabase Configuration
SUPABASE_URL=https://jlfqzcaospvspmzbvbxd.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpsZnF6Y2Fvc3B2c3BtemJ2YnhkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTM3MDMzNiwiZXhwIjoyMDc2OTQ2MzM2fQ.5xdkvyJSsza79Iz3kiASMEE22WhNbBktQD6QBb2UgBY
SUPABASE_BUCKET=menu-images

# Qwen Integration via OpenRouter (READY)
OPENROUTER_API_KEY=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

# LLM Configuration
LLM_MODEL=gpt-4o-mini
FALLBACK_ENABLED=true

# Optional: Additional API Keys
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
```

#### 4. **Add Redis Addon**
1. In Render dashboard → "Add-ons"
2. Search "Redis"
3. Add Redis (Starter plan)
4. Environment variables will be auto-populated

#### 5. **Deploy**
1. Click "Create Web Service"
2. Wait for deployment (5-10 minutes)
3. Get your URL: `https://menu-ocr-api.onrender.com`

---

## 🔍 STEP 2: Verify Qwen Connectivity

### Test Health Endpoint
```bash
curl https://your-render-url.onrender.com/health
```

**Expected Response:**
```json
{
    "status": "healthy",
    "environment": "production",
    "version": "1.0.0",
    "timestamp": 1764034567.123,
    "qwen_services": {
        "qwen_vision_api": "available",
        "openrouter_connected": true,
        "api_key_configured": true
    }
}
```

### Test Qwen Vision API
```bash
curl -X POST https://your-render-url.onrender.com/enhanced-ocr/status \
  -H "Content-Type: application/json"
```

---

## 🧪 STEP 3: End-to-End Testing

### 3.1 **Test Local OCR + Qwen Enhancement**
```bash
# Upload a menu image
curl -X POST https://your-render-url.onrender.com/enhanced-ocr/process-upload \
  -F "image=@test-menu.jpg" \
  -F "enhancement_level=high"
```

**Expected Result:**
- Image processed with MLToolkit OCR
- Fallback to Qwen Vision API if needed
- Structured JSON response with menu items
- Processing metadata showing "qwen_vl_max" used

### 3.2 **Test Direct Qwen Vision**
```bash
curl -X POST https://your-render-url.onrender.com/ocr/process-upload \
  -F "image=@test-menu.jpg" \
  -F "use_qwen_vision=true"
```

**Expected Result:**
- Direct Qwen Vision API processing
- High-quality menu extraction
- Restaurant details and structured menu items

### 3.3 **Test Qwen Table Extraction**
```bash
curl -X POST https://your-render-url.onrender.com/table-extraction/extract \
  -H "Content-Type: application/json" \
  -d '{
    "text": "MENU\\nAppetizers\\nGarlic Bread - $5.99\\nCaesar Salad - $8.99\\nMain Courses\\nMargherita Pizza - $16.99\\nChicken Parmesan - $18.99",
    "table_format": "json"
  }'
```

### 3.4 **Test Enhanced OCR Pipeline**
```bash
curl -X POST https://your-render-url.onrender.com/enhanced-ocr/process-menu \
  -F "file=@complex-menu.jpg"
```

**Expected Result:**
- Complete OCR → Qwen → Ingredient matching pipeline
- Enhanced menu analysis with nutritional insights
- Supabase integration working

---

## 📱 STEP 4: Update Mobile Apps

### Android App Configuration
Update API base URL in Android app:

```kotlin
// In ApiService.kt
companion object {
    private const val BASE_URL = "https://your-render-url.onrender.com/"
}
```

### iOS App Configuration  
Update API base URL in iOS app:

```swift
// In ApiService.swift
private let baseURL = "https://your-render-url.onrender.com/"
```

---

## 🔍 STEP 5: Integration Testing

### 5.1 **Test with Real Menu Images**
1. **Simple Menu**: Test basic OCR + Qwen enhancement
2. **Complex Menu**: Test full pipeline with ingredient matching
3. **Multi-language**: Test translation capabilities
4. **Poor Quality**: Test error handling and fallbacks

### 5.2 **Performance Testing**
```bash
# Test response times
time curl -X POST https://your-render-url.onrender.com/enhanced-ocr/process-upload \
  -F "image=@test-menu.jpg"

# Expected: < 15 seconds for Qwen processing
```

### 5.3 **Load Testing**
```bash
# Test multiple concurrent requests
for i in {1..5}; do
  curl -X POST https://your-render-url.onrender.com/enhanced-ocr/process-upload \
    -F "image=@test-menu.jpg" &
done
```

---

## 🎯 STEP 6: Success Criteria

### ✅ Qwen Connectivity Verified
- [ ] Health endpoint responds with Qwen services status
- [ ] OpenRouter API key configured and working
- [ ] Qwen Vision API responds successfully
- [ ] Table extraction using Qwen works
- [ ] Enhanced OCR pipeline operational

### ✅ End-to-End Flow Working
- [ ] Image upload → OCR → Qwen processing → JSON response
- [ ] Mobile apps can connect to Render service
- [ ] Supabase integration functional
- [ ] Error handling and fallbacks working

### ✅ Performance Metrics
- [ ] OCR processing: < 5 seconds
- [ ] Qwen processing: < 15 seconds
- [ ] Health check: < 1 second
- [ ] API uptime: > 99%

---

## 🚨 Troubleshooting

### Common Issues

#### 1. **"Qwen API key not configured"**
- Check OPENROUTER_API_KEY environment variable
- Verify API key is valid at openrouter.ai

#### 2. **"OpenRouter API request failed"**
- Check API key permissions
- Verify free tier usage limits
- Check network connectivity

#### 3. **"Service not responding"**
- Check Render service logs
- Verify all environment variables set
- Check Redis addon connection

#### 4. **"Database connection failed"**
- Verify SUPABASE_URL and SUPABASE_KEY
- Check Supabase project status
- Verify RLS policies

### Debug Commands
```bash
# Check service status
curl https://your-render-url.onrender.com/health

# Check Qwen connectivity
curl https://your-render-url.onrender.com/enhanced-ocr/status

# View service logs (in Render dashboard)
# Check Environment Variables section
```

---

## 📊 Monitoring & Maintenance

### Key Metrics to Monitor
1. **Qwen API Usage**: Track requests and costs
2. **Response Times**: Monitor performance
3. **Error Rates**: Watch for API failures
4. **Service Uptime**: Monitor availability

### Cost Optimization
1. **Rate Limiting**: Implement request throttling
2. **Caching**: Use Redis for frequent requests
3. **Model Selection**: Use appropriate Qwen models
4. **Image Optimization**: Compress before processing

---

## 🎉 Success Confirmation

Once deployed and tested, you'll have:

✅ **FastAPI running on Render** with public URL  
✅ **Full Qwen integration** via OpenRouter.ai  
✅ **Supabase database** connected and operational  
✅ **Mobile apps** updated with new API endpoints  
✅ **End-to-end workflow** from image → OCR → Qwen → JSON  

**Your Menu OCR service is now production-ready with AI-powered enhancement!**

---

**Guide Generated:** November 23, 2025  
**Service Status:** Ready for Render deployment with Qwen connectivity  
**Next Action:** Deploy to Render and execute end-to-end testing
