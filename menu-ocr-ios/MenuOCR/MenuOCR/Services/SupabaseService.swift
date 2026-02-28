//
//  SupabaseService.swift
//  MenuOCR
//
//  Created by MenuOCR on 2025-01-07.
//

import Foundation
import AuthenticationServices

class SupabaseService: NSObject {
    static let shared = SupabaseService()
    
    private var session: URLSession!
    private let supabaseURL: URL
    private let supabaseKey: String
    
    private var currentUser: User?
    private var accessToken: String?
    
    // Apple Sign In callback
    private var appleSignInCompletion: ((Result<User, Error>) -> Void)?
    
    private override init() {
        supabaseURL = URL(string: AppConfig.Supabase.url)!
        supabaseKey = AppConfig.Supabase.anonKey
        super.init()
        
        // Configure URLSession with proper SSL handling
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 60
        config.waitsForConnectivity = true
        config.requestCachePolicy = .reloadIgnoringLocalCacheData
        session = URLSession(configuration: config, delegate: self, delegateQueue: nil)
        
        loadStoredSession()
    }
    
    private func loadStoredSession() {
        if let token = UserDefaults.standard.string(forKey: "supabase_access_token") {
            self.accessToken = token
        }
        if let userData = UserDefaults.standard.data(forKey: "supabase_user"),
           let user = try? JSONDecoder().decode(User.self, from: userData) {
            self.currentUser = user
        }
    }
    
    private func storeSession(user: User, accessToken: String) {
        self.currentUser = user
        self.accessToken = accessToken
        UserDefaults.standard.set(accessToken, forKey: "supabase_access_token")
        if let userData = try? JSONEncoder().encode(user) {
            UserDefaults.standard.set(userData, forKey: "supabase_user")
        }
    }
    
    private func clearSession() {
        currentUser = nil
        accessToken = nil
        UserDefaults.standard.removeObject(forKey: "supabase_access_token")
        UserDefaults.standard.removeObject(forKey: "supabase_user")
    }
    
    private func formatDate(_ date: Date) -> String {
        let formatter = ISO8601DateFormatter()
        return formatter.string(from: date)
    }

    // MARK: - Authentication methods
    
