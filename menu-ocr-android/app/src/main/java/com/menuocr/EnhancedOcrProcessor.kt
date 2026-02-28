package com.menuocr

import android.graphics.Bitmap
import android.util.Base64
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import retrofit2.Response
import java.io.ByteArrayOutputStream
import java.io.File

/**
 * Enhanced OCR Processor using OpenRouter/Qwen for better menu extraction
 */
class EnhancedOcrProcessor(
    private val apiService: ApiService
) {
    
    /**
     * Process image using enhanced OCR with OpenRouter integration
     */
    suspend fun processImageEnhanced(
        bitmap: Bitmap, 
        enhancementLevel: String = "high"
    ): EnhancedMenuResponse {
        return try {
            // Convert bitmap to base64 for multipart upload
            val byteArrayOutputStream = ByteArrayOutputStream()
            bitmap.compress(Bitmap.CompressFormat.JPEG, 90, byteArrayOutputStream)
            val imageBytes = byteArrayOutputStream.toByteArray()
            
            // Create multipart request
            val imageRequestBody = imageBytes.toRequestBody("image/jpeg".toMediaType())
            val imagePart = MultipartBody.Part.createFormData("image", "menu_image.jpg", imageRequestBody)

            // Map enhancement level to API parameters
            val useLlmEnhancement = when (enhancementLevel) {
                "high" -> "true"
                "balanced" -> "true"
                "fast" -> "false"
                else -> "true"
            }.toRequestBody("text/plain".toMediaType())

            val useQwenVision = when (enhancementLevel) {
                "high" -> "true"
                "balanced" -> "false"
                "fast" -> "false"
                else -> "true"
            }.toRequestBody("text/plain".toMediaType())

            val language = "auto".toRequestBody("text/plain".toMediaType())

            val response = apiService.processEnhancedOcrUpload(
                image = imagePart,
                useLlmEnhancement = useLlmEnhancement,
                useQwenVision = useQwenVision,
                language = language
            )
            
            if (response.isSuccessful) {
                response.body()?.let { menuResponse ->
                    EnhancedMenuResponse(
                        success = menuResponse.success == true,
                        menuItems = menuResponse.menu_items.orEmpty(),
                        rawText = menuResponse.raw_text.orEmpty(),
                        processingTimeMs = menuResponse.processing_time_ms ?: 0,
                        enhanced = menuResponse.enhanced ?: true,
                        cached = menuResponse.cached ?: false,
                        metadata = menuResponse.metadata ?: emptyMap(),
                        enhancementLevel = enhancementLevel,
                        openrouterUsed = true,
                        confidenceScore = extractConfidenceFromMetadata(menuResponse.metadata)
                    )
                } ?: EnhancedMenuResponse(
                    success = false,
                    menuItems = emptyList(),
                    rawText = "",
                    processingTimeMs = 0,
                    enhanced = false,
                    cached = false,
                    metadata = emptyMap(),
                    enhancementLevel = enhancementLevel,
                    openrouterUsed = false,
                    confidenceScore = 0.0,
                    errorMessage = "Empty response body"
                )
            } else {
                EnhancedMenuResponse(
                    success = false,
                    menuItems = emptyList(),
                    rawText = "",
                    processingTimeMs = 0,
                    enhanced = false,
                    cached = false,
                    metadata = emptyMap(),
                    enhancementLevel = enhancementLevel,
                    openrouterUsed = false,
                    confidenceScore = 0.0,
                    errorMessage = "HTTP ${response.code()}: ${response.message()}"
                )
            }
        } catch (e: Exception) {
            EnhancedMenuResponse(
                success = false,
                menuItems = emptyList(),
                rawText = "",
                processingTimeMs = 0,
                enhanced = false,
                cached = false,
                metadata = emptyMap(),
                enhancementLevel = enhancementLevel,
                openrouterUsed = false,
                confidenceScore = 0.0,
                errorMessage = "OCR processing failed: ${e.message}"
            )
        }
    }
    
    /**
     * Process image using URL with enhanced OCR
     */
    suspend fun processImageFromUrl(
        imageUrl: String,
        enhancementLevel: String = "high"
    ): EnhancedMenuResponse {
        return try {
            val request = OcrRequest(
                image_base64 = "",  // Not used for URL
                language = "auto"
            )
            // Note: This method doesn't actually use the imageUrl parameter
            // The backend expects image_url in the request body, but our current API doesn't support it
            // For now, we'll use the base64 method
            val response = apiService.processOcr(request)
            
            if (response.isSuccessful) {
                response.body()?.let { menuResponse ->
                    EnhancedMenuResponse(
                        success = menuResponse.success == true,
                        menuItems = menuResponse.menu_items.orEmpty(),
                        rawText = menuResponse.raw_text.orEmpty(),
                        processingTimeMs = menuResponse.processing_time_ms ?: 0,
                        enhanced = menuResponse.enhanced ?: true,
                        cached = menuResponse.cached ?: false,
                        metadata = menuResponse.metadata ?: emptyMap(),
                        enhancementLevel = enhancementLevel,
                        openrouterUsed = true,
                        confidenceScore = extractConfidenceFromMetadata(menuResponse.metadata)
                    )
                } ?: EnhancedMenuResponse(
                    success = false,
                    menuItems = emptyList(),
                    rawText = "",
                    processingTimeMs = 0,
                    enhanced = false,
                    cached = false,
                    metadata = emptyMap(),
                    enhancementLevel = enhancementLevel,
                    openrouterUsed = false,
                    confidenceScore = 0.0,
                    errorMessage = "Empty response body"
                )
            } else {
                EnhancedMenuResponse(
                    success = false,
                    menuItems = emptyList(),
                    rawText = "",
                    processingTimeMs = 0,
                    enhanced = false,
                    cached = false,
                    metadata = emptyMap(),
                    enhancementLevel = enhancementLevel,
                    openrouterUsed = false,
                    confidenceScore = 0.0,
                    errorMessage = "HTTP ${response.code()}: ${response.message()}"
                )
            }
        } catch (e: Exception) {
            EnhancedMenuResponse(
                success = false,
                menuItems = emptyList(),
                rawText = "",
                processingTimeMs = 0,
                enhanced = false,
                cached = false,
                metadata = emptyMap(),
                enhancementLevel = enhancementLevel,
                openrouterUsed = false,
                confidenceScore = 0.0,
                errorMessage = "OCR processing failed: ${e.message}"
            )
        }
    }
    
    /**
     * Fallback to original OCR processing if enhanced fails
     */
    suspend fun processImageWithFallback(
        bitmap: Bitmap,
        enhancementLevel: String = "high"
    ): EnhancedMenuResponse {
        // First try enhanced OCR
        val enhancedResult = processImageEnhanced(bitmap, enhancementLevel)
        
        // If enhanced fails, try regular OCR as fallback
        if (!enhancedResult.success && enhancedResult.errorMessage != null) {
            try {
                val byteArrayOutputStream = ByteArrayOutputStream()
                bitmap.compress(Bitmap.CompressFormat.JPEG, 90, byteArrayOutputStream)
                val imageBase64 = Base64.encodeToString(byteArrayOutputStream.toByteArray(), Base64.DEFAULT)
                
                val fallbackRequest = OcrRequest(
                    image_base64 = imageBase64,
                    language = "auto"
                )
                
                val fallbackResponse = apiService.processOcr(fallbackRequest)
                
                if (fallbackResponse.isSuccessful) {
                    fallbackResponse.body()?.let { menuResponse ->
                        return EnhancedMenuResponse(
                            success = menuResponse.success == true,
                            menuItems = menuResponse.menu_items.orEmpty(),
                            rawText = menuResponse.raw_text.orEmpty(),
                            processingTimeMs = menuResponse.processing_time_ms ?: 0,
                            enhanced = false,
                            cached = menuResponse.cached ?: false,
                            metadata = menuResponse.metadata ?: emptyMap(),
                            enhancementLevel = "fallback",
                            openrouterUsed = false,
                            confidenceScore = extractConfidenceFromMetadata(menuResponse.metadata),
                            errorMessage = "Used fallback OCR due to enhanced OCR failure: ${enhancedResult.errorMessage}"
                        )
                    }
                }
            } catch (e: Exception) {
                // If fallback also fails, return the original enhanced result with error
                return enhancedResult.copy(
                    errorMessage = "Both enhanced and fallback OCR failed. Enhanced: ${enhancedResult.errorMessage}, Fallback: ${e.message}"
                )
            }
        }
        
        return enhancedResult
    }
    
    private fun extractConfidenceFromMetadata(metadata: Map<String, Any>?): Double {
        return try {
            when (val confidence = metadata?.get("confidence")) {
                is Double -> confidence
                is Float -> confidence.toDouble()
                is Int -> confidence.toDouble()
                is String -> confidence.toDoubleOrNull() ?: 0.0
                else -> 0.0
            }
        } catch (e: Exception) {
            0.0
        }
    }
}

/**
 * Enhanced menu response with OpenRouter metadata
 */
data class EnhancedMenuResponse(
    val success: Boolean,
    val menuItems: List<MenuItem>,
    val rawText: String,
    val processingTimeMs: Int,
    val enhanced: Boolean,
    val cached: Boolean,
    val metadata: Map<String, Any>,
    val enhancementLevel: String,
    val openrouterUsed: Boolean,
    val confidenceScore: Double,
    val errorMessage: String? = null
)