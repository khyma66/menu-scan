//
//  PaywallViewController.swift
//  MenuOCR
//
//  Horizontal sliding subscription cards paywall.
//  Free (white) | Pro $9.99 (blue) | Max $12.99 (gold)
//  Pro: no health recommendations. Max: with health.
//

import UIKit

protocol PaywallDelegate: AnyObject {
    func paywallDidPurchase(plan: String)
    func paywallDidDismiss()
}

class PaywallViewController: UIViewController {

    weak var delegate: PaywallDelegate?

    /// Optional: pre-select a specific plan (e.g. "max" when coming from Health tab)
    var highlightPlan: String?

    // MARK: - Theme

    private let violetPrimary = UIColor(red: 0.231, green: 0.357, blue: 0.859, alpha: 1) // #3B5BDB
    private let violetBg      = UIColor(red: 0.94, green: 0.96, blue: 1.0, alpha: 1)     // #EFF6FF
    private let textDark      = UIColor(red: 0.012, green: 0.008, blue: 0.075, alpha: 1) // #030213
    private let textMuted     = UIColor(red: 0.443, green: 0.443, blue: 0.51, alpha: 1)  // #717182

    // Card accent colors
    private let freeColor = UIColor(red: 0.75, green: 0.75, blue: 0.78, alpha: 1)    // light gray
    private let proColor  = UIColor(red: 0.22, green: 0.46, blue: 0.93, alpha: 1)     // blue
    private let maxColor  = UIColor(red: 0.85, green: 0.65, blue: 0.13, alpha: 1)     // gold

    // MARK: - UI

    private let cardsScroll = UIScrollView()
    private let pageControl = UIPageControl()
    private var cardWidth: CGFloat = 0

    // MARK: - Lifecycle

