package com.menuocr

import okhttp3.MultipartBody
import okhttp3.RequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.Field
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path
import retrofit2.http.Part
import retrofit2.http.Query
import okhttp3.MediaType.Companion.toMediaType

interface ApiService {

    @GET("/health")
    suspend fun checkHealth(): Response<Map<String, Any>>

    @GET("/test-db")
    suspend fun testDb(): Response<Map<String, Any>>

    @Multipart
    @POST("/v1/menus:scan")
    suspend fun scanMenu(
        @Part pages: List<MultipartBody.Part>,
        @Part("target_lang") targetLang: RequestBody,
        @Part("user_country") userCountry: RequestBody,
        @Part("restaurant_name") restaurantName: RequestBody,
        @Part("region") region: RequestBody,
        @Part("cuisine_type") cuisineType: RequestBody
    ): Response<ScanMenuResponse>

    @GET("/v1/jobs/{jobId}")
    suspend fun getJobStatus(@Path("jobId") jobId: String): Response<JobStatusResponse>

    @GET("/v1/menus/{menuId}/personalized")
    suspend fun getPersonalizedMenu(@Path("menuId") menuId: String): Response<PersonalizedMenuResponse>

    @GET("/v1/user/health-profile")
    suspend fun getHealthProfile(): Response<HealthProfileResponse>

    @GET("/v1/user/menus")
    suspend fun getUserMenus(): Response<UserMenusResponse>

    @PUT("/v1/user/health-profile")
    suspend fun updateHealthProfile(@Body request: HealthProfileRequest): Response<HealthProfileResponse>

    @DELETE("/v1/user/account")
    suspend fun deleteUserAccount(): Response<Map<String, Any>>

    @POST("/ocr/process")
    suspend fun processOcr(@Body request: OcrRequest): Response<MenuResponse>

    @Multipart
    @POST("/ocr/process-upload")
    suspend fun processOcrUpload(
        
        @Part image: MultipartBody.Part,
        @Part("use_llm_enhancement") useLlmEnhancement: RequestBody = RequestBody.create("text/plain".toMediaType(), "true"),
        @Part("use_qwen_vision") useQwenVision: RequestBody = RequestBody.create("text/plain".toMediaType(), "true"),
        @Part("language") language: RequestBody = RequestBody.create("text/plain".toMediaType(), "auto")
    ): Response<MenuResponse>

    // Enhanced OCR using existing endpoints
    @Multipart
    @POST("/ocr/process-upload")
    suspend fun processEnhancedOcrUpload(

        @Part image: MultipartBody.Part,
        @Part("use_llm_enhancement") useLlmEnhancement: RequestBody = RequestBody.create("text/plain".toMediaType(), "true"),
        @Part("use_qwen_vision") useQwenVision: RequestBody = RequestBody.create("text/plain".toMediaType(), "true"),
        @Part("language") language: RequestBody = RequestBody.create("text/plain".toMediaType(), "auto"),
        @Part("output_language") outputLanguage: RequestBody = RequestBody.create("text/plain".toMediaType(), "en")
    ): Response<MenuResponse>

    @POST("/ocr/translate-menu-items")
    suspend fun translateMenuItems(@Body request: MenuItemsTranslationRequest): Response<MenuItemsTranslationResponse>

    @POST("/ocr/process")
    suspend fun processEnhancedOcrUrl(
        @Body request: OcrRequest
    ): Response<MenuResponse>

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

    @POST("/auth/reset-password")
    suspend fun requestPasswordReset(@Body request: Map<String, String>): Response<Map<String, Any>>

    @GET("/user/app-profile")
    suspend fun getAppProfile(): Response<AppProfileDetails>

    @PUT("/user/app-profile")
    suspend fun updateAppProfile(@Body request: AppProfileDetailsRequest): Response<AppProfileDetails>

    @GET("/user/profile-preferences")
    suspend fun getProfilePreferences(): Response<ProfilePreferences>

    @PUT("/user/profile-preferences")
    suspend fun updateProfilePreferences(@Body request: ProfilePreferencesRequest): Response<ProfilePreferences>