    func signInWithEmail(email: String, password: String) async throws -> User {
        let url = URL(string: "\(supabaseURL.absoluteString)/auth/v1/token?grant_type=password")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue(supabaseKey, forHTTPHeaderField: "apikey")
        
        let body: [String: String] = [
            "email": email,
            "password": password
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw NSError(domain: "SupabaseService", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid response"])
        }
        
        guard httpResponse.statusCode == 200 else {
            let errorMessage = String(data: data, encoding: .utf8) ?? "Unknown error"
            throw NSError(domain: "SupabaseService", code: httpResponse.statusCode, userInfo: [NSLocalizedDescriptionKey: parseErrorMessage(errorMessage)])
        }
        
        let authResponse = try JSONDecoder().decode(SupabaseAuthResponse.self, from: data)
        let user = User(
            id: authResponse.user.id,
            email: authResponse.user.email ?? email,
            name: authResponse.user.userMetadata?["name"] as? String,
            createdAt: authResponse.user.createdAt ?? formatDate(Date())
        )
        
        guard let token = authResponse.access_token else {
            throw NSError(domain: "SupabaseService", code: -1, userInfo: [NSLocalizedDescriptionKey: "No access token in response"])
        }
        storeSession(user: user, accessToken: token)
        return user
    }

    func signUpWithEmail(email: String, password: String) async throws -> User {
        let url = URL(string: "\(supabaseURL.absoluteString)/auth/v1/signup")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue(supabaseKey, forHTTPHeaderField: "apikey")
        
        let body: [String: String] = [
            "email": email,
            "password": password
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw NSError(domain: "SupabaseService", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid response"])
        }
        
        guard httpResponse.statusCode == 200 else {
            let errorMessage = String(data: data, encoding: .utf8) ?? "Unknown error"
            throw NSError(domain: "SupabaseService", code: httpResponse.statusCode, userInfo: [NSLocalizedDescriptionKey: parseErrorMessage(errorMessage)])
        }
        
        let authResponse = try JSONDecoder().decode(SupabaseAuthResponse.self, from: data)
        let user = User(
            id: authResponse.user.id,
            email: authResponse.user.email ?? email,
            name: authResponse.user.userMetadata?["name"] as? String,
            createdAt: authResponse.user.createdAt ?? formatDate(Date())
        )
        
        if let token = authResponse.access_token, !token.isEmpty {
            storeSession(user: user, accessToken: token)
        }
        
        return user
    }
    
    private func parseErrorMessage(_ json: String) -> String {
        guard let data = json.data(using: .utf8),
              let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            return json
        }
        
        if let msg = dict["msg"] as? String {
            return msg
        }
        if let error = dict["error"] as? String {
            return error
        }
        if let errorDescription = dict["error_description"] as? String {
            return errorDescription
        }
        if let message = dict["message"] as? String {
            return message
        }
        return json
    }

    func signInWithGoogle() async throws -> User {
        throw NSError(domain: "SupabaseService", code: -1, userInfo: [NSLocalizedDescriptionKey: "Google Sign In requires GoogleSignIn SDK setup"])
    }

    // MARK: - Apple Sign In
    
    func signInWithApple() async throws -> User {
        return try await withCheckedThrowingContinuation { continuation in
            Task { @MainActor in
                let provider = ASAuthorizationAppleIDProvider()
                let request = provider.createRequest()
                request.requestedScopes = [.fullName, .email]
                
                let controller = ASAuthorizationController(authorizationRequests: [request])
                controller.delegate = self
                controller.performRequests()
                
                self.appleSignInCompletion = { result in
                    switch result {
                    case .success(let user):
                        continuation.resume(returning: user)
                    case .failure(let error):
                        continuation.resume(throwing: error)
                    }
                }
            }
        }
    }
    
    private func handleAppleSignInResult(authorization: ASAuthorization) async {
        guard let appleIDCredential = authorization.credential as? ASAuthorizationAppleIDCredential else {
            appleSignInCompletion?(.failure(NSError(domain: "SupabaseService", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid Apple credential"])))
            return
        }
        
        guard let identityTokenData = appleIDCredential.identityToken,
              let identityTokenString = String(data: identityTokenData, encoding: .utf8) else {
            appleSignInCompletion?(.failure(NSError(domain: "SupabaseService", code: -1, userInfo: [NSLocalizedDescriptionKey: "Unable to get identity token"])))
            return
        }
        
        do {
            let user = try await signInWithAppleToken(token: identityTokenString, credential: appleIDCredential)
            appleSignInCompletion?(.success(user))
        } catch {
            appleSignInCompletion?(.failure(error))
        }
    }
    
    private func signInWithAppleToken(token: String, credential: ASAuthorizationAppleIDCredential) async throws -> User {
        let url = URL(string: "\(supabaseURL.absoluteString)/auth/v1/token?grant_type=apple")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue(supabaseKey, forHTTPHeaderField: "apikey")
        
        var body: [String: Any] = [
            "identity_token": token
        ]
        
        // Add user's name if available (first sign-in)
        if let fullName = credential.fullName {
            var nameParts: [String] = []
            if let givenName = fullName.givenName, !givenName.isEmpty {
                nameParts.append(givenName)
            }
            if let familyName = fullName.familyName, !familyName.isEmpty {
                nameParts.append(familyName)
            }
            if !nameParts.isEmpty {
                body["user_metadata"] = ["name": nameParts.joined(separator: " ")]
            }
        }
        
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw NSError(domain: "SupabaseService", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid response"])
        }
        
        guard httpResponse.statusCode == 200 else {
            let errorMessage = String(data: data, encoding: .utf8) ?? "Unknown error"
            throw NSError(domain: "SupabaseService", code: httpResponse.statusCode, userInfo: [NSLocalizedDescriptionKey: parseErrorMessage(errorMessage)])
        }
        
        let authResponse = try JSONDecoder().decode(SupabaseAuthResponse.self, from: data)
        
        // Get email from credential or response, fallback to apple user identifier
        let email = credential.email ?? authResponse.user.email ?? "apple_\(credential.user)@privaterelay.appleid.com"
        
        let user = User(
            id: authResponse.user.id,
            email: email,
            name: authResponse.user.userMetadata?["name"] as? String,
            createdAt: authResponse.user.createdAt ?? formatDate(Date())
        )
        
        guard let accessToken = authResponse.access_token else {
            throw NSError(domain: "SupabaseService", code: -1, userInfo: [NSLocalizedDescriptionKey: "No access token in response"])
        }
        
        storeSession(user: user, accessToken: accessToken)
        return user
    }

    func signOut() async throws {
        let url = URL(string: "\(supabaseURL.absoluteString)/auth/v1/logout")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(accessToken ?? "")", forHTTPHeaderField: "Authorization")
        request.setValue(supabaseKey, forHTTPHeaderField: "apikey")
        
        _ = try? await session.data(for: request)
        clearSession()
    }

    func getCurrentUser() -> User? {
        return currentUser
    }

    func isAuthenticated() -> Bool {
        return currentUser != nil && accessToken != nil
    }
    
    func getAccessToken() -> String? {
        return accessToken
    }
    
    func resetPassword(email: String) async throws {
        let url = URL(string: "\(supabaseURL.absoluteString)/auth/v1/recover")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue(supabaseKey, forHTTPHeaderField: "apikey")
        
        let body: [String: String] = ["email": email]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        let (_, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw NSError(domain: "SupabaseService", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid response"])
        }
        
        guard httpResponse.statusCode == 200 else {
            throw NSError(domain: "SupabaseService", code: httpResponse.statusCode, userInfo: [NSLocalizedDescriptionKey: "Failed to send reset email"])
        }
    }
}

// MARK: - URLSessionDelegate for SSL handling

extension SupabaseService: URLSessionDelegate {
    func urlSession(_ session: URLSession, didReceive challenge: URLAuthenticationChallenge, completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void) {
        // Handle SSL certificate validation
        if challenge.protectionSpace.authenticationMethod == NSURLAuthenticationMethodServerTrust {
            guard let serverTrust = challenge.protectionSpace.serverTrust else {
                completionHandler(.performDefaultHandling, nil)
                return
            }
            
            // For Supabase URLs, perform default validation
            if challenge.protectionSpace.host.hasSuffix("supabase.co") {
                let credential = URLCredential(trust: serverTrust)
                completionHandler(.useCredential, credential)
            } else {
                completionHandler(.performDefaultHandling, nil)
            }
        } else {
            completionHandler(.performDefaultHandling, nil)
        }
    }
}

// MARK: - ASAuthorizationControllerDelegate

extension SupabaseService: ASAuthorizationControllerDelegate {
    
    func authorizationController(controller: ASAuthorizationController, didCompleteWithAuthorization authorization: ASAuthorization) {
        Task { @MainActor in
            await handleAppleSignInResult(authorization: authorization)
        }
    }
    
    func authorizationController(controller: ASAuthorizationController, didCompleteWithError error: Error) {
        Task { @MainActor in
            appleSignInCompletion?(.failure(error))
        }
    }
}

// MARK: - Response Models

private struct SupabaseAuthResponse: Codable {
    let access_token: String?
    let token_type: String?
    let expires_in: Int?
    let refresh_token: String?
    let user: SupabaseUser
}

private struct SupabaseUser: Codable {
    let id: String
    let email: String?
    let created_at: String?
    let user_metadata: [String: AnyCodable]?
    
    var createdAt: String? { created_at }
    var userMetadata: [String: Any]? {
        user_metadata?.reduce(into: [String: Any]()) { result, pair in
            result[pair.key] = pair.value.value
        }
    }
    
    enum CodingKeys: String, CodingKey {
        case id, email
        case created_at = "created_at"
        case user_metadata = "user_metadata"
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(String.self, forKey: .id)
        email = try container.decodeIfPresent(String.self, forKey: .email)
        created_at = try container.decodeIfPresent(String.self, forKey: .created_at)
        
        // Handle user_metadata as a dictionary
        if let metadataContainer = try? container.nestedContainer(keyedBy: AnyCodingKey.self, forKey: .user_metadata) {
            var metadata: [String: AnyCodable] = [:]
            for key in metadataContainer.allKeys {
                if let value = try? metadataContainer.decode(AnyCodable.self, forKey: key) {
                    metadata[key.stringValue] = value
                }
            }
            user_metadata = metadata
        } else {
            user_metadata = nil
        }
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(id, forKey: .id)
        try container.encodeIfPresent(email, forKey: .email)
        try container.encodeIfPresent(created_at, forKey: .created_at)
    }
}

private struct AnyCodingKey: CodingKey {
    var stringValue: String
    var intValue: Int?
    
    init?(stringValue: String) {
        self.stringValue = stringValue
        self.intValue = nil
    }
    
    init?(intValue: Int) {
        self.stringValue = String(intValue)
        self.intValue = intValue
    }
}

private struct AnyCodable: Codable {
    let value: Any
    
    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        
        if let string = try? container.decode(String.self) {
            value = string
        } else if let int = try? container.decode(Int.self) {
            value = int
        } else if let double = try? container.decode(Double.self) {
            value = double
        } else if let bool = try? container.decode(Bool.self) {
            value = bool
        } else {
            value = ""
        }
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        if let string = value as? String {
            try container.encode(string)
        } else if let int = value as? Int {
            try container.encode(int)
        } else if let double = value as? Double {
            try container.encode(double)
        } else if let bool = value as? Bool {
            try container.encode(bool)
        }
    }
}
