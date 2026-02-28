package com.menuocr

/**
 * Application configuration for Supabase and Render API endpoints
 */
object AppConfig {
    
    // Supabase Configuration
    object Supabase {
        // Supabase project URL
        const val URL = "https://jlfqzcaospvspmzbvbxd.supabase.co"
        
        // Get your anon/public key from: https://supabase.com/dashboard/project/jlfqzcaospvspmzbvbxd/settings/api
        // This is a PUBLIC key - safe to use in client apps
        const val ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpsZnF6Y2Fvc3B2c3BtemJ2YnhkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEzNzAzMzYsImV4cCI6MjA3Njk0NjMzNn0.cTI-Zo2NXeIZQDiQ4mcLia3slwRMyvMLpLj_-4BtviA"
        const val AUTH_REDIRECT_URL = "com.menuocr://auth-callback"
    }
    
    // Menu OCR API Configuration (using local backend for development)
    object MenuOcrApi {
        const val BASE_URL = "https://menu-ocr-f4mr.onrender.com"
        const val LOCAL_BASE_URL = "http://10.0.2.2:8787"
        const val USE_LOCAL = true
    }

    // FastAPI OCR backend (Gemini extraction + Groq enhancement)
    object FastApi {
        const val BASE_URL = "https://menu-ocr-f4mr.onrender.com"
        const val LOCAL_BASE_URL = "http://10.0.2.2:8000"
        const val USE_LOCAL = true
    }

    // Legacy Render API Configuration (payments, preferences)
    object Render {
        const val BASE_URL = "https://menu-ocr-f4mr.onrender.com"
        const val OCR_ENDPOINT = "/ocr/process"
        const val DISHES_ENDPOINT = "/dishes/extract"
        const val PAYMENTS_ENDPOINT = "/payments"
        const val HEALTH_ENDPOINT = "/health"
        const val USER_PREFERENCES_ENDPOINT = "/user/preferences"
    }

    // MCP Configuration (optional)
    object Mcp {
        const val BASE_URL = "http://10.0.2.2:8001"
        const val AUTH_TOKEN = ""
    }
    
    // Retry Configuration (matching Kilocode config)
    object Retry {
        const val ENABLED = true
        const val DELAY_SECONDS = 10L
        const val MAX_ATTEMPTS = 3
        const val BACKOFF_MULTIPLIER = 1.0f
    }
    
    // Stripe Configuration
    object Stripe {
        // Replace with your actual Stripe publishable key
        const val PUBLISHABLE_KEY = "pk_test_51SWk8N1HFXSHAnudIASPucwXm6GPQdWk52CfSUXVC71R5rVLjQ3TFySSfJr6NNg1azeJ54PpVAhJog0QXdE2vPjI00tTJMuDZD"
    }
    
    // Feature Flags
    object Features {
        const val ENABLE_OFFLINE_MODE = false
        const val ENABLE_ANALYTICS = true
        const val ENABLE_CRASH_REPORTING = true
    }
    
    // Timeouts (in milliseconds)
    object Timeouts {
        const val CONNECT_TIMEOUT = 30_000L
        const val READ_TIMEOUT = 60_000L
        const val WRITE_TIMEOUT = 60_000L
    }
    
    // Overpass API Configuration (OpenStreetMap POI data)
    object Overpass {
        const val BASE_URL = "https://overpass-api.de/api"
        const val INTERPRETER_ENDPOINT = "/interpreter"
        const val DEFAULT_SEARCH_RADIUS = 16000 // 10 miles in meters
        const val MIN_SEARCH_RADIUS = 500 // 0.3 miles
        const val MAX_SEARCH_RADIUS = 32000 // 20 miles
        const val TIMEOUT_SECONDS = 30
    }
    
    // OpenStreetMap Configuration
    object OSM {
        const val TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        const val ATTRIBUTION = "© OpenStreetMap contributors"
        const val MAP_STYLE_URL = "https://demotiles.maplibre.org/style.json"
    }
    
    // Google Sign-In Configuration
    // Get your server client ID from Google Cloud Console
    // This is the OAuth 2.0 client ID for web application (used by Supabase)
    object GoogleAuth {
        // Replace with your actual server client ID from Google Cloud Console
        // This should match the one configured in Supabase Auth > Providers > Google
        const val SERVER_CLIENT_ID = "YOUR_GOOGLE_SERVER_CLIENT_ID.apps.googleusercontent.com"
    }
}
