package com.menuocr.data

import com.menuocr.FoodPreferenceRequest
import com.menuocr.UserProfileUpdateRequest
import com.menuocr.UserPreferences
import io.github.jan.supabase.postgrest.Postgrest
import io.github.jan.supabase.postgrest.postgrest
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class UserPreferencesRepository @Inject constructor(
    private val supabaseClientProvider: SupabaseClientProvider
) {

    private val postgrest: Postgrest = supabaseClientProvider.client.postgrest

    suspend fun getFoodPreferences(): Result<UserPreferences> {
        return try {
            val result = postgrest.from("user_preferences").select().decodeSingle<UserPreferences>()
            Result.success(result)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun addFoodPreference(preference: FoodPreferenceRequest): Result<Unit> {
        return try {
            postgrest.from("food_preferences").insert(preference)
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /*
    suspend fun updateUserProfile(profile: UserProfileUpdateRequest): Result<Unit> {
        return try {
            // Assuming a table named "user_profiles" and a row with a specific user id
            // This needs to be adapted based on your actual table structure
            // postgrest.from("user_profiles").update(profile) { filter ->
            //     filter.eq("user_id", supabaseClientProvider.client.auth.currentUserOrNull()?.id)
            // }
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    */

    /*
    suspend fun removeFoodPreference(preferenceId: String): Result<Unit> {
        return try {
            // postgrest.from("food_preferences").delete { filter ->
            //     filter.eq("id", preferenceId)
            // }
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    */
}