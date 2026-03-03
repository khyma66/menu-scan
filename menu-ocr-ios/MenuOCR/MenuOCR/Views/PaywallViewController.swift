//
//  PaywallViewController.swift
//  MenuOCR
//
//  Full-screen paywall shown when free scan limit (3) is reached.
//  Offers Pro ($9.99/mo) and Max ($19.99/mo) plans.
//  Light violet theme, modern card-based design.
//

import UIKit

protocol PaywallDelegate: AnyObject {
    func paywallDidPurchase(plan: String)
    func paywallDidDismiss()
}

class PaywallViewController: UIViewController {

    weak var delegate: PaywallDelegate?

    // MARK: - Theme colours

    private let violetPrimary  = UIColor(red: 0.486, green: 0.227, blue: 0.929, alpha: 1)   // #7C3AED
    private let violetLight    = UIColor(red: 0.91, green: 0.87, blue: 1.0, alpha: 1)         // #E8DEFF
    private let violetBg       = UIColor(red: 0.96, green: 0.94, blue: 1.0, alpha: 1)         // #F5F0FF
    private let textDark       = UIColor(red: 0.12, green: 0.12, blue: 0.14, alpha: 1)
    private let textMuted      = UIColor(red: 0.45, green: 0.42, blue: 0.55, alpha: 1)
    private let goldAccent     = UIColor(red: 1.0, green: 0.76, blue: 0.03, alpha: 1)

    // MARK: - Lifecycle

    override func viewDidLoad() {
        super.viewDidLoad()
        buildUI()
    }

    override var preferredStatusBarStyle: UIStatusBarStyle { .darkContent }

    // MARK: - Build UI

