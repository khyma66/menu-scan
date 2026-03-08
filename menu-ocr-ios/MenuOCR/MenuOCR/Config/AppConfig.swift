import Foundation

/// Application configuration for API endpoints and keys
/// All hardcoded values are centralized here for easy configuration
enum AppConfig {
    
    // MARK: - Supabase Configuration
    enum Supabase {
        // Supabase project URL (used only for Apple Sign In OAuth redirect)
        static let url = "https://jlfqzcaospvspmzbvbxd.supabase.co"
        // NOTE: Anon key removed — all auth now proxied via the CF Worker backend.
        // This avoids the Supabase April 2026 anon-key deprecation for auth endpoints.
    }
    
    // MARK: - Menu OCR API Configuration (Cloudflare Workers)
    enum MenuOcrApi {
        // Production backend URL — Cloudflare Worker
        static let baseURL = "https://menu-ocr-backend.varunchinna5966.workers.dev"
        
        // Local development URL (for simulator testing)
        static let localBaseURL = "http://localhost:8000"
        
        // Toggle between local and production
        static let useLocal = false
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