//
//  ProfileViewController.swift
//  MenuOCR
//
//  Account tab: sub-tabs for Profile, Payment, Recent Scans, Subscription.
//  Matches Android ProfileFragment layout and colors.
//

import UIKit
import Combine

// MARK: - ProfileTab enum

private enum ProfileTab: Int, CaseIterable {
    case profile = 0
    case payment
    case recentScans
    case subscription

    var title: String {
        switch self {
        case .profile: return "👤 Profile"
        case .payment: return "💳 Payment"
        case .recentScans: return "🧾 Recent Scans"
        case .subscription: return "⭐ Subscription"
        }
    }
}

// MARK: - ProfileViewController

class ProfileViewController: UIViewController {

    private let authViewModel = AuthViewModel()
    private let apiService = ApiService()
    private var cancellables = Set<AnyCancellable>()

    // MARK: - Theme (Android colors)
    private let headerPink = UIColor(red: 0.925, green: 0.286, blue: 0.6, alpha: 1) // #EC4899
    private let subtabActive = UIColor(red: 0.231, green: 0.357, blue: 0.859, alpha: 1) // #3B5BDB
    private let textDark = UIColor(red: 0.012, green: 0.008, blue: 0.075, alpha: 1) // #030213
    private let textMuted = UIColor(red: 0.443, green: 0.443, blue: 0.51, alpha: 1) // #717182
    private let dividerColor = UIColor(red: 0, green: 0, blue: 0, alpha: 0.1) // #0000001A
    private let pageBg = UIColor(red: 0.953, green: 0.953, blue: 0.961, alpha: 1) // #F3F3F5

    // MARK: - Active tab
    private var activeTab: ProfileTab = .profile

    // MARK: - UI Components
    private let scrollView = UIScrollView()
    private let contentView = UIView()
    private let headerView = UIView()
    private let titleLabel = UILabel()

    // Sub-tab buttons
    private let subtabScrollView = UIScrollView()
    private let subtabStack = UIStackView()
    private var subtabButtons: [UIButton] = []

    // Sections (each is a container view)
    private let profileSection = UIView()
    private let paymentSection = UIView()
    private let recentScansSection = UIView()
    private let subscriptionSection = UIView()

    // Profile section
    private let avatarLabel = UILabel()
    private let nameLabel = UILabel()
    private let emailLabel = UILabel()
    private let signOutButton = UIButton(type: .system)

    // Recent scans section
    private let recentScansStack = UIStackView()
    private let noScansLabel = UILabel()

    // Subscription section
    private let subscriptionCard = UIView()
    private let planNameLabel = UILabel()
    private let planStatusLabel = UILabel()
    private let managePlanButton = UIButton(type: .system)

    // Data
    private var recentScans: [RecentScan] = []

