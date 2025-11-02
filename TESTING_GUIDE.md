# Testing Guide - Authentication & Recommendations

## ✅ What's Fixed

1. **Authentication** - Login/Signup integrated into main page
2. **Health Conditions** - Form accessible after login
3. **Recommendations** - Shows when logged in with health conditions

## 🧪 Test Flow

### Step 1: Sign Up
1. Visit http://localhost:3000
2. Click "Sign In / Sign Up"
3. Enter email: `test@example.com`
4. Enter password: `test123` (min 6 chars)
5. Click "Sign Up"
6. Check email for confirmation (if email confirmation enabled)
   OR directly sign in with same credentials

### Step 2: Add Health Conditions
1. After login, click "Add Health Conditions"
2. Select "Illness" tab (red button)
3. Choose "fever" from dropdown
4. Select severity (mild/moderate/severe)
5. Click "Add Condition"
6. Click "Save Conditions"
7. You should see "fever" displayed

**OR add "gastrointestinal":**
- Select "Illness" tab
- Choose "gastrointestinal" (you may need to type it if not in list)
- Add and save

### Step 3: Upload Menu Image
1. Upload a menu image file
2. System processes with OCR
3. Backend matches menu items to dishes in database
4. Applies recommendations based on health conditions

### Step 4: View Recommendations
You should see:
- **⚠️ Not Recommended** section (red) - dishes to avoid
- **✅ Recommended** section (green) - safe dishes
- All menu items with indicators

## 🔍 Troubleshooting

### No Recommendations Showing?

1. **Check if logged in:**
   - Should see your email in top bar
   - If not, sign in first

2. **Check health conditions:**
   - Should see "fever" or "gastrointestinal" displayed
   - If not, add them first

3. **Check menu items match:**
   - Recommendations only show if menu items match dish names in database
   - Sample dishes: "Grilled Chicken", "Caesar Salad", "Pasta Carbonara", etc.
   - Try uploading a menu with these dish names

4. **Check browser console:**
   - Open DevTools (F12)
   - Look for errors
   - Check Network tab for API calls

### Login Not Working?

1. **Check Supabase:**
   - Verify Google OAuth is enabled in Supabase
   - Check redirect URL: `http://localhost:3000/auth/callback`

2. **Check environment:**
   - Verify `.env.local` has correct Supabase URL and key
   - Restart frontend: `npm run dev`

3. **Try email/password:**
   - Use email/password signup instead of Google
   - Check Supabase Dashboard → Authentication → Users

### Recommendations Empty?

1. **Verify health conditions in database:**
   ```sql
   SELECT * FROM health_conditions;
   ```

2. **Verify dishes exist:**
   ```sql
   SELECT * FROM dishes;
   ```

3. **Check recommendations table:**
   ```sql
   SELECT * FROM health_dish_recommendations;
   ```

## 🎯 Expected Results

### With Fever Condition:
- ⚠️ **Not Recommended**: Pasta Carbonara, Seafood Stew, Grilled Chicken
- ✅ **Recommended**: Caesar Salad, Onion Soup, Fruit Salad

### With GI Symptoms:
- ⚠️ **Not Recommended**: Pasta Carbonara, Seafood Stew
- ✅ **Recommended**: Caesar Salad, Fruit Salad, Onion Soup

## 📝 Debugging

### Check Backend Logs
```bash
tail -f /tmp/backend_new.log
```

### Check Frontend Logs
```bash
tail -f /tmp/frontend_new.log
```

### Test API Directly
```bash
# Get dishes
curl http://localhost:8000/api/v1/dishes/

# Check if user is authenticated (after login)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/auth/user
```

## ✅ Success Indicators

- ✅ Can sign up/login
- ✅ Health conditions saved
- ✅ Menu uploaded successfully
- ✅ Recommendations sections appear
- ✅ Dishes marked with ⚠️ or ✅

