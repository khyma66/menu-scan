//
//  ProfileViewController.swift
//  MenuOCR
//
//  Created by MenuOCR on 2025-01-07.
//

import UIKit
import Combine

class ProfileViewController: UIViewController {

    private let authViewModel = AuthViewModel()
    private let apiService = ApiService()
    private var cancellables = Set<AnyCancellable>()

    private let nameLabel: UILabel = {
        let label = UILabel()
        label.font = .systemFont(ofSize: 18, weight: .semibold)
        label.textAlignment = .center
        return label
    }()

    private let emailLabel: UILabel = {
        let label = UILabel()
        label.font = .systemFont(ofSize: 16)
        label.textColor = .secondaryLabel
        label.textAlignment = .left
        return label
    }()

    private let userIdLabel: UILabel = {
        let label = UILabel()
        label.font = .systemFont(ofSize: 12)
        label.textColor = .tertiaryLabel
        label.textAlignment = .left
        label.numberOfLines = 0
        return label
    }()

    private let createdAtLabel: UILabel = {
        let label = UILabel()
        label.font = .systemFont(ofSize: 14)
        label.textAlignment = .left
        return label
    }()

    private let lastSignInLabel: UILabel = {
        let label = UILabel()
        label.font = .systemFont(ofSize: 14)
        label.textAlignment = .left
        return label
    }()

    private let signOutButton: UIButton = {
        let button = UIButton(type: .system)
        button.setTitle("Sign Out", for: .normal)
        button.backgroundColor = .systemRed
        button.setTitleColor(.white, for: .normal)
        button.layer.cornerRadius = 8
        return button
    }()

    private let backButton: UIButton = {
        let button = UIButton(type: .system)
        button.setTitle("Back", for: .normal)
        button.setTitleColor(.systemBlue, for: .normal)
        return button
    }()

    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
        setupBindings()
        loadUserProfile()
    }

    private func setupUI() {
        view.backgroundColor = .systemBackground
        title = "Profile"

        let stackView = UIStackView(arrangedSubviews: [
            nameLabel,
            emailLabel,
            userIdLabel,
            createdAtLabel,
            lastSignInLabel,
            signOutButton,
            backButton
        ])
        stackView.axis = .vertical
        stackView.spacing = 16
        stackView.translatesAutoresizingMaskIntoConstraints = false

        view.addSubview(stackView)

        NSLayoutConstraint.activate([
            stackView.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            stackView.centerYAnchor.constraint(equalTo: view.centerYAnchor),
            stackView.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 32),
            stackView.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -32)
        ])

        signOutButton.addTarget(self, action: #selector(signOutTapped), for: .touchUpInside)
        backButton.addTarget(self, action: #selector(backTapped), for: .touchUpInside)
    }

    private func setupBindings() {
        authViewModel.$authState
            .receive(on: DispatchQueue.main)
            .sink { [weak self] state in
                switch state {
                case .unauthenticated:
                    self?.navigateToLogin()
                case .error(let message):
                    self?.showError(message)
                default:
                    break
                }
            }
            .store(in: &cancellables)
    }

    private func loadUserProfile() {
        if case .authenticated(let user) = authViewModel.authState {
            displayUserInfo(user)
        }
    }

    private func displayUserInfo(_ user: User) {
        nameLabel.text = user.name ?? "User"
        emailLabel.text = user.email
        userIdLabel.text = "ID: \(user.id)"

        // Format dates
        let dateFormatter = DateFormatter()
        dateFormatter.dateStyle = .medium

        if let createdAt = user.createdAt {
            createdAtLabel.text = "Member since: \(createdAt)"
        } else {
            createdAtLabel.text = "Member since: Recently"
        }

        lastSignInLabel.text = "Last sign in: Recently"

        Task {
            do {
                // Keep backend profile details in sync for cross-device profile consistency
                _ = try await apiService.updateAppProfile(
                    request: AppProfileDetailsRequest(
                        full_name: user.name,
                        email: user.email,
                        contact: nil,
                        phone: nil,
                        country: nil
                    )
                )

                let appProfile = try await apiService.getAppProfile()
                await MainActor.run {
                    nameLabel.text = appProfile.full_name ?? user.name ?? "User"
                    emailLabel.text = appProfile.email ?? user.email
                }
            } catch {
                // Profile sync failed — show local data, display subtle warning
                print("Profile sync error: \(error.localizedDescription)")
            }
        }
    }

    private func navigateToLogin() {
        dismiss(animated: true) {
            // Post notification so the app can show login screen
            NotificationCenter.default.post(name: Notification.Name("UserDidSignOut"), object: nil)
        }
    }

    private func showError(_ message: String) {
        let alert = UIAlertController(title: "Error", message: message, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "OK", style: .default))
        present(alert, animated: true)
    }

    @objc private func signOutTapped() {
        authViewModel.signOut()
    }

    @objc private func backTapped() {
        dismiss(animated: true)
    }
}