# Quick Start Guide - Menu OCR with Auth

## 🚀 Fast Setup

### 1. Backend Setup (2 minutes)

```bash
cd fastapi-menu-service

# Already have venv? Activate it
source venv/bin/activate

# If not, create one:
# python -m venv venv
# source venv/bin/activate

# Install any missing packages
pip install @supabase/supabase-js  # If not already installed

# Configure environment
cp env.example .env
# Edit .env with your Supabase credentials
```

**Required in `.env`:**
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
```

### 2. Supabase Database Setup (5 minutes)

1. Go to https://supabase.com → Your Project → SQL Editor
2. Copy contents of `supabase_schema.sql`
3. Paste and Run in SQL Editor
4. Go to Authentication → Providers → Enable Google
5. Add redirect URL: `http://localhost:3000/auth/callback`

### 3. Frontend Setup (2 minutes)

```bash
cd menu-ocr-frontend

# Install Supabase packages
npm install @supabase/supabase-js @supabase/auth-helpers-nextjs

# Create environment file
cat > .env.local << EOF
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF

# Start dev server
npm run dev
```

### 4. Test the Flow

1. **Sign Up:**
   - Visit http://localhost:3000
   - Click "Sign in with Google"
   - Complete OAuth flow

2. **Add Health Conditions:**
   - After signup, add allergies/illnesses
   - Example: "allergy: peanut", "illness: cough"

3. **Process Menu:**
   - Upload menu image URL
   - Get filtered results based on your conditions

## 🧪 Quick API Test

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test OCR (without auth - works!)
curl -X POST http://localhost:8000/api/v1/ocr/process \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/menu.jpg",
    "use_llm_enhancement": false
  }'
```

## ✅ Checklist

- [ ] Supabase project created
- [ ] Database schema run (supabase_schema.sql)
- [ ] Google OAuth enabled in Supabase
- [ ] Backend .env configured
- [ ] Frontend .env.local configured
- [ ] Backend running (port 8000)
- [ ] Frontend running (port 3000)
- [ ] Test signup works
- [ ] Test health conditions form
- [ ] Test menu OCR with filtering

## 🐛 Troubleshooting

**"Supabase client not initialized"**
- Check SUPABASE_URL and SUPABASE_KEY in .env

**"No such table: users"**
- Run supabase_schema.sql in Supabase SQL Editor

**"Google OAuth error"**
- Check redirect URL matches in Supabase settings
- Use exact URL: `http://localhost:3000/auth/callback`

**Frontend can't connect to backend**
- Check NEXT_PUBLIC_API_URL in .env.local
- Ensure backend is running on port 8000

## 📚 Next Steps

1. Deploy backend to Render
2. Deploy frontend to Vercel
3. Update redirect URLs for production
4. Add more health conditions
5. Customize menu suggestions

