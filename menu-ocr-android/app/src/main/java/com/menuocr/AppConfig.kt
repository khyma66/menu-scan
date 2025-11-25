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
        const val ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpsZnF6Y2Fvc3B2c3BtemJ2YnhkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTM3MDMzNiwiZXhwIjoyMDc2OTQ2MzM2fQ.5xdkvyJSsza79Iz3kiASMEE22WhNbBktQD6QBb2UgBY"
    }
    
    // Render API Configuration
    object Render {
        // Render deployment URL - update this when you deploy to Render
        const val BASE_URL = "https://menu-ocr-f4mr.onrender.com"
        
        // API endpoints
        const val OCR_ENDPOINT = "/ocr/process"
        const val DISHES_ENDPOINT = "/dishes/extract"
        const val PAYMENTS_ENDPOINT = "/payments"
        const val HEALTH_ENDPOINT = "/health"
        const val USER_PREFERENCES_ENDPOINT = "/user/preferences"
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
}
