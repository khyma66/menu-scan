package com.menuocr

import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path

interface ApiService {

    @GET("/health")
    suspend fun checkHealth(): Response<Map<String, Any>>

    @POST("/ocr/process")
    suspend fun processOcr(@Body request: OcrRequest): Response<MenuResponse>

    @POST("/dishes/extract")
    suspend fun extractDishes(@Body request: DishRequest): Response<DishResponse>

    @POST("/payments/create-payment-intent")
    suspend fun createPaymentIntent(@Body request: PaymentIntentRequest): Response<PaymentIntentResponse>

    @GET("/payments/history")
    suspend fun getPaymentHistory(): Response<PaymentHistoryResponse>

    @POST("/user/preferences/food-preferences")
    suspend fun addFoodPreference(@Body request: FoodPreferenceRequest): Response<Map<String, Any>>

    @GET("/user/preferences/food-preferences")
    suspend fun getFoodPreferences(): Response<List<FoodPreference>>

    @DELETE("/user/preferences/food-preferences/{preferenceId}")
    suspend fun removeFoodPreference(@Path("preferenceId") preferenceId: String): Response<Map<String, Any>>

    @PUT("/user/preferences/profile")
    suspend fun updateUserProfile(@Body request: UserProfileUpdateRequest): Response<Map<String, Any>>

    @GET("/user/preferences/profile")
    suspend fun getUserProfile(): Response<UserPreferences>
}

data class OcrRequest(
    val image_base64: String,
    val language: String = "en"
)

data class MenuResponse(
    val success: Boolean,
    val menu_items: List<MenuItem>,
    val raw_text: String,
    val processing_time_ms: Int,
    val enhanced: Boolean? = null,
    val cached: Boolean? = null,
    val metadata: Map<String, Any>? = null
)

data class MenuItem(
    val name: String,
    val price: String?,
    val description: String?,
    val category: String?
)

data class DishRequest(
    val text: String,
    val language: String = "en"
)

data class DishResponse(
    val dishes: List<Dish>
)

data class Dish(
    val name: String,
    val price: Double?,
    val description: String?
)

data class PaymentIntentRequest(
    val amount: Int,
    val currency: String = "usd",
    val description: String? = null,
    val metadata: Map<String, String>? = null
)

data class PaymentIntentResponse(
    val client_secret: String,
    val payment_intent_id: String,
    val amount: Int,
    val currency: String,
    val status: String
)

data class PaymentHistoryResponse(
    val payment_intents: List<PaymentIntent>,
    val subscriptions: List<Subscription>
)

data class PaymentIntent(
    val id: String,
    val amount: Int,
    val currency: String,
    val status: String,
    val created: Long,
    val description: String?
)

data class Subscription(
    val id: String,
    val status: String,
    val current_period_start: Long,
    val current_period_end: Long,
    val items: List<SubscriptionItem>
)

data class SubscriptionItem(
    val price: Price
)

data class Price(
    val id: String,
    val nickname: String?,
    val unit_amount: Int?,
    val currency: String
)

// User Preferences Models
data class FoodPreference(
    val id: String,
    val preferenceType: String,
    val foodCategory: String,
    val foodItem: String?,
    val rating: Int,
    val notes: String?,
    val createdAt: String
)

data class UserPreferences(
    val userId: String,
    val foodPreferences: List<FoodPreference>,
    val dietaryRestrictions: List<String>,
    val favoriteCuisines: List<String>,
    val spiceTolerance: String?,
    val budgetPreference: String?
)

data class FoodPreferenceRequest(
    val preference_type: String,
    val food_category: String,
    val food_item: String?,
    val rating: Int,
    val notes: String?
)

data class UserProfileUpdateRequest(
    val dietary_restrictions: List<String>?,
    val favorite_cuisines: List<String>?,
    val spice_tolerance: String?,
    val budget_preference: String?
)