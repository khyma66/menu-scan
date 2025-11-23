package com.menuocr

import android.util.Log
import kotlinx.coroutines.delay
import kotlin.math.pow

/**
 * Retry configuration for handling transient failures
 */
data class RetryConfig(
    val enabled: Boolean = true,
    val delaySeconds: Long = 10,
    val maxAttempts: Int = 3,
    val backoffMultiplier: Float = 1.0f
)

/**
 * Retry helper for handling transient failures with configurable retry logic
 */
object RetryHelper {
    private const val TAG = "RetryHelper"
    
    /**
     * Default retry configuration matching Kilocode config
     */
    val DEFAULT_CONFIG = RetryConfig(
        enabled = true,
        delaySeconds = 10,
        maxAttempts = 3,
        backoffMultiplier = 1.0f
    )
    
    /**
     * Retry a suspending function with exponential backoff
     * 
     * @param config Retry configuration (uses default if null)
     * @param block The suspending function to retry
     * @return The result of the function call
     * @throws The last exception if all retries fail
     */
    suspend fun <T> retry(
        config: RetryConfig = DEFAULT_CONFIG,
        block: suspend () -> T
    ): T {
        if (!config.enabled) {
            return block()
        }
        
        var lastException: Exception? = null
        var currentDelay = config.delaySeconds * 1000L // Convert to milliseconds
        
        for (attempt in 1..config.maxAttempts) {
            try {
                Log.i(TAG, "Attempt $attempt/${config.maxAttempts}")
                val result = block()
                if (attempt > 1) {
                    Log.i(TAG, "Successfully executed on attempt $attempt")
                }
                return result
            } catch (e: Exception) {
                lastException = e
                Log.w(TAG, "Attempt $attempt/${config.maxAttempts} failed: ${e.message}")
                
                if (attempt < config.maxAttempts) {
                    Log.i(TAG, "Retrying in ${currentDelay / 1000} seconds...")
                    delay(currentDelay)
                    currentDelay = (currentDelay * config.backoffMultiplier).toLong()
                } else {
                    Log.e(TAG, "All ${config.maxAttempts} attempts failed")
                }
            }
        }
        
        throw lastException ?: Exception("Retry failed with unknown error")
    }
    
    /**
     * Retry a regular (non-suspending) function with exponential backoff
     * 
     * @param config Retry configuration (uses default if null)
     * @param block The function to retry
     * @return The result of the function call
     * @throws The last exception if all retries fail
     */
    fun <T> retrySync(
        config: RetryConfig = DEFAULT_CONFIG,
        block: () -> T
    ): T {
        if (!config.enabled) {
            return block()
        }
        
        var lastException: Exception? = null
        var currentDelay = config.delaySeconds * 1000L // Convert to milliseconds
        
        for (attempt in 1..config.maxAttempts) {
            try {
                Log.i(TAG, "Attempt $attempt/${config.maxAttempts}")
                val result = block()
                if (attempt > 1) {
                    Log.i(TAG, "Successfully executed on attempt $attempt")
                }
                return result
            } catch (e: Exception) {
                lastException = e
                Log.w(TAG, "Attempt $attempt/${config.maxAttempts} failed: ${e.message}")
                
                if (attempt < config.maxAttempts) {
                    Log.i(TAG, "Retrying in ${currentDelay / 1000} seconds...")
                    Thread.sleep(currentDelay)
                    currentDelay = (currentDelay * config.backoffMultiplier).toLong()
                } else {
                    Log.e(TAG, "All ${config.maxAttempts} attempts failed")
                }
            }
        }
        
        throw lastException ?: Exception("Retry failed with unknown error")
    }
}
