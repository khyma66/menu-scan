# Menu OCR - Deployment Guide

## ✅ What Was Built

### 1. Backend (FastAPI)
- **Location**: `fastapi-menu-service/`
- **Framework**: FastAPI with Python 3.13
- **Features**:
  - OCR processing with Tesseract
  - Redis caching
  - Supabase integration
  - LLM enhancement (OpenAI/Anthropic)
  - Health monitoring
  - Docker support

### 2. Frontend (Next.js)
- **Location**: `menu-ocr-frontend/`
- **Framework**: Next.js 15 with React 19
- **Features**:
  - Image upload via URL
  - Real-time processing status
  - Beautiful UI with Tailwind CSS
  - TypeScript for type safety
  - Responsive design

### 3. Tests
- **Location**: `fastapi-menu-service/tests/`
- **Status**: ✅ 11 tests passing, 1 skipped
- **Coverage**: Endpoints, configuration, OCR parsing

### 4. Deployment Configuration
- **Render**: `render.yaml`, `.render.yaml`
- **Docker**: `Dockerfile` ready
- **Scripts**: `setup.sh`, `render-deploy.sh`

---

## 🚀 Deployment Steps

### Backend Deployment to Render

1. **Prepare Repository**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push
   ```

2. **Connect to Render**
   - Go to https://dashboard.render.com
   - New → Web Service
   - Connect your GitHub repository
   - Select `fastapi-menu-service` directory

3. **Configure Environment Variables**
   ```bash
   # Required
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-supabase-anon-key
   SUPABASE_BUCKET=menu-images
   
   # Optional
   OPENAI_API_KEY=your-openai-key
   ANTHROPIC_API_KEY=your-anthropic-key
   LLM_MODEL=gpt-4o-mini
   FALLBACK_ENABLED=true
   
   # Redis (will be auto-configured)
   REDIS_HOST=<from-redis-addon>
   REDIS_PORT=<from-redis-addon>
   REDIS_PASSWORD=<from-redis-addon>
   ```

4. **Add Redis Database**
   - In Render dashboard → New → Redis
   - Choose "Starter" plan
   - Render will auto-link credentials

5. **Deploy**
   - Render will auto-build and deploy
   - URL will be: `https://menu-ocr-api.onrender.com`

---

### Frontend Deployment

#### Option 1: Vercel (Recommended)

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Deploy**
   ```bash
   cd menu-ocr-frontend
   vercel
   ```

3. **Configure Environment**
   - Set `NEXT_PUBLIC_API_URL` to your Render backend URL
   - Example: `https://menu-ocr-api.onrender.com`

#### Option 2: Render

1. **Create New Static Site**
   - In Render dashboard → New → Static Site
   - Connect your repository
   - Root directory: `menu-ocr-frontend`

2. **Build Settings**
   ```bash
   Build Command: npm install && npm run build
   Publish Directory: .next
   ```

3. **Environment Variables**
   ```
   NEXT_PUBLIC_API_URL=https://menu-ocr-api.onrender.com
   ```

---

## 🧪 Testing

### Run Backend Tests
```bash
cd fastapi-menu-service
source venv/bin/activate
pytest tests/ -v
```

### Test Backend Locally
```bash
cd fastapi-menu-service
source venv/bin/activate
uvicorn app.main:app --reload
# Visit http://localhost:8000/docs
```

### Test Frontend Locally
```bash
cd menu-ocr-frontend
npm run dev
# Visit http://localhost:3000
```

---

## 📁 Project Structure

```
menu-ocr/
├── fastapi-menu-service/       # Backend API
│   ├── app/
│   │   ├── main.py            # FastAPI app
│   │   ├── config.py          # Settings
│   │   ├── models.py          # Pydantic models
│   │   ├── routers/
│   │   │   └── ocr.py         # OCR endpoint
│   │   ├── services/
│   │   │   ├── redis_cache.py # Cache service
│   │   │   ├── supabase_client.py # DB client
│   │   │   └── llm_fallback.py # LLM service
│   │   └── utils/
│   │       └── ocr_parser.py  # Text parser
│   ├── tests/                 # Unit tests
│   ├── Dockerfile            # Container
│   ├── render.yaml           # Render config
│   └── requirements.txt      # Python deps
│
├── menu-ocr-frontend/         # Frontend app
│   ├── app/
│   │   └── page.tsx          # Main page
│   ├── components/
│   │   ├── ImageUpload.tsx   # Upload component
│   │   ├── MenuDisplay.tsx   # Results display
│   │   └── StatusDisplay.tsx # Status messages
│   ├── lib/
│   │   └── api.ts            # API client
│   ├── types/
│   │   └── menu.ts           # TypeScript types
│   └── package.json
│
├── README.md                  # Main docs
├── PROJECT_STATUS.md          # Project status
└── DEPLOYMENT.md             # This file
```

---

## 🔧 Environment Setup

### Backend (.env)
```env
# API Configuration
API_TITLE=Menu OCR API
API_VERSION=1.0.0
DEBUG=false

# Server
HOST=0.0.0.0
PORT=8000

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_TTL=3600

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-key
SUPABASE_BUCKET=menu-images

# LLM (Optional)
OPENAI_API_KEY=your-key
ANTHROPIC_API_KEY=your-key
LLM_MODEL=gpt-4o-mini
FALLBACK_ENABLED=true

# OCR
OCR_CONFIDENCE_THRESHOLD=0.7
MAX_IMAGE_SIZE_MB=10
ALLOWED_EXTENSIONS_STR=.jpg,.jpeg,.png,.webp
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
# or for production:
# NEXT_PUBLIC_API_URL=https://menu-ocr-api.onrender.com
```

---

## 🎯 Next Steps

1. **Deploy Backend to Render**
   - Follow steps above
   - Add environment variables
   - Note the deployment URL

2. **Deploy Frontend**
   - Set API URL to backend URL
   - Deploy to Vercel or Render
   - Test the integration

3. **Monitor**
   - Check backend health: `/health`
   - View logs in Render dashboard
   - Test API endpoints in `/docs`

4. **Production Optimizations**
   - Add error tracking (Sentry)
   - Set up CDN for images
   - Enable rate limiting
   - Add authentication

---

## 📊 API Endpoints

### Health Check
```
GET /health
```
Returns service status and dependencies.

### Process Image
```
POST /api/v1/ocr/process
```
Body:
```json
{
  "image_url": "https://example.com/menu.jpg",
  "use_llm_enhancement": true,
  "language": "en"
}
```

Response:
```json
{
  "success": true,
  "menu_items": [...],
  "processing_time_ms": 1234,
  "enhanced": true,
  "cached": false
}
```

---

## 🐛 Troubleshooting

### Backend Issues

**Redis Connection Failed**
- Ensure Redis is running: `docker run -d -p 6379:6379 redis:alpine`
- Check `REDIS_HOST` and `REDIS_PORT` in `.env`

**Supabase Errors**
- Verify `SUPABASE_URL` and `SUPABASE_KEY`
- Check Supabase project is active

**Tesseract Not Found**
- Install: `brew install tesseract` (macOS)
- or `sudo apt-get install tesseract-ocr` (Linux)

### Frontend Issues

**API Connection Failed**
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Ensure backend is running
- Check CORS settings in backend

**Build Errors**
- Run `npm install` again
- Delete `.next` folder and rebuild

---

## 📝 License

MIT License