    @GET("/user/recent-scans")
    suspend fun getRecentScans(@Query("days") days: Int = 30, @Query("limit") limit: Int = 50): Response<RecentScansListResponse>

    @GET("/user/recent-scans/daily")
    suspend fun getDailyScans(@Query("days") days: Int = 7): Response<DailyScansListResponse>

    @GET("/user/saved-cards")
    suspend fun getSavedCards(): Response<SavedCardsResponse>

    @POST("/user/saved-cards")
    suspend fun saveCard(@Body request: SaveCardRequest): Response<SavedCard>

    @GET("/user/payment-history")
    suspend fun getUserPaymentHistory(): Response<UserPaymentHistoryResponse>

    @GET("/user/subscription/plans")
    suspend fun getSubscriptionPlans(): Response<SubscriptionPlansResponse>

    @GET("/user/subscription")
    suspend fun getSubscriptionInfo(): Response<UserSubscriptionStatus>

    @PUT("/user/subscription/select")
    suspend fun selectSubscriptionPlan(@Body request: SelectSubscriptionPlanRequest): Response<UserSubscriptionStatus>

    /** Get Stripe Customer Portal URL — open in browser to manage/cancel subscription */
    @POST("/subscriptions/customer-portal")
    suspend fun getCustomerPortal(@Header("Authorization") token: String): Response<CustomerPortalResponse>

    /** Get current subscription status from the new commission-free endpoint */
    @GET("/subscriptions/status")
    suspend fun getSubscriptionStatus(@Header("Authorization") token: String): Response<SubscriptionStatusResponse>
}

data class ScanMenuResponse(
    val job_id: String,
    val status: String,
    val is_cached: Boolean,
    val cache_hit_from: String?,
    val menu_id: String?
)

data class JobStatusResponse(
    val job_id: String?,
    val status: String,
    val error: String?,
    val menu: MenuResult?
)

data class MenuResult(
    val id: String,
    val restaurant_name: String?,
    val region: String?,
    val cuisine_type: String?,
    val ocr_raw: String?,
    val personalized: List<PersonalizedDish>?
)

data class PersonalizedMenuResponse(
    val menu_id: String,
    val personalized: List<PersonalizedDish>
)

data class PersonalizedDish(
    val dish_id: String,
    val dish_name: String,
    val price: Double?,
    val ingredients: String?,
    val calories: Int?,
    val recommendation_level: String?,
    val risk_summary: String?,
    val trigger_ingredients: Any?,
    val alternative_suggestion: String?,
    val health_score: Double?
) : java.io.Serializable

data class HealthProfileRequest(
    val health_conditions: List<String>?,
    val allergies: List<String>?,
    val dietary_preferences: List<String>?,
    val medical_notes: String?
)

data class HealthProfileResponse(
    val health_profile: HealthProfile?
)

data class UserMenusResponse(
    val menus: List<UserMenu>
)

data class UserMenu(
    val id: String,
    val restaurant_name: String?,
    val region: String?,
    val cuisine_type: String?,
    val created_at: String?
)

data class HealthProfile(
    val health_conditions: List<String>?,
    val allergies: List<String>?,
    val dietary_preferences: List<String>?,
    val medical_notes: String?
) : java.io.Serializable

data class OcrRequest(
    val image_base64: String,
    val language: String = "en",
    val prompt: String? = null
)

data class MenuResponse(
    val success: Boolean? = null,
    val menu_items: List<MenuItem>? = null,
    val gemini_menu_items: List<MenuItem>? = null,
    val qwen_menu_items: List<MenuItem>? = null,
    val raw_text: String? = null,
    val processing_time_ms: Int? = null,
    val enhanced: Boolean? = null,
    val cached: Boolean? = null,
    val metadata: Map<String, Any>? = null
)

data class MenuItem(
    val name: String?,
    val price: String?,
    val description: String?,
    val category: String?,
    val ingredients: List<String>? = null,
    val taste: String? = null,
    val similarDish1: String? = null,
    val similarDish2: String? = null,
    val recommendation: String? = null,
    val recommendation_reason: String? = null,
    val allergens: List<String>? = null,
    val spiciness_level: String? = null,
    val preparation_method: String? = null
)

