# Fix Login "Invalid Credentials" Issue

## Common Causes

### 1. Email Confirmation Required
Supabase may require users to confirm their email before they can sign in.

**Solution:**
- Option A: Disable email confirmation in Supabase Dashboard
  - Go to: Authentication → Settings
  - Uncheck "Enable email confirmations"
  - Save

- Option B: Check email and confirm account
  - Look for confirmation email from Supabase
  - Click confirmation link
  - Then try signing in

### 2. Need to Sign Up First
Make sure you've signed up before trying to sign in.

**Steps:**
1. Click "Sign Up" tab
2. Enter email and password
3. Click "Sign Up"
4. Then try "Sign In"

### 3. Password Requirements
- Minimum 6 characters
- Try: `test123` or `password123`

## Quick Test

1. **Disable Email Confirmation** (Recommended for testing):
   - Supabase Dashboard → Authentication → Settings
   - Disable "Enable email confirmations"

2. **Test Sign Up:**
   ```
   Email: test@example.com
   Password: test123
   ```

3. **Test Sign In:**
   ```
   Email: test@example.com
   Password: test123
   ```

## Verify in Supabase

Check if user was created:
1. Go to Supabase Dashboard
2. Authentication → Users
3. Look for your email
4. Check status (should be "Active")

## Alternative: Test with Existing User

If you already have a user:
1. Go to Supabase Dashboard → Authentication → Users
2. Click on user
3. Reset password or check status
4. Try signing in again

## Google OAuth (Alternative)

If email/password doesn't work:
1. Click "Continue with Google"
2. Complete Google OAuth flow
3. Automatically logged in

