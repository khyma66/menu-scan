# Frontend URLs

## 🚀 Development URL

**Local Development:**
```
http://localhost:3000
```

To start the frontend:
```bash
cd menu-ocr-frontend
npm run dev
```

Then open: http://localhost:3000

## 🌐 Production URLs

### After Deployment to Vercel
Your production URL will be:
```
https://your-app-name.vercel.app
```

Or your custom domain if configured.

### After Deployment to Render
If deployed as static site:
```
https://your-app-name.onrender.com
```

## 🔗 Backend API URL

The frontend connects to the backend at:
- **Local:** `http://localhost:8000`
- **Production:** Set via `NEXT_PUBLIC_API_URL` environment variable

## 📝 Environment Setup

Make sure `.env.local` is configured:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

## 🎯 Quick Start

```bash
# Terminal 1: Start Backend
cd fastapi-menu-service
source venv/bin/activate
uvicorn app.main:app --reload
# Backend runs at: http://localhost:8000

# Terminal 2: Start Frontend
cd menu-ocr-frontend
npm run dev
# Frontend runs at: http://localhost:3000
```

Then visit: **http://localhost:3000**

