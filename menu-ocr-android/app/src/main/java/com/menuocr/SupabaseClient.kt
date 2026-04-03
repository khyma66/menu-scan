package com.menuocr

import android.content.SharedPreferences
import android.util.Log
import java.net.URLEncoder
import io.github.jan.supabase.createSupabaseClient
import io.github.jan.supabase.gotrue.Auth
import io.github.jan.supabase.gotrue.OtpType
import io.github.jan.supabase.gotrue.auth
import io.github.jan.supabase.gotrue.providers.builtin.Email
import io.github.jan.supabase.gotrue.user.UserSession
import io.github.jan.supabase.storage.Storage

/**
 * Supabase client service for authentication and database operations
 */
object SupabaseClient {
    const val TAG = "SupabaseClient"

    private val AUTH_RETRY_CONFIG = RetryConfig(
        enabled = true,
        delaySeconds = 1,
        maxAttempts = 2,
        backoffMultiplier = 1.0f
    )
    
    val client = createSupabaseClient(
        supabaseUrl = AppConfig.Supabase.URL,
        supabaseKey = AppConfig.Supabase.ANON_KEY
    ) {
        install(Auth)
        install(Storage)
    }
    
    /**
     * Sign up a new user with email and password.
     *
     * Supabase will send a confirmation email containing a 6-digit OTP code.
     * The OTP is enabled in the Supabase Dashboard:
     *   Authentication → Settings → "Use OTP for email confirmations" = ON
     *
     * The redirectUrl is set so that the magic-link version (if OTP is not enabled) 
     * also redirects back into the app instead of opening a browser page.
     */
    suspend fun signUp(email: String, password: String): Result<Unit> {
        return try {
            RetryHelper.retry(AUTH_RETRY_CONFIG) {
                client.auth.signUpWith(Email) {
                    this.email = email
                    this.password = password
                }
                Log.i(TAG, "Sign-up initiated, OTP/confirmation email sent to: $email")
                Result.success(Unit)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Sign up failed: ${e.message}", e)
            Result.failure(e)
        }
    }

    /**
     * Verify the 6-digit OTP code sent to the user's email at sign-up.
     * Call this after [signUp] when the user has entered the code shown
     * in the Fooder confirmation email.
     */
    suspend fun verifyEmailOtp(email: String, otpCode: String): Result<Unit> {
        return try {
            client.auth.verifyEmailOtp(
                type = OtpType.Email.SIGNUP,
                email = email,
                token = otpCode.trim()
            )
            Log.i(TAG, "Email OTP verified for: $email")
            Result.success(Unit)
        } catch (e: Exception) {
            Log.e(TAG, "OTP verification failed: ${e.message}", e)
            Result.failure(e)
        }
    }
    
    /**
     * Sign in an existing user with email and password
     */
    suspend fun signIn(email: String, password: String): Result<Unit> {
        return try {
            RetryHelper.retry(AUTH_RETRY_CONFIG) {
                client.auth.signInWith(Email) {
                    this.email = email
                    this.password = password
                }
                Log.i(TAG, "User signed in successfully: $email")
                Result.success(Unit)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Sign in failed: ${e.message}", e)
            Result.failure(e)
        }
    }
    
    /**
     * Sign out the current user
     */
    suspend fun signOut(): Result<Unit> {
        return try {
            RetryHelper.retry(AUTH_RETRY_CONFIG) {
                client.auth.signOut()
                Log.i(TAG, "User signed out successfully")
                Result.success(Unit)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Sign out failed: ${e.message}", e)
            Result.failure(e)
        }
    }
    
    /**
     * Send password reset email
     */
    suspend fun resetPassword(email: String): Result<Unit> {
        return try {
            RetryHelper.retry(AUTH_RETRY_CONFIG) {
                client.auth.resetPasswordForEmail(
                    email = email,
                )
                Log.i(TAG, "Password reset email sent to: $email")
                Result.success(Unit)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Password reset failed: ${e.message}", e)
            Result.failure(e)
        }
    }
    
    /**
     * Build Google OAuth URL directly against Supabase.
     * Going through the web proxy requires the frontend to be deployed;
     * direct Supabase OAuth avoids the 401 / 404 from an undeployed proxy.
     */
    fun getGoogleOAuthUrl(): String {
        val redirect = URLEncoder.encode(AppConfig.Supabase.AUTH_REDIRECT_URL, "UTF-8")
        return "${AppConfig.Supabase.URL}/auth/v1/authorize?provider=google&redirect_to=$redirect"
    }

    /**
     * Build Apple OAuth URL directly against Supabase.
     */
    fun getAppleOAuthUrl(): String {
        val redirect = URLEncoder.encode(AppConfig.Supabase.AUTH_REDIRECT_URL, "UTF-8")
        return "${AppConfig.Supabase.URL}/auth/v1/authorize?provider=apple&scopes=name%20email&redirect_to=$redirect"
    }

    /**
     * Handle the OAuth callback redirect URI.
     * Supabase can return tokens in either the URI fragment (#access_token=...)
     * or as query params (?access_token=...) depending on the provider/version.
     * We check both.
     */
    suspend fun handleOAuthCallback(uri: android.net.Uri): Result<Unit> {
        return try {
            // Try fragment first (#access_token=...) then query params (?access_token=...)
            val rawFragment = uri.encodedFragment
            val rawQuery = uri.encodedQuery

            val paramSource = when {
                !rawFragment.isNullOrBlank() -> rawFragment
                !rawQuery.isNullOrBlank() -> rawQuery
                else -> return Result.failure(Exception("No authentication data in callback URL"))
            }

            val params = paramSource.split("&").associate {
                val parts = it.split("=", limit = 2)
                parts[0] to (if (parts.size > 1) java.net.URLDecoder.decode(parts[1], "UTF-8") else "")
            }

            val accessToken = params["access_token"]
            val refreshToken = params["refresh_token"]

            if (accessToken.isNullOrBlank()) {
                return Result.failure(Exception("No access token in callback"))
            }
            if (refreshToken.isNullOrBlank()) {
                return Result.failure(Exception("No refresh token in callback"))
            }

            val expiresIn = params["expires_in"]?.toLongOrNull() ?: 3600
            val tokenType = params["token_type"] ?: "bearer"

            // Fetch user BEFORE importSession so the session object contains a
            // populated user — this makes currentUserOrNull() return non-null
            // immediately after importSession, without needing a second call.
            val userInfo = try {
                client.auth.retrieveUser(accessToken).also {
                    Log.i(TAG, "User fetched during OAuth callback: ${it.email}")
                }
            } catch (e: Exception) {
                Log.w(TAG, "Could not prefetch user during OAuth callback: ${e.message}")
                null
            }

            val session = UserSession(
                accessToken = accessToken,
                refreshToken = refreshToken,
                expiresIn = expiresIn,
                tokenType = tokenType,
                user = userInfo   // populated — currentUserOrNull() returns non-null
            )
            client.auth.importSession(session)
            Log.i(TAG, "OAuth session imported with user=${userInfo?.email}")
            Result.success(Unit)
        } catch (e: Exception) {
            Log.e(TAG, "OAuth callback handling failed: ${e.message}", e)
            Result.failure(e)
        }
    }
    
    /**
     * Get the current user's session
     */
    suspend fun getCurrentSession() = client.auth.currentSessionOrNull()
    
    /**
     * Get the current user.
     * Falls back to a network user-fetch when the local session was imported without user
     * data (e.g., immediately after OAuth callback). This ensures profile screens always
     * have a populated user object.
     */
    suspend fun getCurrentUser(): io.github.jan.supabase.gotrue.user.UserInfo? {
        val cached = client.auth.currentUserOrNull()
        if (cached != null) return cached
        val accessToken = client.auth.currentSessionOrNull()?.accessToken ?: return null
        return try {
            client.auth.retrieveUser(accessToken)
        } catch (e: Exception) {
            Log.w(TAG, "retrieveUser fallback failed: ${e.message}")
            null
        }
    }
    
    /**
     * Check if user is authenticated
     */
    suspend fun isAuthenticated(): Boolean {
        return getCurrentSession() != null
    }

    // ── Session persistence (SharedPreferences) ────────────────────────────────
    // Keeps the user logged in across app restarts without a remote DB lookup on
    // every cold start. Access token is validated lazily on first authenticated
    // request; if expired, Supabase auto-refreshes using the refresh token.

    /** Save current session tokens to SharedPreferences. Call after successful sign-in. */
    fun saveSession(prefs: SharedPreferences) {
        val session = client.auth.currentSessionOrNull() ?: return
        prefs.edit()
            .putString("access_token",  session.accessToken)
            .putString("refresh_token", session.refreshToken)
            .apply()
        Log.i(TAG, "Session saved to preferences")
    }

    /**
     * Restore a previously saved session.
     * Validates the access token with Supabase; clears stored tokens if invalid.
     * @return true if session was restored successfully, false otherwise.
     */
    suspend fun restoreSession(prefs: SharedPreferences): Boolean {
        val at = prefs.getString("access_token",  null) ?: return false
        val rt = prefs.getString("refresh_token", null) ?: return false
        return try {
            val userInfo = client.auth.retrieveUser(at)
            val session  = UserSession(
                accessToken  = at,
                refreshToken = rt,
                expiresIn    = 3600L,
                tokenType    = "bearer",
                user         = userInfo
            )
            // importSession() can internally start a token-refresh network call.
            // If that refresh fails it may throw AFTER the session is already
            // written into the Supabase client's in-memory state.  We must
            // sign-out to evict that partial session, otherwise callers that
            // check isAuthenticated() will see the stale (expired) session and
            // be silently auto-navigated past the login screen.
            try {
                client.auth.importSession(session)
            } catch (importEx: Exception) {
                Log.w(TAG, "importSession failed (evicting stale session): ${importEx.message}")
                try { client.auth.signOut() } catch (_: Exception) {}
                prefs.edit().remove("access_token").remove("refresh_token").apply()
                return false
            }
            Log.i(TAG, "Session restored for ${userInfo.email}")
            true
        } catch (e: Exception) {
            val msg = e.message ?: ""
            // Network errors (timeout, no connectivity) should NOT delete the saved
            // tokens — they may still be valid once the device is back online.
            // Only clear tokens on auth failures (HTTP 401/403, invalid JWT, etc.).
            val isNetworkError = e is java.net.UnknownHostException
                    || e is java.net.SocketTimeoutException
                    || e is java.io.IOException
                    || msg.contains("timeout", ignoreCase = true)
                    || msg.contains("Unable to resolve host", ignoreCase = true)
                    || msg.contains("NetworkException", ignoreCase = true)
            if (isNetworkError) {
                Log.w(TAG, "Session restore skipped — network unavailable; tokens preserved: ${e.message}")
            } else {
                Log.w(TAG, "Session restore failed (auth error, clearing tokens): ${e.message}")
                prefs.edit().remove("access_token").remove("refresh_token").apply()
            }
            false
        }
    }

    /** Clear persisted session tokens (call on sign-out). */
    fun clearSession(prefs: SharedPreferences) {
        prefs.edit().remove("access_token").remove("refresh_token").apply()
        Log.i(TAG, "Saved session cleared")
    }
    
    /**
     * Get access token for API calls
     */
    suspend fun getAccessToken(): String? {
        return getCurrentSession()?.accessToken
    }
    
}
