//
//  ProfileViewController.swift
//  MenuOCR
//
//  Profile tab: user info, subscription card, notifications, recent scans.
//  No privacy & security section.
//  Notifications & Recent Scans sync to Supabase per account.
//

import UIKit
import Combine

// MARK: - Models

struct ScanRecord: Codable {
    let id: String?
    let user_id: String?
    let image_key: String?
    let dish_count: Int?
    let status: String?
    let created_at: String?
}

struct NotificationRecord: Codable {
    let id: String?
    let user_id: String?
    let type: String?
    let title: String?
    let message: String?
    let read: Bool?
    let created_at: String?
}

// MARK: - ProfileViewController

class ProfileViewController: UIViewController {

    private let authViewModel = AuthViewModel()
    private let apiService = ApiService()
    private var cancellables = Set<AnyCancellable>()

    // MARK: - Theme
    private let violetPrimary = UIColor(red: 0.486, green: 0.227, blue: 0.929, alpha: 1)
    private let violetBg = UIColor(red: 0.96, green: 0.94, blue: 1.0, alpha: 1)
    private let textDark = UIColor(red: 0.12, green: 0.12, blue: 0.14, alpha: 1)
    private let textMuted = UIColor(red: 0.45, green: 0.42, blue: 0.55, alpha: 1)

    // MARK: - UI Components
    private let scrollView = UIScrollView()
    private let contentView = UIView()
    private let headerView = UIView()
    private let titleLabel = UILabel()

    // User info
    private let avatarLabel = UILabel()
    private let nameLabel = UILabel()
    private let emailLabel = UILabel()

    // Subscription card
    private let subscriptionCard = UIView()
    private let planNameLabel = UILabel()
    private let planStatusLabel = UILabel()
    private let managePlanButton = UIButton(type: .system)

    // Notifications section
    private let notificationsHeader = UILabel()
    private let notificationsStack = UIStackView()
    private let noNotificationsLabel = UILabel()

    // Recent scans section
    private let recentScansHeader = UILabel()
    private let recentScansStack = UIStackView()
    private let noScansLabel = UILabel()

    // Sign out
    private let signOutButton = UIButton(type: .system)

    // Data
    private var notifications: [NotificationRecord] = []
    private var recentScans: [ScanRecord] = []

