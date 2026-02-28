package com.menuocr

import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.URL
import java.net.URLEncoder
import javax.net.ssl.HttpsURLConnection

/**
 * Service for querying OpenStreetMap Overpass API for restaurant data
 * 
 * Overpass API Documentation: https://wiki.openstreetmap.org/wiki/Overpass_API
 * Uses multiple endpoints with retry logic for reliability
 */
class OverpassApiService {

    companion object {
        private const val TAG = "OverpassApiService"
        
        // Multiple Overpass API endpoints for fallback
        private val OVERPASS_ENDPOINTS = listOf(
            "https://overpass-api.de/api",
            "https://maps.mail.ru/osm/tools/overpass/api",
            "https://overpass.kumi.systems/api",
            "https://overpass.openstreetmap.ru/api"
        )
    }

    /**
     * Query restaurants within a radius of a given point
     * 
     * @param latitude Center latitude
     * @param longitude Center longitude
     * @param radius Search radius in meters (default 500m)
     * @return List of restaurants from OpenStreetMap
     */
    suspend fun queryRestaurants(
        latitude: Double,
        longitude: Double,
        radius: Int = AppConfig.Overpass.DEFAULT_SEARCH_RADIUS
    ): Result<List<OverpassRestaurant>> = withContext(Dispatchers.IO) {
        val query = buildOverpassQuery(latitude, longitude, radius)
        
        // Try each endpoint until one succeeds
        for ((index, endpoint) in OVERPASS_ENDPOINTS.withIndex()) {
            try {
                Log.d(TAG, "Trying Overpass endpoint ${index + 1}/${OVERPASS_ENDPOINTS.size}: $endpoint")
                val response = executeOverpassQuery(query, endpoint)
                val restaurants = parseOverpassResponse(response)
                Log.d(TAG, "Successfully fetched ${restaurants.size} restaurants from $endpoint")
                return@withContext Result.success(restaurants)
            } catch (e: Exception) {
                Log.w(TAG, "Failed to query endpoint $endpoint: ${e.message}")
                if (index == OVERPASS_ENDPOINTS.size - 1) {
                    // Last endpoint failed, return error
                    Log.e(TAG, "All Overpass endpoints failed", e)
                    return@withContext Result.failure(e)
                }
                // Continue to next endpoint
            }
        }
        
        Result.failure(Exception("All Overpass API endpoints failed"))
    }

    /**
     * Build Overpass QL query for restaurants
     */
    private fun buildOverpassQuery(lat: Double, lon: Double, radius: Int): String {
        return """
            [out:json][timeout:${AppConfig.Overpass.TIMEOUT_SECONDS}];
            (
              node["amenity"="restaurant"](around:$radius,$lat,$lon);
              way["amenity"="restaurant"](around:$radius,$lat,$lon);
              relation["amenity"="restaurant"](around:$radius,$lat,$lon);
            );
            out center;
        """.trimIndent()
    }

    /**
     * Execute the Overpass query via HTTP POST
     */
    private fun executeOverpassQuery(query: String, baseUrl: String): String {
        val url = URL("$baseUrl${AppConfig.Overpass.INTERPRETER_ENDPOINT}")
        val encodedQuery = "data=${URLEncoder.encode(query, "UTF-8")}"
        
        val connection = (url.openConnection() as HttpsURLConnection).apply {
            requestMethod = "POST"
            doOutput = true
            setRequestProperty("Content-Type", "application/x-www-form-urlencoded")
            connectTimeout = AppConfig.Timeouts.CONNECT_TIMEOUT.toInt()
            readTimeout = AppConfig.Timeouts.READ_TIMEOUT.toInt()
        }

        try {
            // Send POST data
            connection.outputStream.use { os ->
                val input = encodedQuery.toByteArray(Charsets.UTF_8)
                os.write(input, 0, input.size)
            }

            // Read response
            val responseCode = connection.responseCode
            if (responseCode != HttpsURLConnection.HTTP_OK) {
                throw Exception("Overpass API returned HTTP $responseCode")
            }

            return connection.inputStream.use { it.bufferedReader().readText() }
        } finally {
            connection.disconnect()
        }
    }

