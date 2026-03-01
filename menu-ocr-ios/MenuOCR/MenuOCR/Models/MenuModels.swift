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
    let ingredients: [String]?
    let taste: String?
    let similarDish1: String?
    let similarDish2: String?
    let recommendation: String?
    let recommendation_reason: String?
    let allergens: [String]?
    let spiciness_level: String?
    let preparation_method: String?

    init(name: String, price: String? = nil, description: String? = nil, category: String? = nil,
         ingredients: [String]? = nil, taste: String? = nil, similarDish1: String? = nil,
         similarDish2: String? = nil, recommendation: String? = nil, recommendation_reason: String? = nil,
         allergens: [String]? = nil, spiciness_level: String? = nil, preparation_method: String? = nil) {
        self.id = UUID().uuidString
        self.name = name
        self.price = price
        self.description = description
        self.category = category
        self.ingredients = ingredients
        self.taste = taste
        self.similarDish1 = similarDish1
        self.similarDish2 = similarDish2
        self.recommendation = recommendation
        self.recommendation_reason = recommendation_reason
        self.allergens = allergens
        self.spiciness_level = spiciness_level
        self.preparation_method = preparation_method
    }
    
    enum CodingKeys: String, CodingKey {
        case id, name, price, description, category, ingredients, taste
        case similarDish1, similarDish2, recommendation, recommendation_reason
        case allergens, spiciness_level, preparation_method
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decodeIfPresent(String.self, forKey: .id)
        name = try container.decode(String.self, forKey: .name)
        description = try container.decodeIfPresent(String.self, forKey: .description)
        category = try container.decodeIfPresent(String.self, forKey: .category)
        ingredients = try container.decodeIfPresent([String].self, forKey: .ingredients)
        taste = try container.decodeIfPresent(String.self, forKey: .taste)
        similarDish1 = try container.decodeIfPresent(String.self, forKey: .similarDish1)
        similarDish2 = try container.decodeIfPresent(String.self, forKey: .similarDish2)
        recommendation = try container.decodeIfPresent(String.self, forKey: .recommendation)
        recommendation_reason = try container.decodeIfPresent(String.self, forKey: .recommendation_reason)
        allergens = try container.decodeIfPresent([String].self, forKey: .allergens)
        spiciness_level = try container.decodeIfPresent(String.self, forKey: .spiciness_level)
        preparation_method = try container.decodeIfPresent(String.self, forKey: .preparation_method)
        
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
        try container.encodeIfPresent(ingredients, forKey: .ingredients)
        try container.encodeIfPresent(taste, forKey: .taste)
        try container.encodeIfPresent(similarDish1, forKey: .similarDish1)
        try container.encodeIfPresent(similarDish2, forKey: .similarDish2)
        try container.encodeIfPresent(recommendation, forKey: .recommendation)
        try container.encodeIfPresent(recommendation_reason, forKey: .recommendation_reason)
        try container.encodeIfPresent(allergens, forKey: .allergens)
        try container.encodeIfPresent(spiciness_level, forKey: .spiciness_level)
        try container.encodeIfPresent(preparation_method, forKey: .preparation_method)
    }
}

struct MenuResponse: Codable {
    let success: Bool
    let menu_items: [MenuItem]
    let gemini_menu_items: [MenuItem]?
    let qwen_menu_items: [MenuItem]?
    let raw_text: String
    let processing_time_ms: Int
    let enhanced: Bool
    let cached: Bool
    let metadata: [String: String]?
}

struct TranslateMenuItemsRequest: Codable {
    let menu_items: [[String: AnyCodable]]
    let target_language: String
}

struct TranslateMenuItemsResponse: Codable {
    let menu_items: [[String: AnyCodable]]
}

/// Type-erased Codable wrapper for heterogeneous dictionaries
struct AnyCodable: Codable {
    let value: Any

    init(_ value: Any) {
        self.value = value
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let s = try? container.decode(String.self) { value = s }
        else if let i = try? container.decode(Int.self) { value = i }
        else if let d = try? container.decode(Double.self) { value = d }
        else if let b = try? container.decode(Bool.self) { value = b }
        else if let arr = try? container.decode([AnyCodable].self) { value = arr.map { $0.value } }
        else if let dict = try? container.decode([String: AnyCodable].self) {
            value = dict.mapValues { $0.value }
        }
        else if container.decodeNil() { value = NSNull() }
        else { throw DecodingError.dataCorruptedError(in: container, debugDescription: "Unsupported type") }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        if let s = value as? String { try container.encode(s) }
        else if let i = value as? Int { try container.encode(i) }
        else if let d = value as? Double { try container.encode(d) }
        else if let b = value as? Bool { try container.encode(b) }
        else if let arr = value as? [Any] { try container.encode(arr.map { AnyCodable($0) }) }
        else if let dict = value as? [String: Any] {
            try container.encode(dict.mapValues { AnyCodable($0) })
        }
        else { try container.encodeNil() }
    }
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