import Foundation

// MARK: - Core Models

struct Dish: Codable, Identifiable, Equatable {
    let id: String
    let name: String
    let price: Double?
    let description: String?
    let ingredients: [String]?
    let dietaryInfo: [String]?

    enum CodingKeys: String, CodingKey {
        case id, name, price, description, ingredients, dietaryInfo
    }
}

struct Menu: Codable {
    let dishes: [Dish]
}

struct OcrRequest: Codable {
    let image_base64: String
    let language: String = "en"
}

struct MenuResponse: Codable {
    let text: String
    let language: String
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
    let userId: String
    let foodPreferences: [FoodPreference]
    let dietaryRestrictions: [String]
    let favoriteCuisines: [String]
    let spiceTolerance: String?
    let budgetPreference: String?
    let healthConditions: [String]?
    let updatedAt: String?
    
    enum CodingKeys: String, CodingKey {
        case userId, foodPreferences, dietaryRestrictions, favoriteCuisines, spiceTolerance, budgetPreference, healthConditions, updatedAt
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

// MARK: - Translation Models

struct TranslationRequest: Codable {
    let text: String
    let targetLanguage: String
    let sourceLanguage: String?
}

struct TranslationResponse: Codable {
    let translatedText: String
    let sourceLanguage: String
    let targetLanguage: String
    let confidence: Float?
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