    // MARK: - Lifecycle

    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
        setupConstraints()
        setupBindings()
        loadUserProfile()
        selectTab(.profile)
    }

    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        refreshSubscriptionCard()
        loadRecentScans()
    }

    // MARK: - UI Setup

    private func setupUI() {
        view.backgroundColor = pageBg

        // Status bar bg
        let statusBarBg = UIView()
        statusBarBg.backgroundColor = headerPink
        statusBarBg.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(statusBarBg)
        NSLayoutConstraint.activate([
            statusBarBg.topAnchor.constraint(equalTo: view.topAnchor),
            statusBarBg.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            statusBarBg.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            statusBarBg.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
        ])

        // Header
        headerView.backgroundColor = headerPink
        headerView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(headerView)

        titleLabel.text = "Account"
        titleLabel.font = .systemFont(ofSize: 20, weight: .bold)
        titleLabel.textColor = .white
        titleLabel.textAlignment = .center
        titleLabel.translatesAutoresizingMaskIntoConstraints = false
        headerView.addSubview(titleLabel)

        // Sub-tab bar
        setupSubtabs()

        // Scroll view
        scrollView.translatesAutoresizingMaskIntoConstraints = false
        contentView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(scrollView)
        scrollView.addSubview(contentView)

        setupProfileSection()
        setupPaymentSection()
        setupRecentScansSection()
        setupSubscriptionSection()
    }

    // MARK: - Sub-tabs

    private func setupSubtabs() {
        subtabScrollView.showsHorizontalScrollIndicator = false
        subtabScrollView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(subtabScrollView)

        subtabStack.axis = .horizontal
        subtabStack.spacing = 8
        subtabStack.translatesAutoresizingMaskIntoConstraints = false
        subtabScrollView.addSubview(subtabStack)

        for tab in ProfileTab.allCases {
            let btn = UIButton(type: .system)
            btn.setTitle(tab.title, for: .normal)
            btn.titleLabel?.font = .systemFont(ofSize: 14, weight: .medium)
            btn.layer.cornerRadius = 12
            btn.contentEdgeInsets = UIEdgeInsets(top: 8, left: 16, bottom: 8, right: 16)
            btn.tag = tab.rawValue
            btn.addTarget(self, action: #selector(subtabTapped(_:)), for: .touchUpInside)
            btn.translatesAutoresizingMaskIntoConstraints = false
            btn.heightAnchor.constraint(equalToConstant: 40).isActive = true
            subtabStack.addArrangedSubview(btn)
            subtabButtons.append(btn)
        }
    }

    @objc private func subtabTapped(_ sender: UIButton) {
        guard let tab = ProfileTab(rawValue: sender.tag) else { return }
        selectTab(tab)
    }

    private func selectTab(_ tab: ProfileTab) {
        activeTab = tab

        // Update button appearance
        for btn in subtabButtons {
            let isSelected = btn.tag == tab.rawValue
            if isSelected {
                btn.backgroundColor = subtabActive
                btn.setTitleColor(.white, for: .normal)
            } else {
                btn.backgroundColor = .white
                btn.setTitleColor(textDark, for: .normal)
                btn.layer.borderWidth = 1
                btn.layer.borderColor = dividerColor.cgColor
            }
        }

        // Show/hide sections
        profileSection.isHidden = tab != .profile
        paymentSection.isHidden = tab != .payment
        recentScansSection.isHidden = tab != .recentScans
        subscriptionSection.isHidden = tab != .subscription
    }

    // MARK: - Profile Section

    private func setupProfileSection() {
        profileSection.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(profileSection)

        // Avatar circle
        avatarLabel.text = "👤"
        avatarLabel.font = .systemFont(ofSize: 40)
        avatarLabel.textAlignment = .center
        avatarLabel.backgroundColor = headerPink.withAlphaComponent(0.12)
        avatarLabel.layer.cornerRadius = 36
        avatarLabel.clipsToBounds = true
        avatarLabel.translatesAutoresizingMaskIntoConstraints = false
        profileSection.addSubview(avatarLabel)

        nameLabel.text = "Loading..."
        nameLabel.font = .systemFont(ofSize: 20, weight: .bold)
        nameLabel.textColor = textDark
        nameLabel.textAlignment = .center
        nameLabel.translatesAutoresizingMaskIntoConstraints = false
        profileSection.addSubview(nameLabel)

        emailLabel.text = ""
        emailLabel.font = .systemFont(ofSize: 14)
        emailLabel.textColor = textMuted
        emailLabel.textAlignment = .center
        emailLabel.translatesAutoresizingMaskIntoConstraints = false
        profileSection.addSubview(emailLabel)

        // Sign out
        signOutButton.setTitle("Sign Out", for: .normal)
        signOutButton.setTitleColor(.white, for: .normal)
        signOutButton.titleLabel?.font = .systemFont(ofSize: 16, weight: .bold)
        signOutButton.backgroundColor = .systemRed
        signOutButton.layer.cornerRadius = 12
        signOutButton.addTarget(self, action: #selector(signOutTapped), for: .touchUpInside)
        signOutButton.translatesAutoresizingMaskIntoConstraints = false
        profileSection.addSubview(signOutButton)

        NSLayoutConstraint.activate([
            avatarLabel.topAnchor.constraint(equalTo: profileSection.topAnchor, constant: 24),
            avatarLabel.centerXAnchor.constraint(equalTo: profileSection.centerXAnchor),
            avatarLabel.widthAnchor.constraint(equalToConstant: 72),
            avatarLabel.heightAnchor.constraint(equalToConstant: 72),

            nameLabel.topAnchor.constraint(equalTo: avatarLabel.bottomAnchor, constant: 10),
            nameLabel.centerXAnchor.constraint(equalTo: profileSection.centerXAnchor),

            emailLabel.topAnchor.constraint(equalTo: nameLabel.bottomAnchor, constant: 4),
            emailLabel.centerXAnchor.constraint(equalTo: profileSection.centerXAnchor),

            signOutButton.topAnchor.constraint(equalTo: emailLabel.bottomAnchor, constant: 32),
            signOutButton.leadingAnchor.constraint(equalTo: profileSection.leadingAnchor, constant: 16),
            signOutButton.trailingAnchor.constraint(equalTo: profileSection.trailingAnchor, constant: -16),
            signOutButton.heightAnchor.constraint(equalToConstant: 48),
            signOutButton.bottomAnchor.constraint(equalTo: profileSection.bottomAnchor, constant: -20),
        ])
    }

    // MARK: - Payment Section

    private func setupPaymentSection() {
        paymentSection.translatesAutoresizingMaskIntoConstraints = false
        paymentSection.isHidden = true
        contentView.addSubview(paymentSection)

        let infoLabel = UILabel()
        infoLabel.text = "Payment methods are managed through your subscription provider."
        infoLabel.font = .systemFont(ofSize: 15)
        infoLabel.textColor = textMuted
        infoLabel.numberOfLines = 0
        infoLabel.textAlignment = .center
        infoLabel.translatesAutoresizingMaskIntoConstraints = false
        paymentSection.addSubview(infoLabel)

        NSLayoutConstraint.activate([
            infoLabel.topAnchor.constraint(equalTo: paymentSection.topAnchor, constant: 40),
            infoLabel.leadingAnchor.constraint(equalTo: paymentSection.leadingAnchor, constant: 32),
            infoLabel.trailingAnchor.constraint(equalTo: paymentSection.trailingAnchor, constant: -32),
            infoLabel.bottomAnchor.constraint(equalTo: paymentSection.bottomAnchor, constant: -40),
        ])
    }

    // MARK: - Recent Scans Section

    private func setupRecentScansSection() {
        recentScansSection.translatesAutoresizingMaskIntoConstraints = false
        recentScansSection.isHidden = true
        contentView.addSubview(recentScansSection)

        let header = UILabel()
        header.text = "📷 Recent Scans"
        header.font = .systemFont(ofSize: 17, weight: .bold)
        header.textColor = textDark
        header.translatesAutoresizingMaskIntoConstraints = false
        recentScansSection.addSubview(header)

        recentScansStack.axis = .vertical
        recentScansStack.spacing = 8
        recentScansStack.translatesAutoresizingMaskIntoConstraints = false
        recentScansSection.addSubview(recentScansStack)

        noScansLabel.text = "No scans yet"
        noScansLabel.font = .systemFont(ofSize: 14)
        noScansLabel.textColor = textMuted
        noScansLabel.textAlignment = .center
        noScansLabel.translatesAutoresizingMaskIntoConstraints = false
        recentScansSection.addSubview(noScansLabel)

        NSLayoutConstraint.activate([
            header.topAnchor.constraint(equalTo: recentScansSection.topAnchor, constant: 16),
            header.leadingAnchor.constraint(equalTo: recentScansSection.leadingAnchor, constant: 16),

            recentScansStack.topAnchor.constraint(equalTo: header.bottomAnchor, constant: 8),
            recentScansStack.leadingAnchor.constraint(equalTo: recentScansSection.leadingAnchor, constant: 16),
            recentScansStack.trailingAnchor.constraint(equalTo: recentScansSection.trailingAnchor, constant: -16),

            noScansLabel.topAnchor.constraint(equalTo: recentScansStack.bottomAnchor, constant: 8),
            noScansLabel.centerXAnchor.constraint(equalTo: recentScansSection.centerXAnchor),
            noScansLabel.bottomAnchor.constraint(equalTo: recentScansSection.bottomAnchor, constant: -20),
        ])
    }

    // MARK: - Subscription Section

    private func setupSubscriptionSection() {
        subscriptionSection.translatesAutoresizingMaskIntoConstraints = false
        subscriptionSection.isHidden = true
        contentView.addSubview(subscriptionSection)

        subscriptionCard.backgroundColor = .white
        subscriptionCard.layer.cornerRadius = 16
        subscriptionCard.layer.shadowColor = UIColor.black.cgColor
        subscriptionCard.layer.shadowOffset = CGSize(width: 0, height: 2)
        subscriptionCard.layer.shadowOpacity = 0.08
        subscriptionCard.layer.shadowRadius = 8
        subscriptionCard.translatesAutoresizingMaskIntoConstraints = false
        subscriptionSection.addSubview(subscriptionCard)

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
        managePlanButton.backgroundColor = subtabActive
        managePlanButton.layer.cornerRadius = 12
        managePlanButton.addTarget(self, action: #selector(managePlanTapped), for: .touchUpInside)
        managePlanButton.translatesAutoresizingMaskIntoConstraints = false
        subscriptionCard.addSubview(managePlanButton)

        NSLayoutConstraint.activate([
            subscriptionCard.topAnchor.constraint(equalTo: subscriptionSection.topAnchor, constant: 16),
            subscriptionCard.leadingAnchor.constraint(equalTo: subscriptionSection.leadingAnchor, constant: 16),
            subscriptionCard.trailingAnchor.constraint(equalTo: subscriptionSection.trailingAnchor, constant: -16),
            subscriptionCard.bottomAnchor.constraint(equalTo: subscriptionSection.bottomAnchor, constant: -20),

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

    // MARK: - Constraints

    private func setupConstraints() {
        NSLayoutConstraint.activate([
            headerView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            headerView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            headerView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            headerView.heightAnchor.constraint(equalToConstant: 50),

            titleLabel.centerXAnchor.constraint(equalTo: headerView.centerXAnchor),
            titleLabel.centerYAnchor.constraint(equalTo: headerView.centerYAnchor),

            subtabScrollView.topAnchor.constraint(equalTo: headerView.bottomAnchor, constant: 8),
            subtabScrollView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            subtabScrollView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            subtabScrollView.heightAnchor.constraint(equalToConstant: 48),

            subtabStack.topAnchor.constraint(equalTo: subtabScrollView.topAnchor, constant: 4),
            subtabStack.leadingAnchor.constraint(equalTo: subtabScrollView.leadingAnchor, constant: 16),
            subtabStack.trailingAnchor.constraint(equalTo: subtabScrollView.trailingAnchor, constant: -16),
            subtabStack.bottomAnchor.constraint(equalTo: subtabScrollView.bottomAnchor, constant: -4),
            subtabStack.heightAnchor.constraint(equalTo: subtabScrollView.heightAnchor, constant: -8),

            scrollView.topAnchor.constraint(equalTo: subtabScrollView.bottomAnchor),
            scrollView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            scrollView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            scrollView.bottomAnchor.constraint(equalTo: view.bottomAnchor),

            contentView.topAnchor.constraint(equalTo: scrollView.topAnchor),
            contentView.leadingAnchor.constraint(equalTo: scrollView.leadingAnchor),
            contentView.trailingAnchor.constraint(equalTo: scrollView.trailingAnchor),
            contentView.bottomAnchor.constraint(equalTo: scrollView.bottomAnchor),
            contentView.widthAnchor.constraint(equalTo: scrollView.widthAnchor),

            // All sections share the same position
            profileSection.topAnchor.constraint(equalTo: contentView.topAnchor),
            profileSection.leadingAnchor.constraint(equalTo: contentView.leadingAnchor),
            profileSection.trailingAnchor.constraint(equalTo: contentView.trailingAnchor),

            paymentSection.topAnchor.constraint(equalTo: contentView.topAnchor),
            paymentSection.leadingAnchor.constraint(equalTo: contentView.leadingAnchor),
            paymentSection.trailingAnchor.constraint(equalTo: contentView.trailingAnchor),

            recentScansSection.topAnchor.constraint(equalTo: contentView.topAnchor),
            recentScansSection.leadingAnchor.constraint(equalTo: contentView.leadingAnchor),
            recentScansSection.trailingAnchor.constraint(equalTo: contentView.trailingAnchor),

            subscriptionSection.topAnchor.constraint(equalTo: contentView.topAnchor),
            subscriptionSection.leadingAnchor.constraint(equalTo: contentView.leadingAnchor),
            subscriptionSection.trailingAnchor.constraint(equalTo: contentView.trailingAnchor),
        ])

        // The visible section determines content height
        let profileBottom = profileSection.bottomAnchor.constraint(equalTo: contentView.bottomAnchor)
        profileBottom.priority = .defaultLow
        profileBottom.isActive = true

        let paymentBottom = paymentSection.bottomAnchor.constraint(equalTo: contentView.bottomAnchor)
        paymentBottom.priority = .defaultLow
        paymentBottom.isActive = true

        let scansBottom = recentScansSection.bottomAnchor.constraint(equalTo: contentView.bottomAnchor)
        scansBottom.priority = .defaultLow
        scansBottom.isActive = true

        let subBottom = subscriptionSection.bottomAnchor.constraint(equalTo: contentView.bottomAnchor)
        subBottom.priority = .defaultLow
        subBottom.isActive = true
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

        Task {
            do {
                let status = try await apiService.getSubscriptionInfo()
                await MainActor.run {
                    planNameLabel.text = "\(status.plan_name) Plan"
                    planStatusLabel.text = status.status.capitalized
                    planStatusLabel.textColor = status.status == "active" ? .systemGreen : .systemOrange
                    let normalized = status.plan_name.lowercased()
                    if normalized != limiter.planName {
                        if normalized == "free" {
                            limiter.downgrade()
                        } else {
                            limiter.upgradeTo(plan: normalized)
                        }
                    }
                }
            } catch {
                // Keep local state as fallback
            }
        }
    }

    private func loadRecentScans() {
        Task {
            do {
                let result = try await apiService.getRecentScans(days: 30, limit: 10)
                await MainActor.run {
                    recentScans = result.scans
                    renderRecentScans()
                }
            } catch {
                await MainActor.run { renderRecentScans() }
            }
        }
    }

    // MARK: - Render Data

    private func renderRecentScans() {
        recentScansStack.arrangedSubviews.forEach { $0.removeFromSuperview() }
        noScansLabel.isHidden = !recentScans.isEmpty

        for scan in recentScans.prefix(10) {
            let card = makeScanRow(scan)
            recentScansStack.addArrangedSubview(card)
        }
    }

    private func makeScanRow(_ scan: RecentScan) -> UIView {
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
        dateLbl.text = formatDate(scan.scanned_at)
        dateLbl.font = .systemFont(ofSize: 12)
        dateLbl.textColor = textMuted
        dateLbl.translatesAutoresizingMaskIntoConstraints = false
        row.addSubview(dateLbl)

        let statusLbl = UILabel()
        statusLbl.text = scan.processing_status.capitalized
        statusLbl.font = .systemFont(ofSize: 11, weight: .medium)
        statusLbl.textColor = scan.processing_status == "completed" ? .systemGreen : .systemOrange
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
        let limiter = ScanLimitManager.shared
        if limiter.isPremium {
            Task {
                do {
                    let portal = try await apiService.getCustomerPortal()
                    await MainActor.run {
                        if let url = URL(string: portal.portal_url) {
                            UIApplication.shared.open(url)
                        }
                    }
                } catch {
                    await MainActor.run {
                        let paywall = PaywallViewController()
                        paywall.modalPresentationStyle = .fullScreen
                        present(paywall, animated: true)
                    }
                }
            }
        } else {
            let paywall = PaywallViewController()
            paywall.modalPresentationStyle = .fullScreen
            present(paywall, animated: true)
        }
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