    // MARK: - Lifecycle

    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
        setupConstraints()
        setupBindings()
        loadUserProfile()
    }

    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        refreshSubscriptionCard()
        loadNotifications()
        loadRecentScans()
    }

    // MARK: - UI Setup

    private func setupUI() {
        view.backgroundColor = violetBg

        // Header
        headerView.backgroundColor = violetPrimary
        headerView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(headerView)

        let statusBarBg = UIView()
        statusBarBg.backgroundColor = violetPrimary
        statusBarBg.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(statusBarBg)
        NSLayoutConstraint.activate([
            statusBarBg.topAnchor.constraint(equalTo: view.topAnchor),
            statusBarBg.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            statusBarBg.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            statusBarBg.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
        ])

        titleLabel.text = "Profile"
        titleLabel.font = .systemFont(ofSize: 20, weight: .bold)
        titleLabel.textColor = .white
        titleLabel.textAlignment = .center
        titleLabel.translatesAutoresizingMaskIntoConstraints = false
        headerView.addSubview(titleLabel)

        // Scroll view
        scrollView.translatesAutoresizingMaskIntoConstraints = false
        contentView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(scrollView)
        scrollView.addSubview(contentView)

        setupUserInfoSection()
        setupSubscriptionSection()
        setupNotificationsSection()
        setupRecentScansSection()
        setupSignOutButton()
    }

    private func setupUserInfoSection() {
        // Avatar circle
        avatarLabel.text = "👤"
        avatarLabel.font = .systemFont(ofSize: 40)
        avatarLabel.textAlignment = .center
        avatarLabel.backgroundColor = violetPrimary.withAlphaComponent(0.12)
        avatarLabel.layer.cornerRadius = 36
        avatarLabel.clipsToBounds = true
        avatarLabel.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(avatarLabel)

        nameLabel.text = "Loading..."
        nameLabel.font = .systemFont(ofSize: 20, weight: .bold)
        nameLabel.textColor = textDark
        nameLabel.textAlignment = .center
        nameLabel.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(nameLabel)

        emailLabel.text = ""
        emailLabel.font = .systemFont(ofSize: 14)
        emailLabel.textColor = textMuted
        emailLabel.textAlignment = .center
        emailLabel.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(emailLabel)
    }

    private func setupSubscriptionSection() {
        subscriptionCard.backgroundColor = .white
        subscriptionCard.layer.cornerRadius = 16
        subscriptionCard.layer.shadowColor = violetPrimary.cgColor
        subscriptionCard.layer.shadowOffset = CGSize(width: 0, height: 4)
        subscriptionCard.layer.shadowOpacity = 0.1
        subscriptionCard.layer.shadowRadius = 12
        subscriptionCard.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(subscriptionCard)

        let subLabel = UILabel()
        subLabel.text = "Subscription"
        subLabel.font = .systemFont(ofSize: 12, weight: .semibold)
        subLabel.textColor = textMuted
        subLabel.translatesAutoresizingMaskIntoConstraints = false
        subscriptionCard.addSubview(subLabel)

        planNameLabel.text = "Free Plan"
        planNameLabel.font = .systemFont(ofSize: 22, weight: .bold)
        planNameLabel.textColor = textDark
        planNameLabel.translatesAutoresizingMaskIntoConstraints = false
        subscriptionCard.addSubview(planNameLabel)

        planStatusLabel.text = "Active"
        planStatusLabel.font = .systemFont(ofSize: 13, weight: .medium)
        planStatusLabel.textColor = .systemGreen
        planStatusLabel.translatesAutoresizingMaskIntoConstraints = false
        subscriptionCard.addSubview(planStatusLabel)

        managePlanButton.setTitle("Manage Plan", for: .normal)
        managePlanButton.setTitleColor(.white, for: .normal)
        managePlanButton.titleLabel?.font = .systemFont(ofSize: 14, weight: .bold)
        managePlanButton.backgroundColor = violetPrimary
        managePlanButton.layer.cornerRadius = 12
        managePlanButton.addTarget(self, action: #selector(managePlanTapped), for: .touchUpInside)
        managePlanButton.translatesAutoresizingMaskIntoConstraints = false
        subscriptionCard.addSubview(managePlanButton)

        NSLayoutConstraint.activate([
            subLabel.topAnchor.constraint(equalTo: subscriptionCard.topAnchor, constant: 16),
            subLabel.leadingAnchor.constraint(equalTo: subscriptionCard.leadingAnchor, constant: 16),

            planNameLabel.topAnchor.constraint(equalTo: subLabel.bottomAnchor, constant: 4),
            planNameLabel.leadingAnchor.constraint(equalTo: subscriptionCard.leadingAnchor, constant: 16),

            planStatusLabel.centerYAnchor.constraint(equalTo: planNameLabel.centerYAnchor),
            planStatusLabel.leadingAnchor.constraint(equalTo: planNameLabel.trailingAnchor, constant: 8),

            managePlanButton.topAnchor.constraint(equalTo: planNameLabel.bottomAnchor, constant: 12),
            managePlanButton.leadingAnchor.constraint(equalTo: subscriptionCard.leadingAnchor, constant: 16),
            managePlanButton.trailingAnchor.constraint(equalTo: subscriptionCard.trailingAnchor, constant: -16),
            managePlanButton.heightAnchor.constraint(equalToConstant: 40),
            managePlanButton.bottomAnchor.constraint(equalTo: subscriptionCard.bottomAnchor, constant: -16),
        ])
    }

    private func setupNotificationsSection() {
        notificationsHeader.text = "🔔 Notifications"
        notificationsHeader.font = .systemFont(ofSize: 17, weight: .bold)
        notificationsHeader.textColor = textDark
        notificationsHeader.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(notificationsHeader)

        notificationsStack.axis = .vertical
        notificationsStack.spacing = 8
        notificationsStack.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(notificationsStack)

        noNotificationsLabel.text = "No notifications yet"
        noNotificationsLabel.font = .systemFont(ofSize: 14)
        noNotificationsLabel.textColor = textMuted
        noNotificationsLabel.textAlignment = .center
        noNotificationsLabel.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(noNotificationsLabel)
    }

    private func setupRecentScansSection() {
        recentScansHeader.text = "📷 Recent Scans"
        recentScansHeader.font = .systemFont(ofSize: 17, weight: .bold)
        recentScansHeader.textColor = textDark
        recentScansHeader.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(recentScansHeader)

        recentScansStack.axis = .vertical
        recentScansStack.spacing = 8
        recentScansStack.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(recentScansStack)

        noScansLabel.text = "No scans yet"
        noScansLabel.font = .systemFont(ofSize: 14)
        noScansLabel.textColor = textMuted
        noScansLabel.textAlignment = .center
        noScansLabel.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(noScansLabel)
    }

    private func setupSignOutButton() {
        signOutButton.setTitle("Sign Out", for: .normal)
        signOutButton.setTitleColor(.white, for: .normal)
        signOutButton.titleLabel?.font = .systemFont(ofSize: 16, weight: .bold)
        signOutButton.backgroundColor = .systemRed
        signOutButton.layer.cornerRadius = 12
        signOutButton.addTarget(self, action: #selector(signOutTapped), for: .touchUpInside)
        signOutButton.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(signOutButton)
    }

    // MARK: - Constraints

    private func setupConstraints() {
        NSLayoutConstraint.activate([
            headerView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            headerView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            headerView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            headerView.heightAnchor.constraint(equalToConstant: 50),

            titleLabel.centerXAnchor.constraint(equalTo: headerView.centerXAnchor),
            titleLabel.centerYAnchor.constraint(equalTo: headerView.centerYAnchor),

            scrollView.topAnchor.constraint(equalTo: headerView.bottomAnchor),
            scrollView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            scrollView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            scrollView.bottomAnchor.constraint(equalTo: view.bottomAnchor),

            contentView.topAnchor.constraint(equalTo: scrollView.topAnchor),
            contentView.leadingAnchor.constraint(equalTo: scrollView.leadingAnchor),
            contentView.trailingAnchor.constraint(equalTo: scrollView.trailingAnchor),
            contentView.bottomAnchor.constraint(equalTo: scrollView.bottomAnchor),
            contentView.widthAnchor.constraint(equalTo: scrollView.widthAnchor),

            // Avatar
            avatarLabel.topAnchor.constraint(equalTo: contentView.topAnchor, constant: 24),
            avatarLabel.centerXAnchor.constraint(equalTo: contentView.centerXAnchor),
            avatarLabel.widthAnchor.constraint(equalToConstant: 72),
            avatarLabel.heightAnchor.constraint(equalToConstant: 72),

            nameLabel.topAnchor.constraint(equalTo: avatarLabel.bottomAnchor, constant: 10),
            nameLabel.centerXAnchor.constraint(equalTo: contentView.centerXAnchor),

            emailLabel.topAnchor.constraint(equalTo: nameLabel.bottomAnchor, constant: 4),
            emailLabel.centerXAnchor.constraint(equalTo: contentView.centerXAnchor),

            // Subscription card
            subscriptionCard.topAnchor.constraint(equalTo: emailLabel.bottomAnchor, constant: 20),
            subscriptionCard.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            subscriptionCard.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),

            // Notifications
            notificationsHeader.topAnchor.constraint(equalTo: subscriptionCard.bottomAnchor, constant: 24),
            notificationsHeader.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),

            notificationsStack.topAnchor.constraint(equalTo: notificationsHeader.bottomAnchor, constant: 8),
            notificationsStack.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            notificationsStack.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),

            noNotificationsLabel.topAnchor.constraint(equalTo: notificationsStack.bottomAnchor, constant: 8),
            noNotificationsLabel.centerXAnchor.constraint(equalTo: contentView.centerXAnchor),

            // Recent Scans
            recentScansHeader.topAnchor.constraint(equalTo: noNotificationsLabel.bottomAnchor, constant: 24),
            recentScansHeader.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),

            recentScansStack.topAnchor.constraint(equalTo: recentScansHeader.bottomAnchor, constant: 8),
            recentScansStack.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            recentScansStack.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),

            noScansLabel.topAnchor.constraint(equalTo: recentScansStack.bottomAnchor, constant: 8),
            noScansLabel.centerXAnchor.constraint(equalTo: contentView.centerXAnchor),

            // Sign out
            signOutButton.topAnchor.constraint(equalTo: noScansLabel.bottomAnchor, constant: 32),
            signOutButton.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            signOutButton.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            signOutButton.heightAnchor.constraint(equalToConstant: 48),
            signOutButton.bottomAnchor.constraint(equalTo: contentView.bottomAnchor, constant: -40),
        ])
    }

    // MARK: - Bindings

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

    // MARK: - Data Loading

    private func loadUserProfile() {
        if case .authenticated(let user) = authViewModel.authState {
            nameLabel.text = user.name ?? "User"
            emailLabel.text = user.email
        }

        Task {
            do {
                let profile = try await apiService.getAppProfile()
                await MainActor.run {
                    nameLabel.text = profile.full_name ?? nameLabel.text
                    emailLabel.text = profile.email ?? emailLabel.text
                }
            } catch {
                #if DEBUG
                print("Profile load error: \(error.localizedDescription)")
                #endif
            }
        }
    }

    private func refreshSubscriptionCard() {
        let limiter = ScanLimitManager.shared
        let plan = limiter.planName
        switch plan {
        case "pro":
            planNameLabel.text = "Pro Plan"
            planStatusLabel.text = "Active"
            planStatusLabel.textColor = .systemBlue
        case "max":
            planNameLabel.text = "Max Plan"
            planStatusLabel.text = "Active"
            planStatusLabel.textColor = UIColor(red: 0.85, green: 0.65, blue: 0.13, alpha: 1)
        default:
            planNameLabel.text = "Free Plan"
            let remaining = limiter.remainingFreeScans
            planStatusLabel.text = "\(remaining) scan\(remaining == 1 ? "" : "s") left"
            planStatusLabel.textColor = remaining > 0 ? .systemGreen : .systemRed
        }
    }

    private func loadNotifications() {
        Task {
            do {
                let result = try await apiService.getNotifications()
                await MainActor.run {
                    notifications = result
                    renderNotifications()
                }
            } catch {
                await MainActor.run { renderNotifications() }
            }
        }
    }

    private func loadRecentScans() {
        Task {
            do {
                let result = try await apiService.getRecentScans()
                await MainActor.run {
                    recentScans = result
                    renderRecentScans()
                }
            } catch {
                await MainActor.run { renderRecentScans() }
            }
        }
    }

    // MARK: - Render Data

    private func renderNotifications() {
        notificationsStack.arrangedSubviews.forEach { $0.removeFromSuperview() }
        noNotificationsLabel.isHidden = !notifications.isEmpty

        for notif in notifications.prefix(10) {
            let card = makeNotificationRow(notif)
            notificationsStack.addArrangedSubview(card)
        }
    }

    private func makeNotificationRow(_ n: NotificationRecord) -> UIView {
        let row = UIView()
        row.backgroundColor = .white
        row.layer.cornerRadius = 12
        row.translatesAutoresizingMaskIntoConstraints = false
        row.heightAnchor.constraint(greaterThanOrEqualToConstant: 56).isActive = true

        let icon = UILabel()
        icon.text = n.type == "payment" ? "💳" : "📷"
        icon.font = .systemFont(ofSize: 22)
        icon.translatesAutoresizingMaskIntoConstraints = false
        row.addSubview(icon)

        let titleLbl = UILabel()
        titleLbl.text = n.title ?? (n.type == "payment" ? "Payment" : "Scan")
        titleLbl.font = .systemFont(ofSize: 14, weight: .semibold)
        titleLbl.textColor = textDark
        titleLbl.translatesAutoresizingMaskIntoConstraints = false
        row.addSubview(titleLbl)

        let msgLbl = UILabel()
        msgLbl.text = n.message ?? ""
        msgLbl.font = .systemFont(ofSize: 12)
        msgLbl.textColor = textMuted
        msgLbl.numberOfLines = 2
        msgLbl.translatesAutoresizingMaskIntoConstraints = false
        row.addSubview(msgLbl)

        NSLayoutConstraint.activate([
            icon.leadingAnchor.constraint(equalTo: row.leadingAnchor, constant: 12),
            icon.centerYAnchor.constraint(equalTo: row.centerYAnchor),
            icon.widthAnchor.constraint(equalToConstant: 28),

            titleLbl.topAnchor.constraint(equalTo: row.topAnchor, constant: 10),
            titleLbl.leadingAnchor.constraint(equalTo: icon.trailingAnchor, constant: 10),
            titleLbl.trailingAnchor.constraint(equalTo: row.trailingAnchor, constant: -12),

            msgLbl.topAnchor.constraint(equalTo: titleLbl.bottomAnchor, constant: 2),
            msgLbl.leadingAnchor.constraint(equalTo: titleLbl.leadingAnchor),
            msgLbl.trailingAnchor.constraint(equalTo: row.trailingAnchor, constant: -12),
            msgLbl.bottomAnchor.constraint(equalTo: row.bottomAnchor, constant: -10),
        ])

        return row
    }

    private func renderRecentScans() {
        recentScansStack.arrangedSubviews.forEach { $0.removeFromSuperview() }
        noScansLabel.isHidden = !recentScans.isEmpty

        for scan in recentScans.prefix(10) {
            let card = makeScanRow(scan)
            recentScansStack.addArrangedSubview(card)
        }
    }

    private func makeScanRow(_ scan: ScanRecord) -> UIView {
        let row = UIView()
        row.backgroundColor = .white
        row.layer.cornerRadius = 12
        row.translatesAutoresizingMaskIntoConstraints = false
        row.heightAnchor.constraint(equalToConstant: 52).isActive = true

        let icon = UILabel()
        icon.text = "📸"
        icon.font = .systemFont(ofSize: 20)
        icon.translatesAutoresizingMaskIntoConstraints = false
        row.addSubview(icon)

        let titleLbl = UILabel()
        let dishes = scan.dish_count ?? 0
        titleLbl.text = "\(dishes) dish\(dishes == 1 ? "" : "es") found"
        titleLbl.font = .systemFont(ofSize: 14, weight: .semibold)
        titleLbl.textColor = textDark
        titleLbl.translatesAutoresizingMaskIntoConstraints = false
        row.addSubview(titleLbl)

        let dateLbl = UILabel()
        dateLbl.text = formatDate(scan.created_at)
        dateLbl.font = .systemFont(ofSize: 12)
        dateLbl.textColor = textMuted
        dateLbl.translatesAutoresizingMaskIntoConstraints = false
        row.addSubview(dateLbl)

        let statusLbl = UILabel()
        statusLbl.text = (scan.status ?? "done").capitalized
        statusLbl.font = .systemFont(ofSize: 11, weight: .medium)
        statusLbl.textColor = .systemGreen
        statusLbl.translatesAutoresizingMaskIntoConstraints = false
        row.addSubview(statusLbl)

        NSLayoutConstraint.activate([
            icon.leadingAnchor.constraint(equalTo: row.leadingAnchor, constant: 12),
            icon.centerYAnchor.constraint(equalTo: row.centerYAnchor),

            titleLbl.leadingAnchor.constraint(equalTo: icon.trailingAnchor, constant: 10),
            titleLbl.centerYAnchor.constraint(equalTo: row.centerYAnchor, constant: -8),

            dateLbl.leadingAnchor.constraint(equalTo: titleLbl.leadingAnchor),
            dateLbl.topAnchor.constraint(equalTo: titleLbl.bottomAnchor, constant: 2),

            statusLbl.trailingAnchor.constraint(equalTo: row.trailingAnchor, constant: -12),
            statusLbl.centerYAnchor.constraint(equalTo: row.centerYAnchor),
        ])

        return row
    }

    private func formatDate(_ dateStr: String?) -> String {
        guard let ds = dateStr else { return "" }
        let df = ISO8601DateFormatter()
        df.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let date = df.date(from: ds) {
            let out = DateFormatter()
            out.dateStyle = .medium
            out.timeStyle = .short
            return out.string(from: date)
        }
        // Try without fractional seconds
        df.formatOptions = [.withInternetDateTime]
        if let date = df.date(from: ds) {
            let out = DateFormatter()
            out.dateStyle = .medium
            out.timeStyle = .short
            return out.string(from: date)
        }
        return String(ds.prefix(16))
    }

    // MARK: - Actions

    @objc private func managePlanTapped() {
        let paywall = PaywallViewController()
        paywall.modalPresentationStyle = .fullScreen
        present(paywall, animated: true)
    }

    @objc private func signOutTapped() {
        authViewModel.signOut()
    }

    private func navigateToLogin() {
        if let presenting = presentingViewController {
            presenting.dismiss(animated: true) {
                NotificationCenter.default.post(name: Notification.Name("UserDidSignOut"), object: nil)
            }
        } else {
            NotificationCenter.default.post(name: Notification.Name("UserDidSignOut"), object: nil)
        }
    }

    private func showError(_ message: String) {
        let alert = UIAlertController(title: "Error", message: message, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "OK", style: .default))
        present(alert, animated: true)
    }
}

// MARK: - ApiService Extensions for Notifications & Recent Scans

extension ApiService {

    func getNotifications() async throws -> [NotificationRecord] {
        let url = URL(string: "\(baseURL)/user/notifications")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token = await getAuthToken() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
            return []
        }
        struct Wrapper: Codable { let notifications: [NotificationRecord]? }
        let w = try? JSONDecoder().decode(Wrapper.self, from: data)
        return w?.notifications ?? []
    }

    func getRecentScans() async throws -> [ScanRecord] {
        let url = URL(string: "\(baseURL)/user/recent-scans")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token = await getAuthToken() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
            return []
        }
        struct Wrapper: Codable { let scans: [ScanRecord]? }
        let w = try? JSONDecoder().decode(Wrapper.self, from: data)
        return w?.scans ?? []
    }

    func recordScanToServer(dishCount: Int) async throws {
        let url = URL(string: "\(baseURL)/user/recent-scans")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token = await getAuthToken() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        let body: [String: Any] = ["dish_count": dishCount, "status": "done"]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        _ = try await session.data(for: request)
    }
}
