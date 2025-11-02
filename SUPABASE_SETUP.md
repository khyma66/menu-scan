# Supabase Project Configuration

## ✅ Project ID Configured

**Project ID:** `jlfqzcaospvspmzbvbxd`

**Supabase URL:** `https://jlfqzcaospvspmzbvbxd.supabase.co`

## 🔧 Setup Steps

### 1. Get Your Supabase Keys

1. Go to: https://supabase.com/dashboard/project/jlfqzcaospvspmzbvbxd
2. Navigate to **Settings** → **API**
3. Copy:
   - **Project URL**: `https://jlfqzcaospvspmzbvbxd.supabase.co`
   - **anon/public key**: Your public API key
   - **service_role key**: Your service role key (for backend)

### 2. Update Backend Configuration

Edit `fastapi-menu-service/.env`:

```env
SUPABASE_URL=https://jlfqzcaospvspmzbvbxd.supabase.co
SUPABASE_KEY=your-service-role-key-here
SUPABASE_BUCKET=menu-images
```

### 3. Update Frontend Configuration

Edit `menu-ocr-frontend/.env.local`:

```env
NEXT_PUBLIC_SUPABASE_URL=https://jlfqzcaospvspmzbvbxd.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Run Database Schema

1. Go to Supabase Dashboard → **SQL Editor**
2. Run `fastapi-menu-service/supabase_schema.sql` first
3. Then run `fastapi-menu-service/supabase_dishes_schema.sql`

### 5. Enable Google OAuth

1. Go to **Authentication** → **Providers**
2. Enable **Google** provider
3. Set redirect URL:
   - Local: `http://localhost:3000/auth/callback`
   - Production: `https://your-domain.com/auth/callback`

## 🔗 Quick Links

- **Dashboard**: https://supabase.com/dashboard/project/jlfqzcaospvspmzbvbxd
- **API Docs**: https://supabase.com/dashboard/project/jlfqzcaospvspmzbvbxd/api
- **SQL Editor**: https://supabase.com/dashboard/project/jlfqzcaospvspmzbvbxd/sql/new

## 📝 Environment Variables Checklist

### Backend (.env)
- [ ] `SUPABASE_URL=https://jlfqzcaospvspmzbvbxd.supabase.co`
- [ ] `SUPABASE_KEY=<service-role-key>`
- [ ] `SUPABASE_BUCKET=menu-images`

### Frontend (.env.local)
- [ ] `NEXT_PUBLIC_SUPABASE_URL=https://jlfqzcaospvspmzbvbxd.supabase.co`
- [ ] `NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon-key>`
- [ ] `NEXT_PUBLIC_API_URL=http://localhost:8000`

## 🚀 Verification

After setup, verify connection:

```bash
# Test backend connection
cd fastapi-menu-service
source venv/bin/activate
python -c "from app.services.supabase_client import SupabaseClient; s = SupabaseClient(); print('✅ Connected' if s.client else '❌ Not connected')"
```

## 📚 Database Tables

After running schemas, you'll have:
- `users` - User profiles
- `health_conditions` - User health data
- `dishes` - Menu dishes
- `ingredients` - Dish ingredients
- `dish_ingredients` - Dish-ingredient mapping
- `health_dish_recommendations` - Health-based recommendations
- `ocr_results` - OCR processing history

