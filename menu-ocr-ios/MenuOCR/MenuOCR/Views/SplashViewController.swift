//
//  SplashViewController.swift
//  MenuOCR
//
//  Splash screen — large attractive logo with rich gradient, no box
//  Full-bleed gradient adapts to every device
//

import UIKit

class SplashViewController: UIViewController {

    // MARK: - Completion Handler
    var onAnimationComplete: (() -> Void)?

    // MARK: - UI Components

    /// Rich deep-purple gradient (fills entire screen on every device)
    private let gradientLayer: CAGradientLayer = {
        let layer = CAGradientLayer()
        layer.colors = [
            UIColor(red: 0.12, green: 0.05, blue: 0.35, alpha: 1.0).cgColor,   // deep indigo top
            UIColor(red: 0.30, green: 0.10, blue: 0.60, alpha: 1.0).cgColor,   // rich purple mid
            UIColor(red: 0.486, green: 0.227, blue: 0.929, alpha: 1.0).cgColor  // vibrant violet bottom
        ]
        layer.locations = [0.0, 0.45, 1.0]
        layer.startPoint = CGPoint(x: 0.5, y: 0)
        layer.endPoint = CGPoint(x: 0.5, y: 1)
        return layer
    }()

    /// Soft radial glow behind logo
    private let glowView: UIView = {
        let v = UIView()
        v.backgroundColor = UIColor.white.withAlphaComponent(0.06)
        v.layer.cornerRadius = 110
        v.translatesAutoresizingMaskIntoConstraints = false
        return v
    }()

    /// Logo — no box, no red/rectangle background. Just the image centered.
    private let logoImageView: UIImageView = {
        let iv = UIImageView()
        if let img = UIImage(named: "fooder_logo") {
            iv.image = img
        } else if let path = Bundle.main.path(forResource: "fooder_logo", ofType: "jpg"),
                  let img = UIImage(contentsOfFile: path) {
            iv.image = img
        }
        iv.contentMode = .scaleAspectFit
        iv.clipsToBounds = true
        iv.backgroundColor = .clear                 // NO background colour
        iv.layer.cornerRadius = 40                  // soft round, not rectangular
        iv.layer.borderWidth = 0                    // no border
        // Soft shadow for floating look
        iv.layer.shadowColor = UIColor.black.cgColor
        iv.layer.shadowOffset = CGSize(width: 0, height: 8)
        iv.layer.shadowOpacity = 0.25
        iv.layer.shadowRadius = 24
        iv.layer.masksToBounds = false
        iv.translatesAutoresizingMaskIntoConstraints = false
        return iv
    }()

    /// Elegant "Fooder" text below logo
    private let brandLabel: UILabel = {
        let lbl = UILabel()
        lbl.text = "Fooder"
        lbl.font = .systemFont(ofSize: 34, weight: .bold)
        lbl.textColor = .white
        lbl.textAlignment = .center
        lbl.alpha = 0
        lbl.translatesAutoresizingMaskIntoConstraints = false
        return lbl
    }()

    /// Tagline
    private let taglineLabel: UILabel = {
        let lbl = UILabel()
        lbl.text = "Scan. Discover. Enjoy."
        lbl.font = .systemFont(ofSize: 16, weight: .medium)
        lbl.textColor = UIColor.white.withAlphaComponent(0.65)
        lbl.textAlignment = .center
        lbl.alpha = 0
        lbl.translatesAutoresizingMaskIntoConstraints = false
        return lbl
    }()

    // MARK: - Lifecycle

    override func viewDidLoad() {
        super.viewDidLoad()
        // Set background color as fallback (same as gradient start)
        view.backgroundColor = UIColor(red: 0.12, green: 0.05, blue: 0.35, alpha: 1.0)
        setupUI()
    }

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        // Always cover the full screen, including safe areas
        gradientLayer.frame = view.bounds
    }

    override var preferredStatusBarStyle: UIStatusBarStyle { .lightContent }

    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        runBreatheOutAnimation()
    }

    // MARK: - Setup

    private func setupUI() {
        view.layer.insertSublayer(gradientLayer, at: 0)

        view.addSubview(glowView)
        view.addSubview(logoImageView)
        view.addSubview(brandLabel)
        view.addSubview(taglineLabel)

        // Adaptive logo size — big and bold, proportional to screen
        let screenW = UIScreen.main.bounds.width
        let logoSize: CGFloat = min(screenW * 0.48, 200)

        NSLayoutConstraint.activate([
            glowView.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            glowView.centerYAnchor.constraint(equalTo: view.centerYAnchor, constant: -30),
            glowView.widthAnchor.constraint(equalToConstant: 220),
            glowView.heightAnchor.constraint(equalToConstant: 220),

            logoImageView.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            logoImageView.centerYAnchor.constraint(equalTo: view.centerYAnchor, constant: -30),
            logoImageView.widthAnchor.constraint(equalToConstant: logoSize),
            logoImageView.heightAnchor.constraint(equalToConstant: logoSize),

            brandLabel.topAnchor.constraint(equalTo: logoImageView.bottomAnchor, constant: 20),
            brandLabel.centerXAnchor.constraint(equalTo: view.centerXAnchor),

            taglineLabel.topAnchor.constraint(equalTo: brandLabel.bottomAnchor, constant: 6),
            taglineLabel.centerXAnchor.constraint(equalTo: view.centerXAnchor),
        ])

        // Start invisible + small
        logoImageView.transform = CGAffineTransform(scaleX: 0.3, y: 0.3)
        logoImageView.alpha = 0
        glowView.transform = CGAffineTransform(scaleX: 0.5, y: 0.5)
        glowView.alpha = 0
    }

    // MARK: - Breathe-Out Animation

    private func runBreatheOutAnimation() {
        // Phase 1: Logo + glow spring in (0-600ms)
        UIView.animate(
            withDuration: 0.6, delay: 0.15,
            usingSpringWithDamping: 0.6, initialSpringVelocity: 0.5,
            options: .curveEaseOut,
            animations: {
                self.logoImageView.transform = CGAffineTransform(scaleX: 1.12, y: 1.12)
                self.logoImageView.alpha = 1
                self.glowView.transform = CGAffineTransform(scaleX: 1.1, y: 1.1)
                self.glowView.alpha = 1
            },
            completion: { _ in
                // Phase 2: Settle + reveal text
                UIView.animate(withDuration: 0.35, delay: 0,
                    usingSpringWithDamping: 0.8, initialSpringVelocity: 0.3,
                    options: .curveEaseInOut,
                    animations: {
                        self.logoImageView.transform = .identity
                        self.glowView.transform = .identity
                    }, completion: nil)

                // Fade in brand text
                UIView.animate(withDuration: 0.4, delay: 0.1, options: .curveEaseOut, animations: {
                    self.brandLabel.alpha = 1
                    self.taglineLabel.alpha = 1
                })
            }
        )

        // Phase 3: Gentle pulse, then fade out and transition
        UIView.animate(
            withDuration: 0.5, delay: 1.3, options: .curveEaseInOut,
            animations: {
                self.logoImageView.transform = CGAffineTransform(scaleX: 1.06, y: 1.06)
            },
            completion: { _ in
                UIView.animate(
                    withDuration: 0.35, delay: 0, options: .curveEaseInOut,
                    animations: {
                        self.logoImageView.transform = .identity
                    },
                    completion: { _ in
                        // Fade out everything
                        UIView.animate(withDuration: 0.3, delay: 0.1, options: .curveEaseIn,
                            animations: { self.view.alpha = 0 },
                            completion: { _ in self.onAnimationComplete?() }
                        )
                    }
                )
            }
        )
    }
}
