# Supabase Authentication & Health-Based Menu Suggestions

## ✅ Features Added

### 1. Authentication (Google Sign-up)
- **Location**: `fastapi-menu-service/app/services/auth_service.py`
- **Router**: `fastapi-menu-service/app/routers/auth.py`
- **Frontend**: `menu-ocr-frontend/components/AuthForm.tsx`

**Features:**
- ✅ Google OAuth integration
- ✅ Email/password authentication
- ✅ User profile management
- ✅ JWT token verification

### 2. Health Conditions Tracking
- **Location**: `fastapi-menu-service/app/services/health_service.py`
- **Database Schema**: `fastapi-menu-service/supabase_schema.sql`

**Features:**
- ✅ Track allergies, illnesses, dietary restrictions
- ✅ Add/remove health conditions
- ✅ Severity levels for illnesses

### 3. Smart Menu Suggestions
- **Location**: `fastapi-menu-service/app/services/health_service.py`
- **Integration**: Updated OCR router to filter menu items

**Features:**
- ✅ Filter menu items based on allergies
- ✅ Recommend foods for illnesses (e.g., warm soups for cough/flu)
- ✅ Dietary restrictions (vegetarian, vegan, keto, etc.)
- ✅ Highlight items to avoid vs. recommend

## 🗄️ Database Schema

Run the SQL in `fastapi-menu-service/supabase_schema.sql` in your Supabase SQL editor:

```bash
# Tables created:
- users (extends auth.users)
- health_conditions
- menu_suggestions (pre-populated with common conditions)
- ocr_results

# RLS Policies:
- Users can only see their own data
- Users can manage their own health conditions
```

## 🚀 Setup Steps

### 1. Set Up Supabase Authentication

Go to your Supabase project:
- **Authentication** → **Providers** → **Google**
- Enable Google provider
- Add credentials
- Set redirect URL to: `http://localhost:3000/auth/callback` (dev)
  or `https://your-domain.com/auth/callback` (prod)

### 2. Run Database Schema

In Supabase SQL Editor, run:
```sql
-- Copy content from fastapi-menu-service/supabase_schema.sql
```

### 3. Update Environment Variables

Backend (`.env`):
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-service-role-key
```

Frontend (`.env.local`):
```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```

### 4. Install Frontend Dependencies

```bash
cd menu-ocr-frontend
npm install @supabase/supabase-js @supabase/auth-helpers-nextjs
```

## 📝 API Endpoints

### Authentication Endpoints

#### Get User Profile
```http
GET /api/v1/auth/user
Authorization: Bearer <token>
```

#### Update Profile
```http
POST /api/v1/auth/profile
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "user@example.com",
  "full_name": "John Doe",
  "phone": "+1234567890"
}
```

#### Get Health Conditions
```http
GET /api/v1/auth/health-conditions
Authorization: Bearer <token>
```

#### Add Health Condition
```http
POST /api/v1/auth/health-conditions
Authorization: Bearer <token>
Content-Type: application/json

{
  "condition_type": "allergy",
  "condition_name": "peanut",
  "severity": "severe"
}
```

#### Remove Health Condition
```http
DELETE /api/v1/auth/health-conditions/{condition_id}
Authorization: Bearer <token>
```

### OCR Endpoint (Updated)

Now supports optional filtering based on user's health conditions:

```http
POST /api/v1/ocr/process
Authorization: Bearer <token>  # Optional
Content-Type: application/json

{
  "image_url": "https://example.com/menu.jpg",
  "use_llm_enhancement": true,
  "language": "en"
}
```

**Response** (when authenticated):
```json
{
  "success": true,
  "menu_items": [...],  // Filtered items
  "metadata": {
    "original_count": 20,
    "filtered_count": 15,
    "items_to_avoid": [...],
    "conditions": [...]
  }
}
```

## 🎯 How It Works

### 1. User Signs Up
```
1. User clicks "Sign in with Google"
2. Redirected to Google OAuth
3. Returns to app with JWT token
4. Profile created in Supabase
```

### 2. User Adds Health Conditions
```
1. User fills health condition form
2. Conditions saved to database
3. Examples: "allergy: peanut", "illness: cough", "dietary: vegan"
```

### 3. Menu Processing
```
1. User uploads menu image
2. OCR extracts items
3. Backend checks user's health conditions
4. Filters items based on allergies/restrictions
5. Recommends appropriate items (e.g., warm soups for cough)
```

### 4. Filtering Logic

**Avoid Items:**
- Contains allergen keywords
- Contains restricted dietary keywords

**Recommend Items:**
- Matches illness recommendations (e.g., "soup" for cough)
- Aligns with dietary preferences

**Caution Items:**
- May cause issues but not explicitly forbidden

## 📊 Pre-populated Menu Suggestions

Common conditions with automatic filtering:

**Allergies:**
- Peanut → Avoid dishes with "peanut", "satay", "thai"
- Shellfish → Avoid "shrimp", "crab", "lobster"
- Dairy → Avoid "cheese", "butter", "cream"
- Nuts → Avoid "almond", "cashew", "pesto"

**Illnesses:**
- Cough/Cold → Recommend "soup", "warm", "ginger"
- Flu → Recommend "chicken soup", "comfort food"
- Nausea → Avoid "spicy", "fried", "heavy"

**Dietary:**
- Vegetarian → Avoid all meat
- Vegan → Avoid animal products
- Gluten-free → Avoid wheat, bread, pasta
- Keto → Recommend low-carb options

## 🔧 Frontend Integration

The frontend now includes:

1. **AuthForm.tsx** - Sign in/Sign up with Google
2. **HealthConditionForm.tsx** - Add health conditions
3. Updated OCR to filter based on conditions

Users can:
- Sign up with Google
- Add health conditions during onboarding
- Get filtered menu suggestions automatically

## 🧪 Testing

### Manual Test Flow

1. **Sign Up:**
   ```bash
   # User navigates to sign up page
   # Clicks "Sign in with Google"
   # Completes OAuth flow
   ```

2. **Add Health Conditions:**
   ```bash
   # User fills form
   # Adds: "allergy: peanut", "illness: cough"
   # Submits form
   ```

3. **Process Menu:**
   ```bash
   # Uploads menu image
   # Gets filtered results
   # Sees items to avoid and recommendations
   ```

### API Tests

```bash
# Get user profile
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/auth/user

# Add health condition
curl -X POST http://localhost:8000/api/v1/auth/health-conditions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"condition_type":"allergy","condition_name":"peanut"}'

# Process menu with filtering
curl -X POST http://localhost:8000/api/v1/ocr/process \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"image_url":"https://example.com/menu.jpg"}'
```

## 🚀 Deployment

### Supabase Setup

1. Go to Supabase project
2. Enable Google provider in Authentication
3. Run SQL schema
4. Copy credentials to environment variables

### Render Deployment

Environment variables to add:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
```

### Vercel Deployment (Frontend)

Environment variables:
```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=https://your-api.onrender.com
```

## 📝 Notes

- Authentication is optional - OCR works without login
- Health conditions automatically filter menu items
- Pre-populated suggestions can be customized in database
- All user data is protected by RLS policies

