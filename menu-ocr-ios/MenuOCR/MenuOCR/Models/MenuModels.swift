import Foundation

// MARK: - Core Models

struct Dish: Codable, Identifiable, Equatable {
    let id: String
    let name: String
    let price: String?
    let description: String?
    let ingredients: [String]?
    let dietaryInfo: [String]?

    enum CodingKeys: String, CodingKey {
        case id, name, price, description, ingredients, dietaryInfo
    }
    
    init(id: String = UUID().uuidString, name: String, price: String? = nil, description: String? = nil, ingredients: [String]? = nil, dietaryInfo: [String]? = nil) {
        self.id = id
        self.name = name
        self.price = price
        self.description = description
        self.ingredients = ingredients
        self.dietaryInfo = dietaryInfo
    }
}

struct Menu: Codable {
    let dishes: [Dish]
}

struct OcrRequest: Codable {
    let image_base64: String
    let language: String
    
    init(image_base64: String, language: String = "en") {
        self.image_base64 = image_base64
        self.language = language
    }
}

struct MenuItem: Codable, Identifiable {
    let id: String?
    let name: String
    let price: String?
    let description: String?
    let category: String?

    init(name: String, price: String? = nil, description: String? = nil, category: String? = nil) {
        self.id = UUID().uuidString
        self.name = name
        self.price = price
        self.description = description
        self.category = category
    }
    
    enum CodingKeys: String, CodingKey {
        case id, name, price, description, category
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decodeIfPresent(String.self, forKey: .id)
        name = try container.decode(String.self, forKey: .name)
        description = try container.decodeIfPresent(String.self, forKey: .description)
        category = try container.decodeIfPresent(String.self, forKey: .category)
        
        // Handle price that could be String, Int, or Double
        if let priceString = try? container.decode(String.self, forKey: .price) {
            price = priceString
        } else if let priceDouble = try? container.decode(Double.self, forKey: .price) {
            price = String(format: "%.2f", priceDouble)
        } else if let priceInt = try? container.decode(Int.self, forKey: .price) {
            price = String(priceInt)
        } else {
            price = nil
        }
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encodeIfPresent(id, forKey: .id)
        try container.encode(name, forKey: .name)
        try container.encodeIfPresent(price, forKey: .price)
        try container.encodeIfPresent(description, forKey: .description)
        try container.encodeIfPresent(category, forKey: .category)
    }
}

struct MenuResponse: Codable {
    let success: Bool
    let menu_items: [MenuItem]
    let raw_text: String
    let processing_time_ms: Int
    let enhanced: Bool
    let cached: Bool
    let metadata: [String: String]?
}

struct DishRequest: Codable {
    let text: String
    let language: String = "en"
}

struct DishResponse: Codable {
    let dishes: [Dish]
}

// MARK: - State Management

enum MenuState {
    case idle
    case loading
    case success(Menu)
    case error(String)
}

enum AuthState {
    case idle
    case loading
    case authenticated(User)
    case unauthenticated
    case passwordResetSent
    case error(String)
}

struct User: Codable, Identifiable {
    let id: String
    let email: String
    let name: String?
    let createdAt: String?
    
    enum CodingKeys: String, CodingKey {
        case id, email, name, createdAt
    }
    
    init(id: String, email: String, name: String? = nil, createdAt: String? = nil) {
        self.id = id
        self.email = email
        self.name = name
        self.createdAt = createdAt
    }
}

// MARK: - Health Conditions

struct HealthCondition: Codable, Identifiable {
    let id: String
    let userId: String
    let conditionType: String
    let severity: String?
    let description: String?
    let createdAt: String
    let updatedAt: String?
    
    enum CodingKeys: String, CodingKey {
        case id, userId, conditionType, severity, description, createdAt, updatedAt
    }
}

struct HealthConditionRequest: Codable {
    let condition_type: String
    let severity: String?
    let description: String?
}

// MARK: - Table Extraction (Qwen AI)

struct TableExtractionRequest: Codable {
    let text: String
    let format: String = "markdown"
    let source: String?
    let imageUrl: String?
    
    enum CodingKeys: String, CodingKey {
        case text, format, source, imageUrl
    }
}

struct TableExtractionResponse: Codable {
    let success: Bool
    let rawTable: String
    let format: String
    let modelUsed: String
    let tokensUsed: Int
    let promptTokens: Int?
    let completionTokens: Int?
    let processingTimeMs: Int?
    let timestamp: String
    let error: String?
    let tableId: String?
    
    enum CodingKeys: String, CodingKey {
        case success, rawTable, format, modelUsed, tokensUsed, promptTokens, completionTokens, processingTimeMs, timestamp, error, tableId
    }
}

struct BatchTableExtractionRequest: Codable {
    let items: [TableExtractionRequest]
}

struct BatchTableExtractionResponse: Codable {
    let results: [TableExtractionResponse]
    let totalTokens: Int
    let processingTimeMs: Int
}

