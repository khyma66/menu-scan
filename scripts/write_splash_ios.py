#!/usr/bin/env python3
"""Rewrite SplashViewController.swift:
- Remove 'Fooder' text label + tagline
- Just logo, larger, centered on deep purple gradient
- Breathe animation on logo only, then transition
"""

TARGET = "/Users/mohanakrishnanarsupalli/menu-ocr/menu-ocr-ios/MenuOCR/MenuOCR/Views/SplashViewController.swift"

content = r'''//
//  SplashViewController.swift
//  MenuOCR
//
//  Splash screen — logo-only with breathe-out animation
//  Rich deep gradient, no text, device-adaptive centering
//

import UIKit

class SplashViewController: UIViewController {

    // MARK: - Completion Handler
    var onAnimationComplete: (() -> Void)?

    // MARK: - UI Components

    /// Deep purple gradient background
    private let gradientLayer: CAGradientLayer = {
        let layer = CAGradientLayer()
        layer.colors = [
            UIColor(red: 0.176, green: 0.106, blue: 0.412, alpha: 1.0).cgColor, // #2D1B69
            UIColor(red: 0.486, green: 0.227, blue: 0.929, alpha: 1.0).cgColor  // #7C3AED
        ]
        layer.startPoint = CGPoint(x: 0.2, y: 0)
        layer.endPoint = CGPoint(x: 0.8, y: 1)
        return layer
    }()

    /// Subtle radial glow behind logo
    private let glowView: UIView = {
        let v = UIView()
        v.backgroundColor = UIColor.white.withAlphaComponent(0.08)
        v.layer.cornerRadius = 90
        v.translatesAutoresizingMaskIntoConstraints = false
        return v
    }()

    /// Logo image (no white bg — shown on gradient)
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
        iv.layer.cornerRadius = 28
        // Drop shadow for depth
        iv.layer.shadowColor = UIColor.black.cgColor
        iv.layer.shadowOffset = CGSize(width: 0, height: 6)
        iv.layer.shadowOpacity = 0.3
        iv.layer.shadowRadius = 16
        iv.layer.masksToBounds = false
        iv.translatesAutoresizingMaskIntoConstraints = false
        return iv
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

        // Device-adaptive logo size
        let logoSize: CGFloat = min(UIScreen.main.bounds.width * 0.4, 160)

        NSLayoutConstraint.activate([
            glowView.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            glowView.centerYAnchor.constraint(equalTo: view.centerYAnchor),
            glowView.widthAnchor.constraint(equalToConstant: 180),
            glowView.heightAnchor.constraint(equalToConstant: 180),

            logoImageView.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            logoImageView.centerYAnchor.constraint(equalTo: view.centerYAnchor),
            logoImageView.widthAnchor.constraint(equalToConstant: logoSize),
            logoImageView.heightAnchor.constraint(equalToConstant: logoSize),
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
                self.logoImageView.transform = CGAffineTransform(scaleX: 1.15, y: 1.15)
                self.logoImageView.alpha = 1
                self.glowView.transform = CGAffineTransform(scaleX: 1.1, y: 1.1)
                self.glowView.alpha = 1
            },
            completion: { _ in
                // Phase 2: Settle to normal
                UIView.animate(withDuration: 0.35, delay: 0,
                    usingSpringWithDamping: 0.8, initialSpringVelocity: 0.3,
                    options: .curveEaseInOut,
                    animations: {
                        self.logoImageView.transform = .identity
                        self.glowView.transform = .identity
                    }, completion: nil)
            }
        )

        // Phase 3: Gentle pulse, then fade out and transition
        UIView.animate(
            withDuration: 0.5, delay: 1.2, options: .curveEaseInOut,
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
                        // Fade out
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
'''

with open(TARGET, 'w') as f:
    f.write(content)

lines = content.count('\n')
print(f"SplashVC written: {lines} lines")
print(f"No 'Fooder' text: {'Fooder' not in content}")
print(f"No tagline: {'tagline' not in content.split('//')[0]}")
print(f"Has gradient: {'#2D1B69' in content}")
print(f"Has glowView: {'glowView' in content}")
