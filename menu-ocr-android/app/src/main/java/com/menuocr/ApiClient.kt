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
    private var cachedToken: String? = null
    private var tokenCachedAtMs: Long = 0L
    private const val TOKEN_CACHE_TTL_MS = 60_000L
    
    /**
     * Create OkHttp client with retry, logging, and authentication
     */
    private fun createOkHttpClient(): OkHttpClient {
        val loggingInterceptor = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
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
            
            // Add common headers — do NOT set Content-Type here; OkHttp sets it
            // correctly per request (e.g. multipart/form-data for @Multipart endpoints).
            requestBuilder
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
        val baseUrl = if (AppConfig.FastApi.USE_LOCAL) {
            AppConfig.FastApi.LOCAL_BASE_URL
        } else {
            AppConfig.FastApi.BASE_URL
        }
        return Retrofit.Builder()
            .baseUrl(baseUrl)
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
     * Get authentication token from cache.
     * The token is set by [updateAuthToken] from a coroutine context after
     * sign-in / session-restore so the interceptor never needs to block.
     */
    private fun getAuthToken(): String? {
        val now = System.currentTimeMillis()
        if (cachedToken != null && now - tokenCachedAtMs < TOKEN_CACHE_TTL_MS) {
            return cachedToken
        }
        cachedToken = null
        return null
    }

    /**
     * Update the cached auth token. Call from a coroutine after sign-in
     * or session restore so the OkHttp interceptor can use it synchronously.
     */
    suspend fun updateAuthToken() {
        val token = SupabaseClient.getAccessToken()
        cachedToken = token
        tokenCachedAtMs = System.currentTimeMillis()
    }
    
    /**
     * Reset API client (useful for logout or configuration changes)
     */
    fun reset() {
        apiService = null
        paymentService = null
        cachedToken = null
        tokenCachedAtMs = 0L
    }
}
