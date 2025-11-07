//
//  AuthViewModel.swift
//  MenuOCR
//
//  Created by MenuOCR on 2025-01-07.
//

import Foundation
import Combine

class AuthViewModel: ObservableObject {
    @Published var authState: AuthState = .idle

    private let supabaseService = SupabaseService.shared

    init() {
        checkCurrentUser()
    }

    private func checkCurrentUser() {
        if let user = supabaseService.getCurrentUser() {
            authState = .authenticated(user)
        } else {
            authState = .unauthenticated
        }
    }

    func signInWithEmail(email: String, password: String) {
        authState = .loading

        Task {
            do {
                let user = try await supabaseService.signInWithEmail(email: email, password: password)
                await MainActor.run {
                    authState = .authenticated(user)
                }
            } catch {
                await MainActor.run {
                    authState = .error(error.localizedDescription)
                }
            }
        }
    }

    func signUpWithEmail(email: String, password: String) {
        authState = .loading

        Task {
            do {
                let user = try await supabaseService.signUpWithEmail(email: email, password: password)
                await MainActor.run {
                    authState = .authenticated(user)
                }
            } catch {
                await MainActor.run {
                    authState = .error(error.localizedDescription)
                }
            }
        }
    }

    func signInWithGoogle() {
        authState = .loading

        Task {
            do {
                let user = try await supabaseService.signInWithGoogle()
                await MainActor.run {
                    authState = .authenticated(user)
                }
            } catch {
                await MainActor.run {
                    authState = .error(error.localizedDescription)
                }
            }
        }
    }

    func signOut() {
        authState = .loading

        Task {
            do {
                try await supabaseService.signOut()
                await MainActor.run {
                    authState = .unauthenticated
                }
            } catch {
                await MainActor.run {
                    authState = .error(error.localizedDescription)
                }
            }
        }
    }

    func resetPassword(email: String) {
        authState = .loading

        Task {
            // Note: Password reset would need to be implemented in SupabaseService
            await MainActor.run {
                authState = .passwordResetSent
            }
        }
    }
}