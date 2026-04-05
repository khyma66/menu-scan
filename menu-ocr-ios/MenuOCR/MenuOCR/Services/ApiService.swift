import Foundation

class ApiService {
    let baseURL: String = AppConfig.MenuOcrApi.useLocal ? 
        AppConfig.MenuOcrApi.localBaseURL : AppConfig.MenuOcrApi.baseURL
    let session = URLSession.shared
    
    // MARK: - OCR Processing (Multipart Upload — primary endpoint)
    
    func processOcrUpload(imageData: Data, useLlmEnhancement: Bool = true, language: String = "auto", outputLanguage: String = "en") async throws -> MenuResponse {
        let url = URL(string: "\(baseURL)/ocr/process-upload")!
        let boundary = "Boundary-\(UUID().uuidString)"
        
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        urlRequest.timeoutInterval = 120 // long timeout for Gemini+Groq pipeline
        
        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }
        
        var body = Data()
        
        // Image file part
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"image\"; filename=\"menu.jpg\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
        body.append(imageData)
        body.append("\r\n".data(using: .utf8)!)
        
        // use_llm_enhancement
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"use_llm_enhancement\"\r\n\r\n".data(using: .utf8)!)
        body.append("\(useLlmEnhancement)\r\n".data(using: .utf8)!)
        
        // language
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"language\"\r\n\r\n".data(using: .utf8)!)
        body.append("\(language)\r\n".data(using: .utf8)!)
        
        // output_language
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"output_language\"\r\n\r\n".data(using: .utf8)!)
        body.append("\(outputLanguage)\r\n".data(using: .utf8)!)
        
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        urlRequest.httpBody = body
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw ApiError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            // Try to parse error detail
            if let errorDict = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let detail = errorDict["detail"] as? String {
                throw ApiError.serverError(detail)
            }
            throw ApiError.invalidResponse
        }
        
        return try JSONDecoder().decode(MenuResponse.self, from: data)
    }
    
    // MARK: - Translation
    
    func translateMenuItems(items: [[String: AnyCodable]], targetLanguage: String) async throws -> [[String: AnyCodable]] {
        let url = URL(string: "\(baseURL)/ocr/translate-menu-items")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        urlRequest.timeoutInterval = 60
        
        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }
        
        let request = TranslateMenuItemsRequest(menu_items: items, target_language: targetLanguage)
        urlRequest.httpBody = try JSONEncoder().encode(request)
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        
        let result = try JSONDecoder().decode(TranslateMenuItemsResponse.self, from: data)
        return result.menu_items
    }
    
    // MARK: - OCR Processing (Legacy base64 — kept for compatibility)
    
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

    // MARK: - V1 Async Scan Pipeline

    func scanMenu(imageData: [Data], targetLang: String = "en", userCountry: String = "US", restaurantName: String = "", region: String = "", cuisineType: String = "") async throws -> ScanMenuResponse {
        let url = URL(string: "\(baseURL)/v1/menus:scan")!
        let boundary = "Boundary-\(UUID().uuidString)"

        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        urlRequest.timeoutInterval = 120

        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }

        var body = Data()

        // Image parts
        for (index, data) in imageData.enumerated() {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"pages\"; filename=\"page\(index).jpg\"\r\n".data(using: .utf8)!)
            body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
            body.append(data)
            body.append("\r\n".data(using: .utf8)!)
        }

        // Form fields
        let fields: [(String, String)] = [
            ("target_lang", targetLang),
            ("user_country", userCountry),
            ("restaurant_name", restaurantName),
            ("region", region),
            ("cuisine_type", cuisineType)
        ]
        for (name, value) in fields {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"\(name)\"\r\n\r\n".data(using: .utf8)!)
            body.append("\(value)\r\n".data(using: .utf8)!)
        }

        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        urlRequest.httpBody = body

        let (data, response) = try await session.data(for: urlRequest)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        return try JSONDecoder().decode(ScanMenuResponse.self, from: data)
    }

    func getJobStatus(jobId: String) async throws -> JobStatusResponse {
        let url = URL(string: "\(baseURL)/v1/jobs/\(jobId)")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "GET"

        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }

        let (data, response) = try await session.data(for: urlRequest)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        return try JSONDecoder().decode(JobStatusResponse.self, from: data)
    }

    func getPersonalizedMenu(menuId: String) async throws -> PersonalizedMenuResponse {
        let url = URL(string: "\(baseURL)/v1/menus/\(menuId)/personalized")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "GET"

        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }

        let (data, response) = try await session.data(for: urlRequest)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        return try JSONDecoder().decode(PersonalizedMenuResponse.self, from: data)
    }

    // MARK: - V1 Health Profile (Legacy Compat)

    func getHealthProfile() async throws -> HealthProfileResponse {
        let url = URL(string: "\(baseURL)/v1/user/health-profile")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "GET"

        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }

        let (data, response) = try await session.data(for: urlRequest)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        return try JSONDecoder().decode(HealthProfileResponse.self, from: data)
    }

    func updateHealthProfile(request: HealthProfileRequest) async throws -> HealthProfileResponse {
        let url = URL(string: "\(baseURL)/v1/user/health-profile")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "PUT"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }

        urlRequest.httpBody = try JSONEncoder().encode(request)
        let (data, response) = try await session.data(for: urlRequest)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        return try JSONDecoder().decode(HealthProfileResponse.self, from: data)
    }

    // MARK: - User Menus

    func getUserMenus() async throws -> UserMenusResponse {
        let url = URL(string: "\(baseURL)/v1/user/menus")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "GET"

        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }

        let (data, response) = try await session.data(for: urlRequest)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        return try JSONDecoder().decode(UserMenusResponse.self, from: data)
    }

    // MARK: - Account Deletion

    func deleteUserAccount() async throws {
        let url = URL(string: "\(baseURL)/v1/user/account")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "DELETE"

        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }

        let (_, response) = try await session.data(for: urlRequest)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
    }

    // MARK: - Password Reset

    func requestPasswordReset(email: String) async throws {
        let url = URL(string: "\(baseURL)/auth/reset-password")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = ["email": email]
        urlRequest.httpBody = try JSONEncoder().encode(body)

        let (_, response) = try await session.data(for: urlRequest)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
    }

    // MARK: - Food Preference Deletion

    func removeFoodPreference(id: String) async throws {
        let url = URL(string: "\(baseURL)/user/preferences/food-preferences/\(id)")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "DELETE"

        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }

        let (_, response) = try await session.data(for: urlRequest)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
    }

    // MARK: - Recent Scans

    func getRecentScans(days: Int = 30, limit: Int = 50) async throws -> RecentScansListResponse {
        let url = URL(string: "\(baseURL)/user/recent-scans?days=\(days)&limit=\(limit)")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "GET"

        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }

        let (data, response) = try await session.data(for: urlRequest)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        return try JSONDecoder().decode(RecentScansListResponse.self, from: data)
    }

    func getDailyScans(days: Int = 7) async throws -> DailyScansListResponse {
        let url = URL(string: "\(baseURL)/user/recent-scans/daily?days=\(days)")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "GET"

        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }

        let (data, response) = try await session.data(for: urlRequest)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        return try JSONDecoder().decode(DailyScansListResponse.self, from: data)
    }

    // MARK: - Saved Cards

    func getSavedCards() async throws -> SavedCardsResponse {
        let url = URL(string: "\(baseURL)/user/saved-cards")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "GET"

        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }

        let (data, response) = try await session.data(for: urlRequest)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        return try JSONDecoder().decode(SavedCardsResponse.self, from: data)
    }

    func saveCard(request: SaveCardRequest) async throws -> SavedCard {
        let url = URL(string: "\(baseURL)/user/saved-cards")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }

        urlRequest.httpBody = try JSONEncoder().encode(request)
        let (data, response) = try await session.data(for: urlRequest)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        return try JSONDecoder().decode(SavedCard.self, from: data)
    }

    // MARK: - User Payment History

    func getUserPaymentHistory() async throws -> UserPaymentHistoryResponse {
        let url = URL(string: "\(baseURL)/user/payment-history")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "GET"

        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }

        let (data, response) = try await session.data(for: urlRequest)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        return try JSONDecoder().decode(UserPaymentHistoryResponse.self, from: data)
    }

    // MARK: - Subscription Management

    func getSubscriptionPlans() async throws -> SubscriptionPlansResponse {
        let url = URL(string: "\(baseURL)/user/subscription/plans")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "GET"

        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }

        let (data, response) = try await session.data(for: urlRequest)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        return try JSONDecoder().decode(SubscriptionPlansResponse.self, from: data)
    }

    func getSubscriptionInfo() async throws -> UserSubscriptionStatus {
        let url = URL(string: "\(baseURL)/user/subscription")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "GET"

        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }

        let (data, response) = try await session.data(for: urlRequest)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        return try JSONDecoder().decode(UserSubscriptionStatus.self, from: data)
    }

    func selectSubscriptionPlan(planName: String) async throws -> UserSubscriptionStatus {
        let url = URL(string: "\(baseURL)/user/subscription/select")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "PUT"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }

        let request = SelectSubscriptionPlanRequest(plan_name: planName)
        urlRequest.httpBody = try JSONEncoder().encode(request)

        let (data, response) = try await session.data(for: urlRequest)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        return try JSONDecoder().decode(UserSubscriptionStatus.self, from: data)
    }

    func getCustomerPortal() async throws -> CustomerPortalResponse {
        let url = URL(string: "\(baseURL)/subscriptions/customer-portal")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"

        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }

        let (data, response) = try await session.data(for: urlRequest)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        return try JSONDecoder().decode(CustomerPortalResponse.self, from: data)
    }

    func getSubscriptionStatus() async throws -> SubscriptionStatusResponse {
        let url = URL(string: "\(baseURL)/subscriptions/status")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "GET"

        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }

        let (data, response) = try await session.data(for: urlRequest)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        return try JSONDecoder().decode(SubscriptionStatusResponse.self, from: data)
    }

    // MARK: - Stripe Checkout

    struct CheckoutResponse: Codable {
        let success: Bool
        let checkout_url: String?
        let session_id: String?
        let plan: String?
        let fallback: Bool?
    }

    func createCheckoutSession(plan: String) async throws -> CheckoutResponse {
        let url = URL(string: "\(baseURL)/stripe/create-checkout-session")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        urlRequest.timeoutInterval = 30

        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }

        let body: [String: String] = ["plan": plan]
        urlRequest.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await session.data(for: urlRequest)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }

        return try JSONDecoder().decode(CheckoutResponse.self, from: data)
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
                return "Something went wrong. Please try again."
            case .networkError:
                return "Please check your internet connection and try again."
            case .decodingError:
                return "We had trouble reading the results. Please try again."
            case .authenticationRequired:
                return "Please sign in to continue."
            case .serverError:
                return "We're having trouble processing your request. Please try again in a moment."
            }
        }
    }
}
