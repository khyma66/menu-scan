package com.menuocr

import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

/**
 * Retrofit API client factory for Render backend
 */
object ApiClient {
    
    private var apiService: ApiService? = null
    private var paymentService: PaymentService? = null
    
    /**
     * Create OkHttp client with retry, logging, and authentication
     */
    private fun createOkHttpClient(): OkHttpClient {
        val loggingInterceptor = HttpLoggingInterceptor().apply {
            // Always use BODY level for debugging, change to NONE for production
            level = HttpLoggingInterceptor.Level.BODY
        }
        
        val authInterceptor = Interceptor { chain ->
            val originalRequest = chain.request()
            val requestBuilder = originalRequest.newBuilder()
            
            // Add authorization header if user is authenticated
            // This will be populated from Supabase session
            val token = getAuthToken()
            if (token != null) {
                requestBuilder.header("Authorization", "Bearer $token")
            }
            
            // Add common headers
            requestBuilder
                .header("Content-Type", "application/json")
                .header("Accept", "application/json")
            
            chain.proceed(requestBuilder.build())
        }
        
        return OkHttpClient.Builder()
            .addInterceptor(loggingInterceptor)
            .addInterceptor(authInterceptor)
            .connectTimeout(AppConfig.Timeouts.CONNECT_TIMEOUT, TimeUnit.MILLISECONDS)
            .readTimeout(AppConfig.Timeouts.READ_TIMEOUT, TimeUnit.MILLISECONDS)
            .writeTimeout(AppConfig.Timeouts.WRITE_TIMEOUT, TimeUnit.MILLISECONDS)
            .retryOnConnectionFailure(true)
            .build()
    }
    
    /**
     * Create Retrofit instance
     */
    private fun createRetrofit(): Retrofit {
        return Retrofit.Builder()
            .baseUrl(AppConfig.Render.BASE_URL)
            .client(createOkHttpClient())
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }
    
    /**
     * Get API service instance (singleton)
     */
    fun getApiService(): ApiService {
        if (apiService == null) {
            apiService = createRetrofit().create(ApiService::class.java)
        }
        return apiService!!
    }
    
    /**
     * Get Payment service instance with retry logic (singleton)
     */
    fun getPaymentService(): PaymentService {
        if (paymentService == null) {
            paymentService = PaymentService(getApiService())
        }
        return paymentService!!
    }
    
    /**
     * Get authentication token from Supabase
     * This should be called from a coroutine context
     */
    private fun getAuthToken(): String? {
        // This is a synchronous call, so we return null here
        // The actual token should be cached or retrieved differently
        // For now, return null and handle auth in the calling code
        return null
    }
    
    /**
     * Reset API client (useful for logout or configuration changes)
     */
    fun reset() {
        apiService = null
        paymentService = null
    }
}
