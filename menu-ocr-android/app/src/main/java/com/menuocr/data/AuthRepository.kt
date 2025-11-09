package com.menuocr.data

import io.github.jan.supabase.gotrue.GoTrue
import io.github.jan.supabase.gotrue.gotrue
import io.github.jan.supabase.gotrue.providers.builtin.Email
import io.github.jan.supabase.gotrue.user.UserInfo
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthRepository @Inject constructor(
    private val supabaseClientProvider: SupabaseClientProvider
) {

    private val auth: GoTrue = supabaseClientProvider.client.gotrue

    val currentUser: UserInfo?
        get() = auth.currentUserOrNull

    val isAuthenticated: Boolean
        get() = auth.currentUserOrNull != null

    suspend fun signInWithEmail(email: String, password: String): Result<UserInfo> {
        return try {
            auth.signInWith(Email) {
                this.email = email
                this.password = password
            }
            auth.currentUserOrNull?.let { Result.success(it) } ?: Result.failure(IllegalStateException("User not found after sign in"))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun signUpWithEmail(email: String, password: String): Result<UserInfo> {
        return try {
            auth.signUpWith(Email) {
                this.email = email
                this.password = password
            }
            auth.currentUserOrNull?.let { Result.success(it) } ?: Result.failure(IllegalStateException("User not found after sign up. Email confirmation might be required."))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun signOut(): Result<Unit> {
        return try {
            auth.signOut()
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun resetPassword(email: String): Result<Unit> {
        return try {
            auth.resetPasswordForEmail(email)
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun signInWithGoogle(): Result<UserInfo> {
        return try {
            // Note: Google OAuth requires additional setup in Android
            // This would need Google Sign-In SDK integration
            // For now, return a placeholder error
            Result.failure(NotImplementedError("Google Sign-In requires additional Android setup"))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}