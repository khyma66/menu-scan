//
//  SplashViewController.swift
//  MenuOCR
//
//  Splash screen — light violet bg, Fooder brand with tomato-O logo
//

import UIKit

class SplashViewController: UIViewController {

    // MARK: - Completion Handler
    var onAnimationComplete: (() -> Void)?

    // MARK: - Theme
    private let violetPrimary = UIColor(red: 0.98, green: 0.239, blue: 0.18, alpha: 1.0) // #FA3D2E
    private let violetBg      = UIColor(red: 1.0, green: 1.0, blue: 1.0, alpha: 1.0) // white

    // MARK: - UI Components

    /// Soft radial glow behind logo
    private let glowView: UIView = {
        let v = UIView()
        v.backgroundColor = UIColor(red: 0.98, green: 0.239, blue: 0.18, alpha: 0.08)
        v.layer.cornerRadius = 90
        v.translatesAutoresizingMaskIntoConstraints = false
        return v
    }()

    /// Tomato "O" icon — a red circle with a green leaf
    private let tomatoContainer: UIView = {
        let v = UIView()
        v.translatesAutoresizingMaskIntoConstraints = false
        return v
    }()

    /// "Fooder" brand label (the 'oo' will look like it includes the tomato)
    private let brandLabel: UILabel = {
        let lbl = UILabel()
        lbl.textAlignment = .center
        lbl.alpha = 0
        lbl.translatesAutoresizingMaskIntoConstraints = false
        return lbl
    }()

    /// Tagline
    private let taglineLabel: UILabel = {
        let lbl = UILabel()
        lbl.text = "Scan menus. Eat smarter."
        lbl.font = .systemFont(ofSize: 16, weight: .medium)
        lbl.textColor = UIColor(red: 0.443, green: 0.443, blue: 0.51, alpha: 1.0) // #717182
        lbl.textAlignment = .center
        lbl.alpha = 0
        lbl.translatesAutoresizingMaskIntoConstraints = false
        return lbl
    }()

