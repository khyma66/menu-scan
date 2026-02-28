package com.menuocr

import com.google.gson.Gson
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.util.concurrent.TimeUnit

object McpClient {

    private val gson = Gson()

    private val httpClient = OkHttpClient.Builder()
        .connectTimeout(AppConfig.Timeouts.CONNECT_TIMEOUT, TimeUnit.MILLISECONDS)
        .readTimeout(AppConfig.Timeouts.READ_TIMEOUT, TimeUnit.MILLISECONDS)
        .writeTimeout(AppConfig.Timeouts.WRITE_TIMEOUT, TimeUnit.MILLISECONDS)
        .build()

    data class McpRequest(
        val method: String,
        val token: String,
        val payload: Map<String, Any?>? = null
    )

    suspend fun call(method: String, payload: Map<String, Any?>? = null): Result<String> {
        return withContext(Dispatchers.IO) {
            try {
                val token = SupabaseClient.getAccessToken().orEmpty()
                if (token.isBlank()) {
                    Result.failure(IllegalStateException("User token missing"))
                } else {
                    val requestBody = gson.toJson(McpRequest(method = method, token = token, payload = payload))
                        .toRequestBody("application/json".toMediaType())

                    val request = Request.Builder()
                        .url("${AppConfig.Mcp.BASE_URL}/mcp/call")
                        .post(requestBody)
                        .build()

                    val response = httpClient.newCall(request).execute()
                    if (!response.isSuccessful) {
                        Result.failure(IllegalStateException("MCP call failed: ${response.code} ${response.message}"))
                    } else {
                        Result.success(response.body?.string().orEmpty())
                    }
                }

            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
}