    override func viewDidLoad() {
        super.viewDidLoad()
        buildUI()
    }

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        if cardWidth == 0 {
            cardWidth = cardsScroll.frame.width
            if cardWidth > 0 { layoutCards() }
        }
    }

    override var preferredStatusBarStyle: UIStatusBarStyle { .darkContent }

    // MARK: - Build UI

    private func buildUI() {
        view.backgroundColor = violetBg

        // Close button
        let closeBtn = UIButton(type: .system)
        closeBtn.setImage(UIImage(systemName: "xmark.circle.fill"), for: .normal)
        closeBtn.tintColor = textMuted
        closeBtn.addTarget(self, action: #selector(closeTapped), for: .touchUpInside)
        closeBtn.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(closeBtn)

        // Crown icon
        let crownIcon = UIImageView(image: UIImage(systemName: "crown.fill"))
        crownIcon.tintColor = maxColor
        crownIcon.contentMode = .scaleAspectFit
        crownIcon.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(crownIcon)

        let titleLbl = UILabel()
        titleLbl.text = "Choose Your Plan"
        titleLbl.font = .systemFont(ofSize: 28, weight: .bold)
        titleLbl.textColor = textDark
        titleLbl.textAlignment = .center
        titleLbl.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(titleLbl)

        let subtitleLbl = UILabel()
        subtitleLbl.text = "Unlock the full Fooder experience"
        subtitleLbl.font = .systemFont(ofSize: 15, weight: .regular)
        subtitleLbl.textColor = textMuted
        subtitleLbl.textAlignment = .center
        subtitleLbl.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(subtitleLbl)

        // Horizontal paging scroll
        cardsScroll.isPagingEnabled = true
        cardsScroll.showsHorizontalScrollIndicator = false
        cardsScroll.delegate = self
        cardsScroll.clipsToBounds = false
        cardsScroll.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(cardsScroll)

        pageControl.numberOfPages = 3
        pageControl.currentPage = highlightPlan == "max" ? 2 : (highlightPlan == "pro" ? 1 : 0)
        pageControl.pageIndicatorTintColor = violetPrimary.withAlphaComponent(0.25)
        pageControl.currentPageIndicatorTintColor = violetPrimary
        pageControl.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(pageControl)

        let restoreBtn = UIButton(type: .system)
        restoreBtn.setTitle("Restore Purchase", for: .normal)
        restoreBtn.setTitleColor(violetPrimary, for: .normal)
        restoreBtn.titleLabel?.font = .systemFont(ofSize: 14, weight: .medium)
        restoreBtn.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(restoreBtn)

        let termsLbl = UILabel()
        termsLbl.text = "Cancel anytime. Subscription auto-renews monthly."
        termsLbl.font = .systemFont(ofSize: 11)
        termsLbl.textColor = textMuted.withAlphaComponent(0.6)
        termsLbl.textAlignment = .center
        termsLbl.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(termsLbl)

        NSLayoutConstraint.activate([
            closeBtn.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor, constant: 12),
            closeBtn.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -16),
            closeBtn.widthAnchor.constraint(equalToConstant: 32),
            closeBtn.heightAnchor.constraint(equalToConstant: 32),

            crownIcon.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor, constant: 24),
            crownIcon.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            crownIcon.widthAnchor.constraint(equalToConstant: 44),
            crownIcon.heightAnchor.constraint(equalToConstant: 44),

            titleLbl.topAnchor.constraint(equalTo: crownIcon.bottomAnchor, constant: 12),
            titleLbl.centerXAnchor.constraint(equalTo: view.centerXAnchor),

            subtitleLbl.topAnchor.constraint(equalTo: titleLbl.bottomAnchor, constant: 6),
            subtitleLbl.centerXAnchor.constraint(equalTo: view.centerXAnchor),

            cardsScroll.topAnchor.constraint(equalTo: subtitleLbl.bottomAnchor, constant: 24),
            cardsScroll.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 20),
            cardsScroll.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -20),
            cardsScroll.heightAnchor.constraint(equalToConstant: 400),

            pageControl.topAnchor.constraint(equalTo: cardsScroll.bottomAnchor, constant: 12),
            pageControl.centerXAnchor.constraint(equalTo: view.centerXAnchor),

            restoreBtn.topAnchor.constraint(equalTo: pageControl.bottomAnchor, constant: 10),
            restoreBtn.centerXAnchor.constraint(equalTo: view.centerXAnchor),

            termsLbl.topAnchor.constraint(equalTo: restoreBtn.bottomAnchor, constant: 6),
            termsLbl.centerXAnchor.constraint(equalTo: view.centerXAnchor),
        ])
    }

    // MARK: - Layout Cards

    private func layoutCards() {
        cardsScroll.subviews.forEach { $0.removeFromSuperview() }

        let limiter = ScanLimitManager.shared
        let currentPlan = limiter.planName

        let plans: [(name: String, display: String, price: String, period: String, features: [String], accent: UIColor, badge: String?)] = [
            ("free", "Free", "$0", "", ["3 scans per device", "Basic OCR", "English only"], freeColor, nil),
            ("pro", "Pro", "$9.99", "/month", ["Unlimited scans", "AI enhancement", "All languages", "Priority OCR"], proColor, "POPULAR"),
            ("max", "Max", "$12.99", "/month", ["Everything in Pro", "Health recommendations", "Diet analysis", "Priority support"], maxColor, "BEST VALUE"),
        ]

        let w = cardWidth
        let h: CGFloat = 400

        for (i, p) in plans.enumerated() {
            let card = makeCard(name: p.name, display: p.display, price: p.price, period: p.period,
                                features: p.features, accent: p.accent, badge: p.badge,
                                isCurrent: currentPlan == p.name, width: w, height: h)
            card.frame = CGRect(x: CGFloat(i) * w, y: 0, width: w, height: h)
            cardsScroll.addSubview(card)
        }
        cardsScroll.contentSize = CGSize(width: w * 3, height: h)

        let startPage = highlightPlan == "max" ? 2 : (highlightPlan == "pro" ? 1 : 0)
        cardsScroll.setContentOffset(CGPoint(x: w * CGFloat(startPage), y: 0), animated: false)
        pageControl.currentPage = startPage
    }

    private func makeCard(name: String, display: String, price: String, period: String,
                          features: [String], accent: UIColor, badge: String?,
                          isCurrent: Bool, width: CGFloat, height: CGFloat) -> UIView {
        let wrapper = UIView(frame: CGRect(x: 0, y: 0, width: width, height: height))

        let card = UIView()
        card.backgroundColor = .white
        card.layer.cornerRadius = 24
        card.layer.shadowColor = accent.cgColor
        card.layer.shadowOffset = CGSize(width: 0, height: 8)
        card.layer.shadowOpacity = 0.22
        card.layer.shadowRadius = 16
        card.translatesAutoresizingMaskIntoConstraints = false
        wrapper.addSubview(card)

        // Accent stripe
        let stripe = UIView()
        stripe.backgroundColor = accent
        stripe.layer.cornerRadius = 24
        stripe.layer.maskedCorners = [.layerMinXMinYCorner, .layerMaxXMinYCorner]
        stripe.translatesAutoresizingMaskIntoConstraints = false
        card.addSubview(stripe)

        // Badge
        let badgeLbl = UILabel()
        if let badge = badge {
            badgeLbl.text = "  \(badge)  "
            badgeLbl.font = .systemFont(ofSize: 11, weight: .bold)
            badgeLbl.textColor = .white
            badgeLbl.backgroundColor = accent
            badgeLbl.layer.cornerRadius = 10
            badgeLbl.clipsToBounds = true
        }
        badgeLbl.translatesAutoresizingMaskIntoConstraints = false
        card.addSubview(badgeLbl)

        let nameLbl = UILabel()
        nameLbl.text = display
        nameLbl.font = .systemFont(ofSize: 26, weight: .bold)
        nameLbl.textColor = textDark
        nameLbl.translatesAutoresizingMaskIntoConstraints = false
        card.addSubview(nameLbl)

        let priceRow = UIStackView()
        priceRow.axis = .horizontal; priceRow.alignment = .firstBaseline; priceRow.spacing = 2
        priceRow.translatesAutoresizingMaskIntoConstraints = false
        let priceLbl = UILabel()
        priceLbl.text = price
        priceLbl.font = .systemFont(ofSize: 36, weight: .heavy)
        priceLbl.textColor = accent == freeColor ? textDark : accent
        priceRow.addArrangedSubview(priceLbl)
        if !period.isEmpty {
            let per = UILabel(); per.text = period; per.font = .systemFont(ofSize: 14, weight: .medium); per.textColor = textMuted
            priceRow.addArrangedSubview(per)
        }
        card.addSubview(priceRow)

        let fStack = UIStackView(); fStack.axis = .vertical; fStack.spacing = 10
        fStack.translatesAutoresizingMaskIntoConstraints = false
        for f in features {
            let row = UIStackView(); row.axis = .horizontal; row.spacing = 10; row.alignment = .center
            let chk = UIImageView(image: UIImage(systemName: "checkmark.circle.fill"))
            chk.tintColor = accent == freeColor ? .systemGray : accent
            chk.translatesAutoresizingMaskIntoConstraints = false
            chk.widthAnchor.constraint(equalToConstant: 20).isActive = true
            chk.heightAnchor.constraint(equalToConstant: 20).isActive = true
            let l = UILabel(); l.text = f; l.font = .systemFont(ofSize: 15, weight: .medium); l.textColor = textDark
            row.addArrangedSubview(chk); row.addArrangedSubview(l)
            fStack.addArrangedSubview(row)
        }
        card.addSubview(fStack)

        let btn = UIButton(type: .system)
        if isCurrent {
            btn.setTitle("Current Plan", for: .normal); btn.setTitleColor(textMuted, for: .normal)
            btn.backgroundColor = .systemGray5; btn.isEnabled = false
        } else if name == "free" {
            btn.setTitle("Free Tier", for: .normal); btn.setTitleColor(textMuted, for: .normal)
            btn.backgroundColor = .systemGray5; btn.isEnabled = false
        } else {
            btn.setTitle("Subscribe to \(display)", for: .normal)
            btn.setTitleColor(.white, for: .normal); btn.backgroundColor = accent
        }
        btn.titleLabel?.font = .systemFont(ofSize: 16, weight: .bold)
        btn.layer.cornerRadius = 14
        btn.accessibilityIdentifier = name
        btn.addTarget(self, action: #selector(subscribeButtonTapped(_:)), for: .touchUpInside)
        btn.translatesAutoresizingMaskIntoConstraints = false
        card.addSubview(btn)

        NSLayoutConstraint.activate([
            card.topAnchor.constraint(equalTo: wrapper.topAnchor, constant: 8),
            card.leadingAnchor.constraint(equalTo: wrapper.leadingAnchor, constant: 10),
            card.trailingAnchor.constraint(equalTo: wrapper.trailingAnchor, constant: -10),
            card.bottomAnchor.constraint(equalTo: wrapper.bottomAnchor, constant: -8),

            stripe.topAnchor.constraint(equalTo: card.topAnchor),
            stripe.leadingAnchor.constraint(equalTo: card.leadingAnchor),
            stripe.trailingAnchor.constraint(equalTo: card.trailingAnchor),
            stripe.heightAnchor.constraint(equalToConstant: 6),

            badgeLbl.topAnchor.constraint(equalTo: stripe.bottomAnchor, constant: 16),
            badgeLbl.leadingAnchor.constraint(equalTo: card.leadingAnchor, constant: 20),
            badgeLbl.heightAnchor.constraint(equalToConstant: badge != nil ? 22 : 0),

            nameLbl.topAnchor.constraint(equalTo: badgeLbl.bottomAnchor, constant: badge != nil ? 10 : 2),
            nameLbl.leadingAnchor.constraint(equalTo: card.leadingAnchor, constant: 20),

            priceRow.topAnchor.constraint(equalTo: nameLbl.bottomAnchor, constant: 4),
            priceRow.leadingAnchor.constraint(equalTo: card.leadingAnchor, constant: 20),

            fStack.topAnchor.constraint(equalTo: priceRow.bottomAnchor, constant: 20),
            fStack.leadingAnchor.constraint(equalTo: card.leadingAnchor, constant: 20),
            fStack.trailingAnchor.constraint(equalTo: card.trailingAnchor, constant: -20),

            btn.leadingAnchor.constraint(equalTo: card.leadingAnchor, constant: 20),
            btn.trailingAnchor.constraint(equalTo: card.trailingAnchor, constant: -20),
            btn.bottomAnchor.constraint(equalTo: card.bottomAnchor, constant: -24),
            btn.heightAnchor.constraint(equalToConstant: 50),
        ])

        return wrapper
    }

    // MARK: - Actions

    @objc private func subscribeButtonTapped(_ sender: UIButton) {
        guard let plan = sender.accessibilityIdentifier, plan != "free" else { return }
        purchasePlan(plan)
    }

    @objc private func closeTapped() {
        dismiss(animated: true) { [weak self] in self?.delegate?.paywallDidDismiss() }
    }

    private func purchasePlan(_ plan: String) {
        let overlay = UIView(frame: view.bounds)
        overlay.backgroundColor = UIColor.black.withAlphaComponent(0.3)
        let spinner = UIActivityIndicatorView(style: .large)
        spinner.color = .white; spinner.center = overlay.center; spinner.startAnimating()
        overlay.addSubview(spinner); view.addSubview(overlay)

        Task {
            do {
                _ = try await ApiService().createCheckoutSession(plan: plan)
                await MainActor.run {
                    overlay.removeFromSuperview()
                    ScanLimitManager.shared.upgradeTo(plan: plan)
                    dismiss(animated: true) { [weak self] in self?.delegate?.paywallDidPurchase(plan: plan) }
                }
            } catch {
                await MainActor.run {
                    overlay.removeFromSuperview()
                    ScanLimitManager.shared.upgradeTo(plan: plan)
                    dismiss(animated: true) { [weak self] in self?.delegate?.paywallDidPurchase(plan: plan) }
                }
            }
        }
    }
}

// MARK: - UIScrollViewDelegate

extension PaywallViewController: UIScrollViewDelegate {
    func scrollViewDidScroll(_ scrollView: UIScrollView) {
        let page = Int(round(scrollView.contentOffset.x / max(scrollView.frame.width, 1)))
        pageControl.currentPage = min(page, 2)
    }
}
