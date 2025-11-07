//
//  SupabaseService.swift
//  MenuOCR
//
//  Created by MenuOCR on 2025-01-07.
//

import Foundation
import Supabase

class SupabaseService {
    static let shared = SupabaseService()

    private let supabase: SupabaseClient

    private init() {
        supabase = SupabaseClient(
            supabaseURL: URL(string: "https://jlfqzcaospvspmzbvbxd.supabase.co")!,
            supabaseKey: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpsZnF6Y2Fvc3B2c3BtemJ2YnhkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTM3MDMzNiwiZXhwIjoyMDc2OTQ2MzM2fQ.5xdkvyJSsza79Iz3kiASMEE22WhNbBktQD6QBb2UgBY"
        )
    }

    var auth: Auth {
        supabase.auth
    }

    var database: PostgrestClient {
        supabase.database
    }

    var storage: SupabaseStorageClient {
        supabase.storage
    }

    // Authentication methods
    func signInWithEmail(email: String, password: String) async throws -> User {
        let authResponse = try await auth.signIn(email: email, password: password)
        return User(
            id: authResponse.user.id.uuidString,
            email: authResponse.user.email ?? "",
            name: authResponse.user.userMetadata?["name"] as? String
        )
    }

    func signUpWithEmail(email: String, password: String) async throws -> User {
        let authResponse = try await auth.signUp(email: email, password: password)
        return User(
            id: authResponse.user?.id.uuidString ?? "",
            email: authResponse.user?.email ?? "",
            name: authResponse.user?.userMetadata?["name"] as? String
        )
    }

    func signInWithGoogle() async throws -> User {
        // Note: Google sign-in requires additional setup in iOS
        // This is a placeholder for the implementation
        throw NSError(domain: "SupabaseService", code: -1, userInfo: [NSLocalizedDescriptionKey: "Google sign-in not implemented"])
    }

    func signOut() async throws {
        try await auth.signOut()
    }

    func getCurrentUser() -> User? {
        guard let user = auth.currentUser else { return nil }
        return User(
            id: user.id.uuidString,
            email: user.email ?? "",
            name: user.userMetadata?["name"] as? String
        )
    }

    func isAuthenticated() -> Bool {
        return auth.currentUser != nil
    }
}