data class MenuItemsTranslationRequest(
    val menu_items: List<MenuItem>,
    val target_language: String
)

data class MenuItemsTranslationResponse(
    val menu_items: List<MenuItem>
)

data class DishRequest(
    val text: String,
    val language: String = "en"
)

data class DishResponse(
    val dishes: List<Dish>? = null
)

data class Dish(
    val name: String?,
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

data class AppProfileDetailsRequest(
    val full_name: String? = null,
    val email: String? = null,
    val contact: String? = null,
    val phone: String? = null,
    val country: String? = null
)

data class AppProfileDetails(
    val user_id: String,
    val full_name: String? = null,
    val email: String? = null,
    val contact: String? = null,
    val phone: String? = null,
    val country: String? = null,
    val updated_at: String? = null
)

data class ProfilePreferencesRequest(
    val notifications_enabled: Boolean = true,
    val push_notifications: Boolean = true,
    val email_notifications: Boolean = false,
    val language: String? = null,
    val timezone: String? = null
)

data class ProfilePreferences(
    val user_id: String,
    val notifications_enabled: Boolean = true,
    val push_notifications: Boolean = true,
    val email_notifications: Boolean = false,
    val language: String? = null,
    val timezone: String? = null,
    val updated_at: String? = null
)

data class RecentScan(
    val id: String,
    val scanned_at: String,
    val source: String? = null,
    val image_name: String? = null,
    val detected_language: String? = null,
    val output_language: String? = null,
    val dish_count: Int? = null,
    val processing_status: String = "completed",
    val processing_time_ms: Int? = null,
    val pipeline: String? = null
)

data class RecentScansListResponse(
    val scans: List<RecentScan>,
    val total_count: Int = 0
)

data class DailyScanGroup(
    val date: String,
    val scans: List<RecentScan>,
    val count: Int = 0
)

data class DailyScansListResponse(
    val days: List<DailyScanGroup>,
    val total_count: Int = 0
)

data class SaveCardRequest(
    val card_brand: String,
    val card_last_four: String,
    val card_exp_month: Int,
    val card_exp_year: Int,
    val cardholder_name: String? = null,
    val tokenized_card_id: String? = null,
    val is_default: Boolean = true
)

data class SavedCard(
    val id: String,
    val card_brand: String,
    val card_last_four: String,
    val card_exp_month: Int,
    val card_exp_year: Int,
    val cardholder_name: String? = null,
    val is_default: Boolean = false,
    val created_at: String? = null
)

data class SavedCardsResponse(
    val cards: List<SavedCard>
)

data class UserPaymentRecord(
    val id: String,
    val amount_cents: Int,
    val currency: String,
    val status: String,
    val transaction_type: String,
    val created_at: String? = null
)

data class UserPaymentHistoryResponse(
    val payments: List<UserPaymentRecord>
)

data class SubscriptionPlan(
    val name: String,
    val price: Double? = null,
    val price_display: String? = null,
    val display_name: String? = null,
    val billing_period: String? = null,
    val currency: String? = null,
    val description: String? = null,
    val features: List<String>? = null
) {
    /** Resolve display price: prefer price_display string, else format from price number */
    fun resolvedPriceDisplay(): String? {
        if (!price_display.isNullOrBlank()) return price_display
        if (price != null) {
            return if (price == 0.0) "$0" else "$${String.format("%.2f", price)}"
        }
        return null
    }
}

data class SubscriptionPlansResponse(
    val plans: List<SubscriptionPlan>
)

data class SelectSubscriptionPlanRequest(
    val plan_name: String
)

data class UserSubscriptionStatus(
    val plan_name: String,
    val plan_description: String,
    val status: String,
    val current_period_end: String? = null,
    val cancel_at_period_end: Boolean = false
)

data class CustomerPortalResponse(
    val portal_url: String
)

data class SubscriptionStatusResponse(
    val plan_id: String,
    val plan_name: String,
    val status: String,
    val is_effective: Boolean,
    val scan_limit_monthly: Int,
    val features: List<String>,
    val current_period_end: String? = null,
    val cancel_at_period_end: Boolean = false,
    val billing_cycle: String? = null
)