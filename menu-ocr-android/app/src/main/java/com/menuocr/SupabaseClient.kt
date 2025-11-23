package com.menuocr

import android.util.Log
import io.github.jan.supabase.createSupabaseClient
import io.github.jan.supabase.gotrue.Auth
import io.github.jan.supabase.gotrue.auth
import io.github.jan.supabase.gotrue.providers.builtin.Email
import io.github.jan.supabase.postgrest.Postgrest
import io.github.jan.supabase.postgrest.from
import io.github.jan.supabase.storage.Storage

/**
 * Supabase client service for authentication and database operations
 */
object SupabaseClient {
    const val TAG = "SupabaseClient"
    
    val client = createSupabaseClient(
        supabaseUrl = AppConfig.Supabase.URL,
        supabaseKey = AppConfig.Supabase.ANON_KEY
    ) {
        install(Auth)
        install(Postgrest)
        install(Storage)
    }
    
    /**
     * Sign up a new user with email and password
     */
    suspend fun signUp(email: String, password: String): Result<Unit> {
        return try {
            RetryHelper.retry {
                client.auth.signUpWith(Email) {
                    this.email = email
                    this.password = password
                }
                Log.i(TAG, "User signed up successfully: $email")
                Result.success(Unit)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Sign up failed: ${e.message}", e)
            Result.failure(e)
        }
    }
    
    /**
     * Sign in an existing user with email and password
     */
    suspend fun signIn(email: String, password: String): Result<Unit> {
        return try {
            RetryHelper.retry {
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
            RetryHelper.retry {
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
     * Get the current user's session
     */
    suspend fun getCurrentSession() = client.auth.currentSessionOrNull()
    
    /**
     * Get the current user
     */
    suspend fun getCurrentUser() = client.auth.currentUserOrNull()
    
    /**
     * Check if user is authenticated
     */
    suspend fun isAuthenticated(): Boolean {
        return getCurrentSession() != null
    }
    
    /**
     * Get access token for API calls
     */
    suspend fun getAccessToken(): String? {
        return getCurrentSession()?.accessToken
    }
    
    /**
     * Insert data into a table with retry
     */
    suspend fun insert(
        table: String,
        data: Any
    ): Result<Unit> {
        return try {
            RetryHelper.retry {
                client.from(table).insert(data)
                Log.i(TAG, "Data inserted successfully into $table")
                Result.success(Unit)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Insert failed for table $table: ${e.message}", e)
            Result.failure(e)
        }
    }
    
    /**
     * Query data from a table with retry
     */
    suspend fun selectRaw(
        table: String
    ): Result<String> {
        return try {
            RetryHelper.retry {
                val result = client.from(table).select().data
                Log.i(TAG, "Data selected successfully from $table")
                Result.success(result)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Select failed for table $table: ${e.message}", e)
            Result.failure(e)
        }
    }
    
    /**
     * Update data in a table with retry
     */
    suspend fun update(
        table: String,
        data: Any
    ): Result<Unit> {
        return try {
            RetryHelper.retry {
                client.from(table).update(data)
                Log.i(TAG, "Data updated successfully in $table")
                Result.success(Unit)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Update failed for table $table: ${e.message}", e)
            Result.failure(e)
        }
    }
    
    /**
     * Delete data from a table with retry
     */
    suspend fun delete(
        table: String
    ): Result<Unit> {
        return try {
            RetryHelper.retry {
                client.from(table).delete()
                Log.i(TAG, "Data deleted successfully from $table")
                Result.success(Unit)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Delete failed for table $table: ${e.message}", e)
            Result.failure(e)
        }
    }
}
