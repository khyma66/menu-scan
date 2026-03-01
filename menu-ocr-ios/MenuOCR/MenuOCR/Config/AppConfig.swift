import Foundation

/// Application configuration for API endpoints and keys
/// All hardcoded values are centralized here for easy configuration
enum AppConfig {
    
    // MARK: - Supabase Configuration
    enum Supabase {
        // Supabase project URL
        static let url = "https://jlfqzcaospvspmzbvbxd.supabase.co"
        
        // Supabase anon/public key - safe for client apps
        // Get from: https://supabase.com/dashboard/project/_/settings/api
        static let anonKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpsZnF6Y2Fvc3B2c3BtemJ2YnhkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEzNzAzMzYsImV4cCI6MjA3Njk0NjMzNn0.5xdkvyJSsza79Iz3kiASMEE22WhNbBktQD6QBb2UgBY"
    }
    
    // MARK: - Menu OCR API Configuration
    enum MenuOcrApi {
        // Production backend URL
        static let baseURL = "https://menu-ocr-f4mr.onrender.com"
        
        // Local development URL (for simulator testing)
        static let localBaseURL = "http://localhost:8000"
        
        // Toggle between local and production
        static let useLocal = true
    }
    
    // MARK: - Overpass API Configuration (OpenStreetMap POI data)
    enum Overpass {
        static let baseURL = "https://overpass-api.de/api"
        static let interpreterEndpoint = "/interpreter"
        static let defaultSearchRadius = 500 // meters
        static let timeoutSeconds = 25
    }
    
    // MARK: - OpenStreetMap Configuration
    enum OSM {
        static let tileURL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        static let attribution = "© OpenStreetMap contributors"
        static let mapStyleURL = "https://demotiles.maplibre.org/style.json"
    }
    
    // MARK: - Stripe Configuration
    enum Stripe {
        // Replace with your actual Stripe publishable key
        static let publishableKey = "pk_test_51SWk8N1HFXSHAnudIASPucwXm6GPQdWk52CfSUXVC71R5rVLjQ3TFySSfJr6NNg1azeJ54PpVAhJog0QXdE2vPjI00tTJMuDZD"
    }
    
    // MARK: - Feature Flags
    enum Features {
        static let enableOfflineMode = false
        static let enableAnalytics = true
        static let enableCrashReporting = true
    }
    
    // MARK: - Timeouts (in seconds)
    enum Timeouts {
        static let connectTimeout: TimeInterval = 30
        static let readTimeout: TimeInterval = 60
        static let writeTimeout: TimeInterval = 60
    }
    
    // MARK: - Retry Configuration
    enum Retry {
        static let enabled = true
        static let delaySeconds: TimeInterval = 10
        static let maxAttempts = 3
        static let backoffMultiplier = 1.0
    }
}