    /**
     * Parse Overpass API JSON response
     */
    private fun parseOverpassResponse(jsonResponse: String): List<OverpassRestaurant> {
        val restaurants = mutableListOf<OverpassRestaurant>()
        
        try {
            val json = JSONObject(jsonResponse)
            val elements = json.optJSONArray("elements") ?: return emptyList()

            for (i in 0 until elements.length()) {
                val element = elements.getJSONObject(i)
                val restaurant = parseElement(element)
                if (restaurant != null) {
                    restaurants.add(restaurant)
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to parse Overpass response", e)
        }

        return restaurants
    }

    /**
     * Parse a single element from Overpass response
     */
    private fun parseElement(element: JSONObject): OverpassRestaurant? {
        try {
            val type = element.optString("type")
            val id = element.optLong("id")
            val tags = element.optJSONObject("tags") ?: return null
            
            // Get coordinates - for ways/relations use center, for nodes use direct lat/lon
            val lat: Double
            val lon: Double
            
            if (type == "node") {
                lat = element.optDouble("lat", 0.0)
                lon = element.optDouble("lon", 0.0)
            } else {
                // For ways and relations, use center coordinates
                val center = element.optJSONObject("center")
                if (center != null) {
                    lat = center.optDouble("lat", 0.0)
                    lon = center.optDouble("lon", 0.0)
                } else {
                    return null
                }
            }

            // Skip if coordinates are invalid
            if (lat == 0.0 && lon == 0.0) return null

            val name = tags.optString("name", "Unknown Restaurant")
            val cuisine = tags.optString("cuisine", "Unknown")
            val amenity = tags.optString("amenity", "restaurant")
            
            // Additional restaurant details
            val openingHours = tags.optString("opening_hours", null)
            val phone = tags.optString("phone", tags.optString("contact:phone", null))
            val website = tags.optString("website", tags.optString("contact:website", null))
            val address = buildAddress(tags)
            val wheelchair = tags.optString("wheelchair", null)
            val takeaway = tags.optString("takeaway", null)
            val delivery = tags.optString("delivery", null)
            val outdoorSeating = tags.optString("outdoor_seating", null)
            val internetAccess = tags.optString("internet_access", null)
            
            // Build tags list for display
            val displayTags = mutableListOf<String>()
            if (takeaway == "yes") displayTags.add("Takeaway")
            if (delivery == "yes") displayTags.add("Delivery")
            if (wheelchair == "yes") displayTags.add("Wheelchair")
            if (outdoorSeating == "yes") displayTags.add("Outdoor seating")
            if (internetAccess == "wlan" || internetAccess == "yes") displayTags.add("WiFi")

            return OverpassRestaurant(
                id = id,
                osmType = type,
                name = name,
                latitude = lat,
                longitude = lon,
                cuisine = cuisine,
                openingHours = openingHours,
                phone = phone,
                website = website,
                address = address,
                wheelchair = wheelchair == "yes",
                takeaway = takeaway == "yes",
                delivery = delivery == "yes",
                outdoorSeating = outdoorSeating == "yes",
                hasWifi = internetAccess == "wlan" || internetAccess == "yes",
                tags = displayTags
            )
        } catch (e: Exception) {
            Log.e(TAG, "Failed to parse element", e)
            return null
        }
    }

    /**
     * Build address string from OSM tags
     */
    private fun buildAddress(tags: JSONObject): String? {
        val parts = mutableListOf<String>()
        
        tags.optString("addr:street")?.let { if (it.isNotEmpty()) parts.add(it) }
        tags.optString("addr:housenumber")?.let { if (it.isNotEmpty()) parts.add(it) }
        tags.optString("addr:city")?.let { if (it.isNotEmpty()) parts.add(it) }
        tags.optString("addr:postcode")?.let { if (it.isNotEmpty()) parts.add(it) }
        
        return if (parts.isNotEmpty()) parts.joinToString(", ") else null
    }
}

/**
 * Data class representing a restaurant from Overpass API
 */
data class OverpassRestaurant(
    val id: Long,
    val osmType: String,
    val name: String,
    val latitude: Double,
    val longitude: Double,
    val cuisine: String,
    val openingHours: String?,
    val phone: String?,
    val website: String?,
    val address: String?,
    val wheelchair: Boolean,
    val takeaway: Boolean,
    val delivery: Boolean,
    val outdoorSeating: Boolean,
    val hasWifi: Boolean,
    val tags: List<String>
) {
    /**
     * Calculate distance from a given location
     */
    fun distanceFrom(lat: Double, lon: Double): Double {
        return haversineDistance(lat, lon, latitude, longitude)
    }

    /**
     * Haversine formula for distance calculation
     * Returns distance in kilometers
     */
    private fun haversineDistance(lat1: Double, lon1: Double, lat2: Double, lon2: Double): Double {
        val r = 6371.0 // Earth's radius in kilometers
        
        val latDistance = Math.toRadians(lat2 - lat1)
        val lonDistance = Math.toRadians(lon2 - lon1)
        
        val a = Math.sin(latDistance / 2) * Math.sin(latDistance / 2) +
                Math.cos(Math.toRadians(lat1)) * Math.cos(Math.toRadians(lat2)) *
                Math.sin(lonDistance / 2) * Math.sin(lonDistance / 2)
        
        val c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
        
        return r * c
    }

    /**
     * Get cuisine display name (capitalize first letter of each word)
     */
    fun getCuisineDisplayName(): String {
        return cuisine.split("_").joinToString(" ") { word ->
            word.lowercase().replaceFirstChar { it.uppercase() }
        }
    }
}
