# Render Deployment Instructions

Since Render is upgraded with a paid plan, follow these steps to deploy the Menu OCR backend:

## 1. Automatic Deployment (Recommended)
Since the code is pushed to GitHub, Render should automatically deploy if:
- Render is connected to the GitHub repository
- Auto-deploy is enabled

Check Render dashboard at: https://dashboard.render.com

## 2. Manual Deployment Steps

### Step 1: Go to Render Dashboard
Visit: https://dashboard.render.com

### Step 2: Create New Web Service
- Click "New +" → "Web Service"
- Connect your GitHub repository: `mohan6695/menu-ocr`
- Select the `main` branch

### Step 3: Configure Service
**Service Name:** `menu-ocr-api`
**Runtime:** Python 3
**Region:** Oregon (US West)
**Branch:** main
**Root Directory:** `fastapi-menu-service`

### Step 4: Build and Deploy Commands
**Build Command:** `pip install -r requirements.txt`
**Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Step 5: Environment Variables
Copy and paste these from `render-env.txt`:

```
SUPABASE_URL=https://jlfqzcaospvspmzbvbxd.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpsZnF6Y2Fvc3B2c3BtemJ2YnhkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTM3MDMzNiwiZXhwIjoyMDc2OTQ2MzM2fQ.5xdkvyJSsza79Iz3kiASMEE22WhNbBktQD6QBb2UgBY
SUPABASE_BUCKET=menu-images
LLM_MODEL=gpt-4o-mini
FALLBACK_ENABLED=true
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
PYTHON_VERSION=3.11
API_TITLE=Menu OCR API
API_VERSION=1.0.0
API_PREFIX=/api/v1
DEBUG=false
```

### Step 6: Click "Create Web Service"
Wait for deployment to complete (2-5 minutes).

## 3. Get Deployment URL
After successful deployment, your API will be available at:
`https://menu-ocr-api.onrender.com`

Test it: https://menu-ocr-api.onrender.com/health

## 4. Update Android App
Replace the API base URL in Android app configuration to use the Render deployment URL.

## Status Check
- ✅ Code pushed to GitHub
- ✅ Render configuration files ready
- ⏳ Waiting for Render deployment