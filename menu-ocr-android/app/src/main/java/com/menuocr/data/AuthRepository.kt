package com.menuocr.data

import io.github.jan.supabase.auth.Auth
import io.github.jan.supabase.auth.providers.Google
import io.github.jan.supabase.auth.providers.builtin.Email
import io.github.jan.supabase.auth.user.UserInfo
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthRepository @Inject constructor(
    private val supabaseClientProvider: SupabaseClientProvider
) {

    private val auth = supabaseClientProvider.client.auth

    val currentUser: UserInfo?
        get() = auth.currentUserOrNull()

    val isAuthenticated: Boolean
        get() = auth.currentUserOrNull() != null

    suspend fun signInWithEmail(email: String, password: String): Result<UserInfo> {
        return try {
            val result = auth.signInWith(Email) {
                this.email = email
                this.password = password
            }
            Result.success(result)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun signUpWithEmail(email: String, password: String): Result<UserInfo> {
        return try {
            val result = auth.signUpWith(Email) {
                this.email = email
                this.password = password
            }
            Result.success(result)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun signInWithGoogle(): Flow<Result<UserInfo>> = flow {
        try {
            val result = auth.signInWith(Google)
            emit(Result.success(result))
        } catch (e: Exception) {
            emit(Result.failure(e))
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
}