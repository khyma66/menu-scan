# Render Deployment Fix - Service ID: srv-d45dp8vdiees7387c9bg

## Issues Identified

### 1. Missing Required Environment Variables
- **SUPABASE_SERVICE_ROLE_KEY**: Required for production but missing
- **OPENROUTER_API_KEY**: Referenced in config.py but missing
- **JWT_SECRET_KEY**: Should be set for production security
- **SECRET_KEY**: Should be set for production security

### 2. Configuration Mismatches
- **CORS Origins**: Need to include production domains
- **Trusted Hosts**: Need to include Render's domains
- **Environment**: Set to "production" for production deployment

### 3. Start Command Issues
- **Port Binding**: Must use $PORT variable from Render
- **Module Path**: Correct path is `app.main:app`

## Fixed Configuration

### Updated render.yaml
```yaml
services:
  - type: web
    name: menu-ocr-api
    runtime: python
    region: oregon
    plan: starter
    rootDir: fastapi-menu-service
    buildCommand: cd fastapi-menu-service && pip install -r requirements.txt
    startCommand: cd fastapi-menu-service && uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11
      - key: ENVIRONMENT
        value: production
      - key: DEBUG
        value: false
      - key: API_TITLE
        value: Menu OCR API
      - key: API_VERSION
        value: 1.0.0
      - key: LOG_LEVEL
        value: INFO
      - key: SUPABASE_URL
        value: https://jlfqzcaospvspmzbvbxd.supabase.co
      - key: SUPABASE_KEY
        value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpsZnF6Y2Fvc3B2c3BtemJ2YnhkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEzNzAzMzYsImV4cCI6MjA3Njk0NjMzNn0.cTI-Zo2NXeIZQDiQ4mcLia3slwRMyvMLpLj_-4BtviA
      - key: SUPABASE_SERVICE_ROLE_KEY
        value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpsZnF6Y2Fvc3B2c3BtemJ2YnhkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTM3MDMzNiwiZXhwIjoyMDc2OTQ2MzM2fQ.5xdkvyJSsza79Iz3kiASMEE22WhNbBktQD6QBb2UgBY
      - key: SUPABASE_BUCKET
        value: menu-images
      - key: CORS_ORIGINS
        value: '["https://menu-ocr-api.onrender.com", "https://*.onrender.com"]'
      - key: TRUSTED_HOSTS
        value: '["menu-ocr-api.onrender.com", "*.onrender.com", "localhost", "127.0.0.1"]'
      - key: REDIS_HOST
        fromDatabase:
          name: menu-ocr-redis
          property: host
      - key: REDIS_PORT
        fromDatabase:
          name: menu-ocr-redis
          property: port
      - key: REDIS_PASSWORD
        fromDatabase:
          name: menu-ocr-redis
          property: password
      - key: REDIS_DB
        value: 0
      - key: REDIS_TTL
        value: 3600
      - key: JWT_SECRET_KEY
        value: your-super-secret-jwt-key-change-this-in-production
      - key: SECRET_KEY
        value: your-super-secret-key-change-this-in-production
      - key: OPENROUTER_API_KEY
        value: your-openrouter-api-key
      - key: OPENAI_API_KEY
        value: your-openai-api-key
      - key: ANTHROPIC_API_KEY
        value: your-anthropic-api-key

databases:
  - name: menu-ocr-redis
    databaseName: menu-ocr-redis
    user: redis
    plan: starter
```

## Immediate Fix Steps

### Step 1: Update Render Service Settings

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Select your service**: menu-ocr-api (srv-d45dp8vdiees7387c9bg)
3. **Navigate to Environment tab**

### Step 2: Add Missing Environment Variables

Add these critical variables:

```
ENVIRONMENT=production
DEBUG=false
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpsZnF6Y2Fvc3B2c3BtemJ2YnhkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTM3MDMzNiwiZXhwIjoyMDc2OTQ2MzM2fQ.5xdkvyJSsza79Iz3kiASMEE22WhNbBktQD6QBb2UgBY
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
SECRET_KEY=your-super-secret-key-change-this-in-production
OPENROUTER_API_KEY=your-openrouter-api-key
```

### Step 3: Update Build and Start Commands

**Build Command:**
```bash
cd fastapi-menu-service && pip install -r requirements.txt
```

**Start Command:**
```bash
cd fastapi-menu-service && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Step 4: Root Directory Configuration
Set **Root Directory** to: `fastapi-menu-service`

### Step 5: Deploy
Click "Manual Deploy" → "Deploy latest commit"

## Troubleshooting Common Issues

### Issue 1: Module Not Found
**Error**: `Module 'app.main' not found`
**Solution**: Ensure Root Directory is set to `fastapi-menu-service`

### Issue 2: Port Binding Error
**Error**: `Address already in use`
**Solution**: Use `--port $PORT` in start command

### Issue 3: Environment Variable Missing
**Error**: `Missing required environment variables`
**Solution**: Add all required vars listed above

### Issue 4: CORS Error
**Error**: `CORS policy blocked request`
**Solution**: Update CORS_ORIGINS to include production domains

### Issue 5: Database Connection Error
**Error**: `Cannot connect to Redis`
**Solution**: Ensure Redis addon is attached and environment variables are set

## Verification Steps

After fixing, verify deployment:

1. **Health Check**: https://menu-ocr-api.onrender.com/health
2. **API Docs**: https://menu-ocr-api.onrender.com/docs
3. **Test Endpoint**: https://menu-ocr-api.onrender.com/

Expected response from health:
```json
{
  "status": "healthy",
  "environment": "production", 
  "version": "1.0.0",
  "timestamp": 1731999999.123
}
```

## Quick Fix Commands

If you want to apply this immediately via Render CLI:

```bash
# Update environment variables
render env set ENVIRONMENT=production DEBUG=false
render env set SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
render env set JWT_SECRET_KEY="your-super-secret-jwt-key"
render env set SECRET_KEY="your-super-secret-key"
render env set OPENROUTER_API_KEY="your-openrouter-api-key"

# Manual deploy
render deploy
```

## Status Check

After applying fixes, your service should show:
- **Status**: Active
- **Region**: Oregon (US West)
- **Runtime**: Python 3.11
- **Health**: Green checkmark
- **URL**: https://menu-ocr-api.onrender.com