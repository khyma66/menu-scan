package com.menuocr

import android.util.Log
import retrofit2.Response

/**
 * Payment service wrapper with retry logic for handling transient failures
 */
class PaymentService(private val apiService: ApiService) {
    
    companion object {
        private const val TAG = "PaymentService"
    }
    
    /**
     * Create a payment intent with retry logic
     */
    suspend fun createPaymentIntent(request: PaymentIntentRequest): Response<PaymentIntentResponse> {
        return RetryHelper.retry {
            Log.d(TAG, "Creating payment intent for amount: ${request.amount}")
            apiService.createPaymentIntent(request)
        }
    }
    
    /**
     * Get payment history with retry logic
     */
    suspend fun getPaymentHistory(): Response<PaymentHistoryResponse> {
        return RetryHelper.retry {
            Log.d(TAG, "Fetching payment history")
            apiService.getPaymentHistory()
        }
    }
    
    /**
     * Process OCR with retry logic
     */
    suspend fun processOcr(request: OcrRequest): Response<MenuResponse> {
        return RetryHelper.retry {
            Log.d(TAG, "Processing OCR for language: ${request.language}")
            apiService.processOcr(request)
        }
    }
    
    /**
     * Extract dishes with retry logic
     */
    suspend fun extractDishes(request: DishRequest): Response<DishResponse> {
        return RetryHelper.retry {
            Log.d(TAG, "Extracting dishes from text")
            apiService.extractDishes(request)
        }
    }
    
    /**
     * Add food preference with retry logic
     */
    suspend fun addFoodPreference(request: FoodPreferenceRequest): Response<Map<String, Any>> {
        return RetryHelper.retry {
            Log.d(TAG, "Adding food preference: ${request.food_category}")
            apiService.addFoodPreference(request)
        }
    }
    
    /**
     * Get food preferences with retry logic
     */
    suspend fun getFoodPreferences(): Response<List<FoodPreference>> {
        return RetryHelper.retry {
            Log.d(TAG, "Fetching food preferences")
            apiService.getFoodPreferences()
        }
    }
    
    /**
     * Remove food preference with retry logic
     */
    suspend fun removeFoodPreference(preferenceId: String): Response<Map<String, Any>> {
        return RetryHelper.retry {
            Log.d(TAG, "Removing food preference: $preferenceId")
            apiService.removeFoodPreference(preferenceId)
        }
    }
    
    /**
     * Update user profile with retry logic
     */
    suspend fun updateUserProfile(request: UserProfileUpdateRequest): Response<Map<String, Any>> {
        return RetryHelper.retry {
            Log.d(TAG, "Updating user profile")
            apiService.updateUserProfile(request)
        }
    }
    
    /**
     * Get user profile with retry logic
     */
    suspend fun getUserProfile(): Response<UserPreferences> {
        return RetryHelper.retry {
            Log.d(TAG, "Fetching user profile")
            apiService.getUserProfile()
        }
    }
    
    /**
     * Check health with retry logic
     */
    suspend fun checkHealth(): Response<Map<String, Any>> {
        return RetryHelper.retry {
            Log.d(TAG, "Checking API health")
            apiService.checkHealth()
        }
    }
}
