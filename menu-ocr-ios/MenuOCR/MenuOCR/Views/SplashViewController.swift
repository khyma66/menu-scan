//
//  SplashViewController.swift
//  MenuOCR
//
//  Splash screen with breathe-out logo animation
//  Shows on app launch, then transitions to main tab bar
//

import UIKit

class SplashViewController: UIViewController {

    // MARK: - Completion Handler
    var onAnimationComplete: (() -> Void)?

    // MARK: - UI Components

    /// Gradient background layer
    private let gradientLayer: CAGradientLayer = {
        let layer = CAGradientLayer()
        layer.colors = [
            UIColor(red: 0.98, green: 0.24, blue: 0.18, alpha: 1.0).cgColor, // Primary red-orange
            UIColor(red: 0.90, green: 0.16, blue: 0.12, alpha: 1.0).cgColor  // Deeper red
        ]
        layer.startPoint = CGPoint(x: 0, y: 0)
        layer.endPoint = CGPoint(x: 1, y: 1)
        return layer
    }()

    /// App icon container
    private let iconContainer: UIView = {
        let view = UIView()
        view.backgroundColor = UIColor.white.withAlphaComponent(0.15)
        view.layer.cornerRadius = 40
        view.translatesAutoresizingMaskIntoConstraints = false
        return view
    }()

    /// App icon (fork.knife SF symbol)
    private let iconImageView: UIImageView = {
        let config = UIImage.SymbolConfiguration(pointSize: 44, weight: .medium)
        let image = UIImage(systemName: "fork.knife.circle.fill", withConfiguration: config)
        let imageView = UIImageView(image: image)
        imageView.tintColor = .white
        imageView.contentMode = .scaleAspectFit
        imageView.translatesAutoresizingMaskIntoConstraints = false
        return imageView
    }()

    /// App name label
    private let appNameLabel: UILabel = {
        let label = UILabel()
        label.text = "Foodit"
        label.font = .systemFont(ofSize: 36, weight: .bold)
        label.textColor = .white
        label.textAlignment = .center
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }()

    /// Tagline label
    private let taglineLabel: UILabel = {
        let label = UILabel()
        label.text = "Scan · Discover · Eat Healthy"
        label.font = .systemFont(ofSize: 16, weight: .regular)
        label.textColor = UIColor.white.withAlphaComponent(0.85)
        label.textAlignment = .center
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }()

    // MARK: - Lifecycle

    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
    }

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        gradientLayer.frame = view.bounds
    }

    override var preferredStatusBarStyle: UIStatusBarStyle {
        return .lightContent
    }

    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        runBreatheOutAnimation()
    }

    // MARK: - Setup

    private func setupUI() {
        // Gradient background
        view.layer.insertSublayer(gradientLayer, at: 0)

        // Add subviews
        view.addSubview(iconContainer)
        iconContainer.addSubview(iconImageView)
        view.addSubview(appNameLabel)
        view.addSubview(taglineLabel)

        // Constraints - center everything
        NSLayoutConstraint.activate([
            // Icon container
            iconContainer.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            iconContainer.centerYAnchor.constraint(equalTo: view.centerYAnchor, constant: -60),
            iconContainer.widthAnchor.constraint(equalToConstant: 80),
            iconContainer.heightAnchor.constraint(equalToConstant: 80),

            // Icon inside container
            iconImageView.centerXAnchor.constraint(equalTo: iconContainer.centerXAnchor),
            iconImageView.centerYAnchor.constraint(equalTo: iconContainer.centerYAnchor),
            iconImageView.widthAnchor.constraint(equalToConstant: 50),
            iconImageView.heightAnchor.constraint(equalToConstant: 50),

            // App name
            appNameLabel.topAnchor.constraint(equalTo: iconContainer.bottomAnchor, constant: 24),
            appNameLabel.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            appNameLabel.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 32),
            appNameLabel.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -32),

            // Tagline
            taglineLabel.topAnchor.constraint(equalTo: appNameLabel.bottomAnchor, constant: 8),
            taglineLabel.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            taglineLabel.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 32),
            taglineLabel.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -32),
        ])

        // Start with elements invisible + small
        iconContainer.transform = CGAffineTransform(scaleX: 0.3, y: 0.3)
        iconContainer.alpha = 0
        appNameLabel.alpha = 0
        appNameLabel.transform = CGAffineTransform(translationX: 0, y: 20)
        taglineLabel.alpha = 0
        taglineLabel.transform = CGAffineTransform(translationX: 0, y: 20)
    }

    // MARK: - Breathe-Out Animation

    private func runBreatheOutAnimation() {
        // Phase 1: Icon breathes in (scale up from small to slightly large)
        UIView.animate(
            withDuration: 0.6,
            delay: 0.1,
            usingSpringWithDamping: 0.6,
            initialSpringVelocity: 0.5,
            options: .curveEaseOut,
            animations: {
                self.iconContainer.transform = CGAffineTransform(scaleX: 1.15, y: 1.15)
                self.iconContainer.alpha = 1
            },
            completion: { _ in
                // Phase 2: Breathe out (settle to normal size)
                UIView.animate(
                    withDuration: 0.4,
                    delay: 0,
                    usingSpringWithDamping: 0.8,
                    initialSpringVelocity: 0.3,
                    options: .curveEaseInOut,
                    animations: {
                        self.iconContainer.transform = .identity
                    },
                    completion: nil
                )
            }
        )

        // Phase 3: Fade in app name
        UIView.animate(
            withDuration: 0.5,
            delay: 0.5,
            options: .curveEaseOut,
            animations: {
                self.appNameLabel.alpha = 1
                self.appNameLabel.transform = .identity
            },
            completion: nil
        )

        // Phase 4: Fade in tagline
        UIView.animate(
            withDuration: 0.5,
            delay: 0.7,
            options: .curveEaseOut,
            animations: {
                self.taglineLabel.alpha = 1
                self.taglineLabel.transform = .identity
            },
            completion: nil
        )

        // Phase 5: Pulse breathe loop once, then transition
        UIView.animate(
            withDuration: 0.6,
            delay: 1.4,
            options: .curveEaseInOut,
            animations: {
                self.iconContainer.transform = CGAffineTransform(scaleX: 1.08, y: 1.08)
            },
            completion: { _ in
                UIView.animate(
                    withDuration: 0.4,
                    delay: 0,
                    options: .curveEaseInOut,
                    animations: {
                        self.iconContainer.transform = .identity
                    },
                    completion: { _ in
                        // Final: fade everything out and transition
                        UIView.animate(
                            withDuration: 0.3,
                            delay: 0.1,
                            options: .curveEaseIn,
                            animations: {
                                self.view.alpha = 0
                            },
                            completion: { _ in
                                self.onAnimationComplete?()
                            }
                        )
                    }
                )
            }
        )
    }
}