// MARK: - User Preferences & Food Preferences

struct UserPreferences: Codable, Identifiable {
    let id: String
    let userId: String
    let foodPreferences: [FoodPreference]
    let dietaryRestrictions: [String]
    let favoriteCuisines: [String]
    let spiceTolerance: String?
    let budgetPreference: String?
    let healthConditions: [String]?
    let updatedAt: String?
    
    enum CodingKeys: String, CodingKey {
        case id, userId, foodPreferences, dietaryRestrictions, favoriteCuisines, spiceTolerance, budgetPreference, healthConditions, updatedAt
    }
    
    init(id: String = UUID().uuidString, userId: String, foodPreferences: [FoodPreference], dietaryRestrictions: [String], favoriteCuisines: [String], spiceTolerance: String? = nil, budgetPreference: String? = nil, healthConditions: [String]? = nil, updatedAt: String? = nil) {
        self.id = id
        self.userId = userId
        self.foodPreferences = foodPreferences
        self.dietaryRestrictions = dietaryRestrictions
        self.favoriteCuisines = favoriteCuisines
        self.spiceTolerance = spiceTolerance
        self.budgetPreference = budgetPreference
        self.healthConditions = healthConditions
        self.updatedAt = updatedAt
    }
}

struct FoodPreference: Codable, Identifiable, Equatable {
    let id: String
    let preferenceType: String
    let foodCategory: String
    let foodItem: String?
    let rating: Int
    let notes: String?
    let createdAt: String
    
    enum CodingKeys: String, CodingKey {
        case id, preferenceType, foodCategory, foodItem, rating, notes, createdAt
    }
}

struct FoodPreferenceRequest: Codable {
    let preference_type: String
    let food_category: String
    let food_item: String?
    let rating: Int
    let notes: String?
}

struct UserProfileUpdateRequest: Codable {
    let dietary_restrictions: [String]?
    let favorite_cuisines: [String]?
    let spice_tolerance: String?
    let budget_preference: String?
    let health_conditions: [String]?
}

struct AppProfileDetails: Codable {
    let user_id: String
    let full_name: String?
    let email: String?
    let contact: String?
    let phone: String?
    let country: String?
    let updated_at: String?
}

struct AppProfileDetailsRequest: Codable {
    let full_name: String?
    let email: String?
    let contact: String?
    let phone: String?
    let country: String?
}

struct DiscoveryPreferences: Codable {
    let user_id: String
    let search_radius_miles: Int
    let selected_cuisines: [String]
    let location_label: String?
    let latitude: Double?
    let longitude: Double?
    let updated_at: String?
}

struct DiscoveryPreferencesRequest: Codable {
    let search_radius_miles: Int
    let selected_cuisines: [String]
    let location_label: String?
    let latitude: Double?
    let longitude: Double?
}

// MARK: - Payment Models

struct PaymentIntentRequest: Codable {
    let amount: Int
    let currency: String
    let description: String?
    let metadata: [String: String]?

    init(amount: Int, currency: String = "usd", description: String? = nil, metadata: [String: String]? = nil) {
        self.amount = amount
        self.currency = currency
        self.description = description
        self.metadata = metadata
    }
}

struct PaymentIntentResponse: Codable {
    let client_secret: String
    let payment_intent_id: String
    let amount: Int
    let currency: String
    let status: String
}

struct PaymentHistoryResponse: Codable {
    let payment_intents: [PaymentIntent]
    let subscriptions: [Subscription]
}

struct PaymentIntent: Codable, Identifiable {
    let id: String
    let amount: Int
    let currency: String
    let status: String
    let created: Int
    let description: String?
}

struct Subscription: Codable, Identifiable {
    let id: String
    let status: String
    let current_period_start: Int
    let current_period_end: Int
    let items: [SubscriptionItem]
}

struct SubscriptionItem: Codable {
    let price: Price
}

struct Price: Codable, Identifiable {
    let id: String
    let nickname: String?
    let unit_amount: Int?
    let currency: String
}

// MARK: - API Response Models

struct ApiResponse<T: Codable>: Codable {
    let data: T?
    let message: String?
    let success: Bool
    let error: String?
}

struct HealthCheckResponse: Codable {
    let status: String
    let timestamp: String
    let version: String?
    let services: [String: String]?
}

// MARK: - Error Models

struct ApiErrorResponse: Codable {
    let error: String
    let message: String?
    let details: [String]?
    let timestamp: String
}

// MARK: - Extension for better JSON handling

extension Array where Element: Codable {
    func toJSON() -> [String: Any]? {
        guard let data = try? JSONEncoder().encode(self),
              let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            return nil
        }
        return dict
    }
}

extension Encodable {
    func toJSON() -> [String: Any]? {
        guard let data = try? JSONEncoder().encode(self),
              let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            return nil
        }
        return dict
    }
}