    // MARK: - Lifecycle

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = violetBg
        setupUI()
    }

    override var preferredStatusBarStyle: UIStatusBarStyle { .darkContent }

    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        runBreatheOutAnimation()
    }

    // MARK: - Setup

    private func setupUI() {
        view.addSubview(glowView)
        view.addSubview(tomatoContainer)
        view.addSubview(brandLabel)
        view.addSubview(taglineLabel)

        // Build tomato icon
        buildTomatoIcon()

        // Build brand label with styled text
        let attr = NSMutableAttributedString()
        let mainFont = UIFont.systemFont(ofSize: 42, weight: .heavy)
        let violet = violetPrimary

        attr.append(NSAttributedString(string: "F", attributes: [.font: mainFont, .foregroundColor: violet]))
        // First 'o' – styled red (tomato)
        attr.append(NSAttributedString(string: "o", attributes: [
            .font: mainFont, .foregroundColor: UIColor.systemRed
        ]))
        attr.append(NSAttributedString(string: "o", attributes: [.font: mainFont, .foregroundColor: violet]))
        attr.append(NSAttributedString(string: "d", attributes: [.font: mainFont, .foregroundColor: violet]))
        attr.append(NSAttributedString(string: "e", attributes: [.font: mainFont, .foregroundColor: violet]))
        attr.append(NSAttributedString(string: "r", attributes: [.font: mainFont, .foregroundColor: violet]))
        brandLabel.attributedText = attr

        let tomatoSize: CGFloat = 100

        NSLayoutConstraint.activate([
            glowView.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            glowView.centerYAnchor.constraint(equalTo: view.centerYAnchor, constant: -60),
            glowView.widthAnchor.constraint(equalToConstant: 180),
            glowView.heightAnchor.constraint(equalToConstant: 180),

            tomatoContainer.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            tomatoContainer.centerYAnchor.constraint(equalTo: view.centerYAnchor, constant: -60),
            tomatoContainer.widthAnchor.constraint(equalToConstant: tomatoSize),
            tomatoContainer.heightAnchor.constraint(equalToConstant: tomatoSize),

            brandLabel.topAnchor.constraint(equalTo: tomatoContainer.bottomAnchor, constant: 18),
            brandLabel.centerXAnchor.constraint(equalTo: view.centerXAnchor),

            taglineLabel.topAnchor.constraint(equalTo: brandLabel.bottomAnchor, constant: 6),
            taglineLabel.centerXAnchor.constraint(equalTo: view.centerXAnchor),
        ])

        // Start invisible + small
        tomatoContainer.transform = CGAffineTransform(scaleX: 0.3, y: 0.3)
        tomatoContainer.alpha = 0
        glowView.transform = CGAffineTransform(scaleX: 0.5, y: 0.5)
        glowView.alpha = 0
    }

    private func buildTomatoIcon() {
        // Red tomato body
        let body = UIView()
        body.backgroundColor = UIColor.systemRed
        body.layer.cornerRadius = 42
        body.translatesAutoresizingMaskIntoConstraints = false
        tomatoContainer.addSubview(body)

        // Green leaf (small triangle-ish shape)
        let leaf = UIView()
        leaf.backgroundColor = UIColor(red: 0.13, green: 0.72, blue: 0.30, alpha: 1.0)
        leaf.layer.cornerRadius = 8
        leaf.transform = CGAffineTransform(rotationAngle: .pi / 4)
        leaf.translatesAutoresizingMaskIntoConstraints = false
        tomatoContainer.addSubview(leaf)

        // White "O" letter in center
        let oLabel = UILabel()
        oLabel.text = "O"
        oLabel.font = .systemFont(ofSize: 48, weight: .heavy)
        oLabel.textColor = .white
        oLabel.textAlignment = .center
        oLabel.translatesAutoresizingMaskIntoConstraints = false
        tomatoContainer.addSubview(oLabel)

        NSLayoutConstraint.activate([
            body.centerXAnchor.constraint(equalTo: tomatoContainer.centerXAnchor),
            body.centerYAnchor.constraint(equalTo: tomatoContainer.centerYAnchor, constant: 4),
            body.widthAnchor.constraint(equalToConstant: 84),
            body.heightAnchor.constraint(equalToConstant: 84),

            leaf.centerXAnchor.constraint(equalTo: tomatoContainer.centerXAnchor),
            leaf.bottomAnchor.constraint(equalTo: body.topAnchor, constant: 10),
            leaf.widthAnchor.constraint(equalToConstant: 20),
            leaf.heightAnchor.constraint(equalToConstant: 20),

            oLabel.centerXAnchor.constraint(equalTo: body.centerXAnchor),
            oLabel.centerYAnchor.constraint(equalTo: body.centerYAnchor),
        ])

        // Subtle shadow on tomato
        body.layer.shadowColor = UIColor.systemRed.cgColor
        body.layer.shadowOffset = CGSize(width: 0, height: 6)
        body.layer.shadowOpacity = 0.3
        body.layer.shadowRadius = 12
        body.layer.masksToBounds = false
    }

    // MARK: - Breathe-Out Animation

    private func runBreatheOutAnimation() {
        UIView.animate(
            withDuration: 0.6, delay: 0.15,
            usingSpringWithDamping: 0.6, initialSpringVelocity: 0.5,
            options: .curveEaseOut,
            animations: {
                self.tomatoContainer.transform = CGAffineTransform(scaleX: 1.12, y: 1.12)
                self.tomatoContainer.alpha = 1
                self.glowView.transform = CGAffineTransform(scaleX: 1.1, y: 1.1)
                self.glowView.alpha = 1
            },
            completion: { _ in
                UIView.animate(withDuration: 0.35, delay: 0,
                    usingSpringWithDamping: 0.8, initialSpringVelocity: 0.3,
                    options: .curveEaseInOut,
                    animations: {
                        self.tomatoContainer.transform = .identity
                        self.glowView.transform = .identity
                    }, completion: nil)

                UIView.animate(withDuration: 0.4, delay: 0.1, options: .curveEaseOut, animations: {
                    self.brandLabel.alpha = 1
                    self.taglineLabel.alpha = 1
                })
            }
        )

        UIView.animate(
            withDuration: 0.5, delay: 1.3, options: .curveEaseInOut,
            animations: {
                self.tomatoContainer.transform = CGAffineTransform(scaleX: 1.06, y: 1.06)
            },
            completion: { _ in
                UIView.animate(
                    withDuration: 0.35, delay: 0, options: .curveEaseInOut,
                    animations: {
                        self.tomatoContainer.transform = .identity
                    },
                    completion: { _ in
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
