import Foundation

class ApiService {
    let baseURL: String = AppConfig.MenuOcrApi.useLocal ? 
        AppConfig.MenuOcrApi.localBaseURL : AppConfig.MenuOcrApi.baseURL
    let session = URLSession.shared
    
    // MARK: - OCR Processing
    
    func processOcr(request: OcrRequest) async throws -> MenuResponse {
        return try await RetryHelper.retry {
            let url = URL(string: "\(self.baseURL)/ocr/process")!
            var urlRequest = URLRequest(url: url)
            urlRequest.httpMethod = "POST"
            urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
            
            if let authToken = await self.getAuthToken() {
                urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
            }
            
            let jsonData = try JSONEncoder().encode(request)
            urlRequest.httpBody = jsonData
            
            let (data, response) = try await self.session.data(for: urlRequest)
            
            guard let httpResponse = response as? HTTPURLResponse,
                  httpResponse.statusCode == 200 else {
                throw ApiError.invalidResponse
            }
            
            return try JSONDecoder().decode(MenuResponse.self, from: data)
        }
    }
    
    func processOcrBatch(requests: [OcrRequest]) async throws -> [MenuResponse] {
        let url = URL(string: "\(baseURL)/ocr/batch")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }
        
        let jsonData = try JSONEncoder().encode(requests)
        urlRequest.httpBody = jsonData
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        
        return try JSONDecoder().decode([MenuResponse].self, from: data)
    }
    
    // MARK: - Dish Extraction
    
    func extractDishes(request: DishRequest) async throws -> DishResponse {
        return try await RetryHelper.retry {
            let url = URL(string: "\(self.baseURL)/dishes/extract")!
            var urlRequest = URLRequest(url: url)
            urlRequest.httpMethod = "POST"
            urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
            
            if let authToken = await self.getAuthToken() {
                urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
            }
            
            let jsonData = try JSONEncoder().encode(request)
            urlRequest.httpBody = jsonData
            
            let (data, response) = try await self.session.data(for: urlRequest)
            
            guard let httpResponse = response as? HTTPURLResponse,
                  httpResponse.statusCode == 200 else {
                throw ApiError.invalidResponse
            }
            
            return try JSONDecoder().decode(DishResponse.self, from: data)
        }
    }
    
    // MARK: - Table Extraction (Qwen AI)
    
    func extractTable(request: TableExtractionRequest) async throws -> TableExtractionResponse {
        let url = URL(string: "\(baseURL)/table-extraction/extract")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }
        
        let jsonData = try JSONEncoder().encode(request)
        urlRequest.httpBody = jsonData
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        
        return try JSONDecoder().decode(TableExtractionResponse.self, from: data)
    }
    
    func extractTableFromOCR(ocrText: String, imageUrl: String?) async throws -> TableExtractionResponse {
        let url = URL(string: "\(baseURL)/table-extraction/extract-from-ocr")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }
        
        let requestDict: [String: Any] = [
            "ocr_text": ocrText,
            "image_url": imageUrl as Any
        ]
        
        let jsonData = try JSONSerialization.data(withJSONObject: requestDict)
        urlRequest.httpBody = jsonData
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        
        return try JSONDecoder().decode(TableExtractionResponse.self, from: data)
    }
    
    // MARK: - Health Conditions
    
    func getHealthConditions() async throws -> [HealthCondition] {
        let url = URL(string: "\(baseURL)/health-conditions")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "GET"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        
        return try JSONDecoder().decode([HealthCondition].self, from: data)
    }
    
    func addHealthCondition(request: HealthConditionRequest) async throws -> HealthCondition {
        let url = URL(string: "\(baseURL)/health-conditions")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }
        
        let jsonData = try JSONEncoder().encode(request)
        urlRequest.httpBody = jsonData
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        
        return try JSONDecoder().decode(HealthCondition.self, from: data)
    }
    
    // MARK: - Payment Processing
    
    func createPaymentIntent(request: PaymentIntentRequest) async throws -> PaymentIntentResponse {
        return try await RetryHelper.retry {
            let url = URL(string: "\(self.baseURL)/payments/create-payment-intent")!
            var urlRequest = URLRequest(url: url)
            urlRequest.httpMethod = "POST"
            urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
            
            if let authToken = await self.getAuthToken() {
                urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
            }
            
            let jsonData = try JSONEncoder().encode(request)
            urlRequest.httpBody = jsonData
            
            let (data, response) = try await self.session.data(for: urlRequest)
            
            guard let httpResponse = response as? HTTPURLResponse,
                  httpResponse.statusCode == 200 else {
                throw ApiError.invalidResponse
            }
            
            return try JSONDecoder().decode(PaymentIntentResponse.self, from: data)
        }
    }
    
    func getPaymentHistory() async throws -> PaymentHistoryResponse {
        return try await RetryHelper.retry {
            let url = URL(string: "\(self.baseURL)/payments/history")!
            var urlRequest = URLRequest(url: url)
            urlRequest.httpMethod = "GET"
            urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
            
            if let authToken = await self.getAuthToken() {
                urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
            }
            
            let (data, response) = try await self.session.data(for: urlRequest)
            
            guard let httpResponse = response as? HTTPURLResponse,
                  httpResponse.statusCode == 200 else {
                throw ApiError.invalidResponse
            }
            
            return try JSONDecoder().decode(PaymentHistoryResponse.self, from: data)
        }
    }
    
    // MARK: - User Preferences
    
    func addFoodPreference(request: FoodPreferenceRequest) async throws -> FoodPreference {
        let url = URL(string: "\(baseURL)/user/preferences/food-preferences")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }
        
        let jsonData = try JSONEncoder().encode(request)
        urlRequest.httpBody = jsonData
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        
        return try JSONDecoder().decode(FoodPreference.self, from: data)
    }
    
    func getFoodPreferences() async throws -> [FoodPreference] {
        let url = URL(string: "\(baseURL)/user/preferences/food-preferences")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "GET"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        
        return try JSONDecoder().decode([FoodPreference].self, from: data)
    }
    
    func updateUserProfile(request: UserProfileUpdateRequest) async throws -> UserPreferences {
        let url = URL(string: "\(baseURL)/user/preferences/profile")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "PUT"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }
        
        let jsonData = try JSONEncoder().encode(request)
        urlRequest.httpBody = jsonData
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        
        return try JSONDecoder().decode(UserPreferences.self, from: data)
    }
    
    func getUserProfile() async throws -> UserPreferences {
        let url = URL(string: "\(baseURL)/user/preferences/profile")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "GET"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        
        return try JSONDecoder().decode(UserPreferences.self, from: data)
    }

    // MARK: - App Profile + Discovery

    func getAppProfile() async throws -> AppProfileDetails {
        let url = URL(string: "\(baseURL)/user/app-profile")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "GET"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }

        let (data, response) = try await session.data(for: urlRequest)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }

        return try JSONDecoder().decode(AppProfileDetails.self, from: data)
    }

    func updateAppProfile(request: AppProfileDetailsRequest) async throws -> AppProfileDetails {
        let url = URL(string: "\(baseURL)/user/app-profile")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "PUT"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }

        urlRequest.httpBody = try JSONEncoder().encode(request)
        let (data, response) = try await session.data(for: urlRequest)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }

        return try JSONDecoder().decode(AppProfileDetails.self, from: data)
    }

    func getDiscoveryPreferences() async throws -> DiscoveryPreferences {
        let url = URL(string: "\(baseURL)/user/discovery-preferences")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "GET"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }

        let (data, response) = try await session.data(for: urlRequest)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }

        return try JSONDecoder().decode(DiscoveryPreferences.self, from: data)
    }

    func updateDiscoveryPreferences(request: DiscoveryPreferencesRequest) async throws -> DiscoveryPreferences {
        let url = URL(string: "\(baseURL)/user/discovery-preferences")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "PUT"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }

        urlRequest.httpBody = try JSONEncoder().encode(request)
        let (data, response) = try await session.data(for: urlRequest)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }

        return try JSONDecoder().decode(DiscoveryPreferences.self, from: data)
    }
    
    // MARK: - Authentication
    
    func getAuthToken() async -> String? {
        // Get auth token from local storage
        return UserDefaults.standard.string(forKey: "auth_token")
    }
    
    func testApiConnection() async -> Bool {
        let url = URL(string: "\(baseURL)/health")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "GET"
        
        do {
            let (_, response) = try await session.data(for: urlRequest)
            return (response as? HTTPURLResponse)?.statusCode == 200
        } catch {
            return false
        }
    }
    
    enum ApiError: Error, LocalizedError {
        case invalidResponse
        case networkError(Error)
        case decodingError(Error)
        case authenticationRequired
        case serverError(String)
        
        var errorDescription: String? {
            switch self {
            case .invalidResponse:
                return "Invalid response from server"
            case .networkError(let error):
                return "Network error: \(error.localizedDescription)"
            case .decodingError(let error):
                return "Data decoding error: \(error.localizedDescription)"
            case .authenticationRequired:
                return "Authentication required"
            case .serverError(let message):
                return "Server error: \(message)"
            }
        }
    }
}