    private func buildUI() {
        view.backgroundColor = violetBg

        let scroll = UIScrollView()
        scroll.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(scroll)
        let content = UIView()
        content.translatesAutoresizingMaskIntoConstraints = false
        scroll.addSubview(content)

        NSLayoutConstraint.activate([
            scroll.topAnchor.constraint(equalTo: view.topAnchor),
            scroll.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            scroll.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            scroll.bottomAnchor.constraint(equalTo: view.bottomAnchor),
            content.topAnchor.constraint(equalTo: scroll.topAnchor),
            content.leadingAnchor.constraint(equalTo: scroll.leadingAnchor),
            content.trailingAnchor.constraint(equalTo: scroll.trailingAnchor),
            content.bottomAnchor.constraint(equalTo: scroll.bottomAnchor),
            content.widthAnchor.constraint(equalTo: scroll.widthAnchor),
        ])

        // Close button
        let closeBtn = UIButton(type: .system)
        closeBtn.setImage(UIImage(systemName: "xmark.circle.fill"), for: .normal)
        closeBtn.tintColor = textMuted
        closeBtn.addTarget(self, action: #selector(closeTapped), for: .touchUpInside)
        closeBtn.translatesAutoresizingMaskIntoConstraints = false
        content.addSubview(closeBtn)

        // Lock icon
        let lockIcon = UIImageView(image: UIImage(systemName: "lock.shield.fill"))
        lockIcon.tintColor = violetPrimary
        lockIcon.contentMode = .scaleAspectFit
        lockIcon.translatesAutoresizingMaskIntoConstraints = false
        content.addSubview(lockIcon)

        // Title
        let titleLbl = UILabel()
        titleLbl.text = "Free Limit Reached"
        titleLbl.font = .systemFont(ofSize: 28, weight: .bold)
        titleLbl.textColor = textDark
        titleLbl.textAlignment = .center
        titleLbl.translatesAutoresizingMaskIntoConstraints = false
        content.addSubview(titleLbl)

        // Subtitle
        let subtitleLbl = UILabel()
        let remaining = ScanLimitManager.shared.scanCount
        subtitleLbl.text = "You've used all \(ScanLimitManager.freeLimit) free scans.\nUpgrade to keep scanning menus."
        subtitleLbl.font = .systemFont(ofSize: 15, weight: .regular)
        subtitleLbl.textColor = textMuted
        subtitleLbl.textAlignment = .center
        subtitleLbl.numberOfLines = 0
        subtitleLbl.translatesAutoresizingMaskIntoConstraints = false
        content.addSubview(subtitleLbl)

        // Pro card
        let proCard = makePlanCard(
            title: "Pro",
            price: "$9.99",
            period: "/month",
            features: ["Unlimited scans", "AI-powered enhancement", "All languages", "Health recommendations"],
            isPrimary: true,
            badge: "POPULAR"
        )
        proCard.tag = 100
        let proTap = UITapGestureRecognizer(target: self, action: #selector(proSelected))
        proCard.addGestureRecognizer(proTap)
        content.addSubview(proCard)

        // Max card
        let maxCard = makePlanCard(
            title: "Max",
            price: "$19.99",
            period: "/month",
            features: ["Everything in Pro", "Priority processing", "API access", "Custom integrations", "Priority support"],
            isPrimary: false,
            badge: "BEST VALUE"
        )
        maxCard.tag = 200
        let maxTap = UITapGestureRecognizer(target: self, action: #selector(maxSelected))
        maxCard.addGestureRecognizer(maxTap)
        content.addSubview(maxCard)

        // Restore button
        let restoreBtn = UIButton(type: .system)
        restoreBtn.setTitle("Restore Purchase", for: .normal)
        restoreBtn.setTitleColor(violetPrimary, for: .normal)
        restoreBtn.titleLabel?.font = .systemFont(ofSize: 14, weight: .medium)
        restoreBtn.translatesAutoresizingMaskIntoConstraints = false
        content.addSubview(restoreBtn)

        // Terms
        let termsLbl = UILabel()
        termsLbl.text = "Cancel anytime. Subscription renews automatically."
        termsLbl.font = .systemFont(ofSize: 12, weight: .regular)
        termsLbl.textColor = textMuted.withAlphaComponent(0.7)
        termsLbl.textAlignment = .center
        termsLbl.translatesAutoresizingMaskIntoConstraints = false
        content.addSubview(termsLbl)

        NSLayoutConstraint.activate([
            closeBtn.topAnchor.constraint(equalTo: content.safeAreaLayoutGuide.topAnchor, constant: 12),
            closeBtn.trailingAnchor.constraint(equalTo: content.trailingAnchor, constant: -16),
            closeBtn.widthAnchor.constraint(equalToConstant: 32),
            closeBtn.heightAnchor.constraint(equalToConstant: 32),

            lockIcon.topAnchor.constraint(equalTo: content.safeAreaLayoutGuide.topAnchor, constant: 40),
            lockIcon.centerXAnchor.constraint(equalTo: content.centerXAnchor),
            lockIcon.widthAnchor.constraint(equalToConstant: 56),
            lockIcon.heightAnchor.constraint(equalToConstant: 56),

            titleLbl.topAnchor.constraint(equalTo: lockIcon.bottomAnchor, constant: 16),
            titleLbl.centerXAnchor.constraint(equalTo: content.centerXAnchor),

            subtitleLbl.topAnchor.constraint(equalTo: titleLbl.bottomAnchor, constant: 8),
            subtitleLbl.leadingAnchor.constraint(equalTo: content.leadingAnchor, constant: 32),
            subtitleLbl.trailingAnchor.constraint(equalTo: content.trailingAnchor, constant: -32),

            proCard.topAnchor.constraint(equalTo: subtitleLbl.bottomAnchor, constant: 28),
            proCard.leadingAnchor.constraint(equalTo: content.leadingAnchor, constant: 20),
            proCard.trailingAnchor.constraint(equalTo: content.trailingAnchor, constant: -20),

            maxCard.topAnchor.constraint(equalTo: proCard.bottomAnchor, constant: 16),
            maxCard.leadingAnchor.constraint(equalTo: content.leadingAnchor, constant: 20),
            maxCard.trailingAnchor.constraint(equalTo: content.trailingAnchor, constant: -20),

            restoreBtn.topAnchor.constraint(equalTo: maxCard.bottomAnchor, constant: 20),
            restoreBtn.centerXAnchor.constraint(equalTo: content.centerXAnchor),

            termsLbl.topAnchor.constraint(equalTo: restoreBtn.bottomAnchor, constant: 8),
            termsLbl.centerXAnchor.constraint(equalTo: content.centerXAnchor),
            termsLbl.bottomAnchor.constraint(equalTo: content.bottomAnchor, constant: -40),
        ])
    }

    // MARK: - Plan Card Builder

    private func makePlanCard(title: String, price: String, period: String, features: [String], isPrimary: Bool, badge: String) -> UIView {
        let card = UIView()
        card.backgroundColor = isPrimary ? .white : .white
        card.layer.cornerRadius = 20
        card.layer.borderWidth = isPrimary ? 2.5 : 1
        card.layer.borderColor = isPrimary ? violetPrimary.cgColor : UIColor.systemGray4.cgColor
        card.layer.shadowColor = violetPrimary.cgColor
        card.layer.shadowOffset = CGSize(width: 0, height: isPrimary ? 6 : 2)
        card.layer.shadowOpacity = isPrimary ? 0.18 : 0.06
        card.layer.shadowRadius = isPrimary ? 16 : 8
        card.translatesAutoresizingMaskIntoConstraints = false

        // Badge
        let badgeLbl = UILabel()
        badgeLbl.text = badge
        badgeLbl.font = .systemFont(ofSize: 11, weight: .bold)
        badgeLbl.textColor = .white
        badgeLbl.backgroundColor = isPrimary ? violetPrimary : goldAccent
        badgeLbl.textAlignment = .center
        badgeLbl.layer.cornerRadius = 10
        badgeLbl.clipsToBounds = true
        badgeLbl.translatesAutoresizingMaskIntoConstraints = false
        card.addSubview(badgeLbl)

        // Plan title
        let planLbl = UILabel()
        planLbl.text = title
        planLbl.font = .systemFont(ofSize: 24, weight: .bold)
        planLbl.textColor = textDark
        planLbl.translatesAutoresizingMaskIntoConstraints = false
        card.addSubview(planLbl)

        // Price row
        let priceRow = UIStackView()
        priceRow.axis = .horizontal
        priceRow.alignment = .firstBaseline
        priceRow.spacing = 2
        priceRow.translatesAutoresizingMaskIntoConstraints = false

        let priceLbl = UILabel()
        priceLbl.text = price
        priceLbl.font = .systemFont(ofSize: 32, weight: .heavy)
        priceLbl.textColor = violetPrimary
        priceRow.addArrangedSubview(priceLbl)

        let periodLbl = UILabel()
        periodLbl.text = period
        periodLbl.font = .systemFont(ofSize: 14, weight: .medium)
        periodLbl.textColor = textMuted
        priceRow.addArrangedSubview(periodLbl)
        card.addSubview(priceRow)

        // Features
        let featureStack = UIStackView()
        featureStack.axis = .vertical
        featureStack.spacing = 8
        featureStack.translatesAutoresizingMaskIntoConstraints = false
        for f in features {
            let row = UIStackView()
            row.axis = .horizontal
            row.spacing = 8
            row.alignment = .center
            let check = UIImageView(image: UIImage(systemName: "checkmark.circle.fill"))
            check.tintColor = violetPrimary
            check.translatesAutoresizingMaskIntoConstraints = false
            check.widthAnchor.constraint(equalToConstant: 18).isActive = true
            check.heightAnchor.constraint(equalToConstant: 18).isActive = true
            let lbl = UILabel()
            lbl.text = f
            lbl.font = .systemFont(ofSize: 14, weight: .medium)
            lbl.textColor = textDark
            row.addArrangedSubview(check)
            row.addArrangedSubview(lbl)
            featureStack.addArrangedSubview(row)
        }
        card.addSubview(featureStack)

        // Subscribe button
        let subscribeBtn = UIButton(type: .system)
        subscribeBtn.setTitle("Subscribe to \(title)", for: .normal)
        subscribeBtn.setTitleColor(.white, for: .normal)
        subscribeBtn.titleLabel?.font = .systemFont(ofSize: 16, weight: .bold)
        subscribeBtn.backgroundColor = isPrimary ? violetPrimary : textDark
        subscribeBtn.layer.cornerRadius = 14
        subscribeBtn.isUserInteractionEnabled = false // card tap handles it
        subscribeBtn.translatesAutoresizingMaskIntoConstraints = false
        card.addSubview(subscribeBtn)

        NSLayoutConstraint.activate([
            badgeLbl.topAnchor.constraint(equalTo: card.topAnchor, constant: 16),
            badgeLbl.leadingAnchor.constraint(equalTo: card.leadingAnchor, constant: 20),
            badgeLbl.widthAnchor.constraint(greaterThanOrEqualToConstant: 80),
            badgeLbl.heightAnchor.constraint(equalToConstant: 22),

            planLbl.topAnchor.constraint(equalTo: badgeLbl.bottomAnchor, constant: 10),
            planLbl.leadingAnchor.constraint(equalTo: card.leadingAnchor, constant: 20),

            priceRow.topAnchor.constraint(equalTo: planLbl.bottomAnchor, constant: 4),
            priceRow.leadingAnchor.constraint(equalTo: card.leadingAnchor, constant: 20),

            featureStack.topAnchor.constraint(equalTo: priceRow.bottomAnchor, constant: 16),
            featureStack.leadingAnchor.constraint(equalTo: card.leadingAnchor, constant: 20),
            featureStack.trailingAnchor.constraint(equalTo: card.trailingAnchor, constant: -20),

            subscribeBtn.topAnchor.constraint(equalTo: featureStack.bottomAnchor, constant: 18),
            subscribeBtn.leadingAnchor.constraint(equalTo: card.leadingAnchor, constant: 20),
            subscribeBtn.trailingAnchor.constraint(equalTo: card.trailingAnchor, constant: -20),
            subscribeBtn.heightAnchor.constraint(equalToConstant: 50),
            subscribeBtn.bottomAnchor.constraint(equalTo: card.bottomAnchor, constant: -20),
        ])

        return card
    }

    // MARK: - Actions

    @objc private func proSelected() {
        purchasePlan("pro")
    }

    @objc private func maxSelected() {
        purchasePlan("max")
    }

    @objc private func closeTapped() {
        dismiss(animated: true) { [weak self] in
            self?.delegate?.paywallDidDismiss()
        }
    }

    private func purchasePlan(_ plan: String) {
        // Show loading overlay
        let overlay = UIView(frame: view.bounds)
        overlay.backgroundColor = UIColor.black.withAlphaComponent(0.3)
        overlay.tag = 9999
        let spinner = UIActivityIndicatorView(style: .large)
        spinner.color = .white
        spinner.center = overlay.center
        spinner.startAnimating()
        overlay.addSubview(spinner)
        view.addSubview(overlay)

        // Use Stripe Checkout via backend
        Task {
            do {
                let apiService = ApiService()
                let result = try await apiService.createCheckoutSession(plan: plan)

                await MainActor.run {
                    overlay.removeFromSuperview()
                    // For now, mark as premium (in production, verify receipt server-side)
                    ScanLimitManager.shared.upgradeTo(plan: plan)
                    dismiss(animated: true) { [weak self] in
                        self?.delegate?.paywallDidPurchase(plan: plan)
                    }
                }
            } catch {
                await MainActor.run {
                    overlay.removeFromSuperview()
                    // Still upgrade for now (Stripe webhook would handle in production)
                    ScanLimitManager.shared.upgradeTo(plan: plan)
                    dismiss(animated: true) { [weak self] in
                        self?.delegate?.paywallDidPurchase(plan: plan)
                    }
                }
            }
        }
    }
}
