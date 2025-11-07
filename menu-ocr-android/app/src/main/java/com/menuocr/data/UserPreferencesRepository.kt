package com.menuocr.data

import com.menuocr.FoodPreference
import com.menuocr.UserPreferences
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class UserPreferencesRepository @Inject constructor(
    private val supabaseClientProvider: SupabaseClientProvider
) {

    private val supabase = supabaseClientProvider.client

    suspend fun getUserPreferences(userId: String): UserPreferences {
        // Get food preferences
        val foodPrefsResponse = supabase
            .from("food_preferences")
            .select("*")
            .eq("user_id", userId)
            .execute()

        val foodPreferences = foodPrefsResponse.data?.map { pref ->
            FoodPreference(
                id = pref["id"] as String,
                preferenceType = pref["preference_type"] as String,
                foodCategory = pref["food_category"] as String,
                foodItem = pref["food_item"] as? String,
                rating = (pref["rating"] as Number).toInt(),
                notes = pref["notes"] as? String,
                createdAt = pref["created_at"] as String
            )
        } ?: emptyList()

        // Get user profile preferences
        val profileResponse = supabase
            .from("user_preferences")
            .select("*")
            .eq("user_id", userId)
            .execute()

        val profileData = profileResponse.data?.firstOrNull()
        val dietaryRestrictions = (profileData?.get("dietary_restrictions") as? List<*>)?.map { it.toString() } ?: emptyList()
        val favoriteCuisines = (profileData?.get("favorite_cuisines") as? List<*>)?.map { it.toString() } ?: emptyList()

        return UserPreferences(
            userId = userId,
            foodPreferences = foodPreferences,
            dietaryRestrictions = dietaryRestrictions,
            favoriteCuisines = favoriteCuisines,
            spiceTolerance = profileData?.get("spice_tolerance") as? String,
            budgetPreference = profileData?.get("budget_preference") as? String
        )
    }

    suspend fun addFoodPreference(userId: String, preference: FoodPreference): String {
        val data = mapOf(
            "user_id" to userId,
            "preference_type" to preference.preferenceType,
            "food_category" to preference.foodCategory,
            "food_item" to preference.foodItem,
            "rating" to preference.rating,
            "notes" to preference.notes
        )

        val response = supabase
            .from("food_preferences")
            .insert(data)
            .execute()

        return response.data?.firstOrNull()?.get("id") as String
    }

    suspend fun updateUserProfile(userId: String, preferences: UserPreferences): Boolean {
        val data = mapOf(
            "user_id" to userId,
            "dietary_restrictions" to preferences.dietaryRestrictions,
            "favorite_cuisines" to preferences.favoriteCuisines,
            "spice_tolerance" to preferences.spiceTolerance,
            "budget_preference" to preferences.budgetPreference
        )

        supabase
            .from("user_preferences")
            .upsert(data, onConflict = "user_id")
            .execute()

        return true
    }

    suspend fun removeFoodPreference(userId: String, preferenceId: String): Boolean {
        supabase
            .from("food_preferences")
            .delete()
            .eq("id", preferenceId)
            .eq("user_id", userId)
            .execute()

        return true
    }
}