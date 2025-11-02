# Run SQL Schemas in Supabase Web Interface

## 📋 Steps to Run in Supabase Web Dashboard

### Step 1: Open SQL Editor
1. Go to: https://supabase.com/dashboard/project/jlfqzcaospvspmzbvbxd
2. Click **SQL Editor** in the left sidebar
3. Click **New Query**

### Step 2: Run Main Schema
1. Copy the contents of `fastapi-menu-service/supabase_schema.sql`
2. Paste into the SQL Editor
3. Click **Run** (or press Cmd/Ctrl + Enter)
4. Wait for "Success" message

### Step 3: Run Dishes Schema
1. Click **New Query** again
2. Copy the contents of `fastapi-menu-service/supabase_dishes_schema.sql`
3. Paste into the SQL Editor
4. Click **Run**
5. Wait for "Success" message

## ✅ Verification

After running, check tables exist:
- Go to **Table Editor** in Supabase
- You should see:
  - `users`
  - `health_conditions`
  - `dishes`
  - `ingredients`
  - `dish_ingredients`
  - `health_dish_recommendations`
  - `ocr_results`

## 🔗 Direct Links

- **SQL Editor**: https://supabase.com/dashboard/project/jlfqzcaospvspmzbvbxd/sql/new
- **Table Editor**: https://supabase.com/dashboard/project/jlfqzcaospvspmzbvbxd/editor

## 📝 Quick Copy Commands

For easy copying, you can also use:

```bash
# Copy schema to clipboard (macOS)
cat fastapi-menu-service/supabase_schema.sql | pbcopy

# Then paste in Supabase SQL Editor
```

