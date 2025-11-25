//
//  GoogleDriveViewController.swift
//  MenuOCR
//
//  Created by MenuOCR on 2025-01-07.
//

import UIKit

class GoogleDriveViewController: UIViewController {

    private let scrollView = UIScrollView()
    private let contentView = UIView()

    // Status
    private let statusLabel = UILabel()

    // Buttons
    private let signInButton = UIButton()
    private let refreshButton = UIButton()
    private let syncButton = UIButton()
    private let settingsButton = UIButton()

    // File list (placeholder)
    private let filesCard = UIView()
    private let filesTitleLabel = UILabel()
    private let filesListLabel = UILabel()

    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
        setupConstraints()
        updateStatus("Google Drive integration ready (demo mode)")
    }

    private func setupUI() {
        view.backgroundColor = UIColor.systemGray6

        // Status
        statusLabel.textAlignment = .center
        statusLabel.font = UIFont.systemFont(ofSize: 16)
        statusLabel.textColor = .gray
        statusLabel.numberOfLines = 0

        // Buttons
        signInButton.setTitle("🔐 Sign In to Google Drive", for: .normal)
        signInButton.backgroundColor = UIColor.systemBlue
        signInButton.setTitleColor(.white, for: .normal)
        signInButton.layer.cornerRadius = 8
        signInButton.addTarget(self, action: #selector(signInTapped), for: .touchUpInside)

        refreshButton.setTitle("🔄 Refresh Files", for: .normal)
        refreshButton.backgroundColor = UIColor.systemGreen
        refreshButton.setTitleColor(.white, for: .normal)
        refreshButton.layer.cornerRadius = 8
        refreshButton.addTarget(self, action: #selector(refreshTapped), for: .touchUpInside)

        syncButton.setTitle("☁️ Sync with Drive", for: .normal)
        syncButton.backgroundColor = UIColor.systemOrange
        syncButton.setTitleColor(.white, for: .normal)
        syncButton.layer.cornerRadius = 8
        syncButton.addTarget(self, action: #selector(syncTapped), for: .touchUpInside)

        settingsButton.setTitle("⚙️ Drive Settings", for: .normal)
        settingsButton.backgroundColor = UIColor.systemGray
        settingsButton.setTitleColor(.white, for: .normal)
        settingsButton.layer.cornerRadius = 8
        settingsButton.addTarget(self, action: #selector(settingsTapped), for: .touchUpInside)

        // Files card
        filesCard.backgroundColor = .white
        filesCard.layer.cornerRadius = 12
        filesCard.layer.shadowColor = UIColor.black.cgColor
        filesCard.layer.shadowOffset = CGSize(width: 0, height: 2)
        filesCard.layer.shadowOpacity = 0.1
        filesCard.layer.shadowRadius = 4

        filesTitleLabel.text = "📁 Recent Files"
        filesTitleLabel.font = UIFont.boldSystemFont(ofSize: 18)
        filesTitleLabel.textColor = .black

        filesListLabel.text = """
        • menu_scan_2025-01-07.jpg
        • restaurant_receipt.pdf
        • pizza_menu_ocr.txt
        • dinner_receipt.jpg
        • cafe_menu_scan.png
        """
        filesListLabel.font = UIFont.systemFont(ofSize: 14)
        filesListLabel.textColor = .gray
        filesListLabel.numberOfLines = 0

        // Layout
        scrollView.translatesAutoresizingMaskIntoConstraints = false
        contentView.translatesAutoresizingMaskIntoConstraints = false

        view.addSubview(scrollView)
        scrollView.addSubview(contentView)

        contentView.addSubview(statusLabel)
        contentView.addSubview(signInButton)
        contentView.addSubview(refreshButton)
        contentView.addSubview(syncButton)
        contentView.addSubview(settingsButton)
        contentView.addSubview(filesCard)

        filesCard.addSubview(filesTitleLabel)
        filesCard.addSubview(filesListLabel)
    }

    private func setupConstraints() {
        // Scroll view
        NSLayoutConstraint.activate([
            scrollView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            scrollView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            scrollView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            scrollView.bottomAnchor.constraint(equalTo: view.bottomAnchor),

            contentView.topAnchor.constraint(equalTo: scrollView.topAnchor),
            contentView.leadingAnchor.constraint(equalTo: scrollView.leadingAnchor),
            contentView.trailingAnchor.constraint(equalTo: scrollView.trailingAnchor),
            contentView.bottomAnchor.constraint(equalTo: scrollView.bottomAnchor),
            contentView.widthAnchor.constraint(equalTo: scrollView.widthAnchor)
        ])

        // Status
        statusLabel.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            statusLabel.topAnchor.constraint(equalTo: contentView.topAnchor, constant: 20),
            statusLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            statusLabel.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16)
        ])

        // Buttons
        signInButton.translatesAutoresizingMaskIntoConstraints = false
        refreshButton.translatesAutoresizingMaskIntoConstraints = false
        syncButton.translatesAutoresizingMaskIntoConstraints = false
        settingsButton.translatesAutoresizingMaskIntoConstraints = false

        NSLayoutConstraint.activate([
            signInButton.topAnchor.constraint(equalTo: statusLabel.bottomAnchor, constant: 30),
            signInButton.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            signInButton.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            signInButton.heightAnchor.constraint(equalToConstant: 50),

            refreshButton.topAnchor.constraint(equalTo: signInButton.bottomAnchor, constant: 12),
            refreshButton.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            refreshButton.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            refreshButton.heightAnchor.constraint(equalToConstant: 50),

            syncButton.topAnchor.constraint(equalTo: refreshButton.bottomAnchor, constant: 12),
            syncButton.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            syncButton.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            syncButton.heightAnchor.constraint(equalToConstant: 50),

            settingsButton.topAnchor.constraint(equalTo: syncButton.bottomAnchor, constant: 12),
            settingsButton.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            settingsButton.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            settingsButton.heightAnchor.constraint(equalToConstant: 50)
        ])

        // Files card
        filesCard.translatesAutoresizingMaskIntoConstraints = false
        filesTitleLabel.translatesAutoresizingMaskIntoConstraints = false
        filesListLabel.translatesAutoresizingMaskIntoConstraints = false

        NSLayoutConstraint.activate([
            filesCard.topAnchor.constraint(equalTo: settingsButton.bottomAnchor, constant: 30),
            filesCard.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            filesCard.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            filesCard.heightAnchor.constraint(equalToConstant: 200),
            filesCard.bottomAnchor.constraint(equalTo: contentView.bottomAnchor, constant: -20),

            filesTitleLabel.topAnchor.constraint(equalTo: filesCard.topAnchor, constant: 16),
            filesTitleLabel.leadingAnchor.constraint(equalTo: filesCard.leadingAnchor, constant: 16),
            filesTitleLabel.trailingAnchor.constraint(equalTo: filesCard.trailingAnchor, constant: -16),

            filesListLabel.topAnchor.constraint(equalTo: filesTitleLabel.bottomAnchor, constant: 12),
            filesListLabel.leadingAnchor.constraint(equalTo: filesCard.leadingAnchor, constant: 16),
            filesListLabel.trailingAnchor.constraint(equalTo: filesCard.trailingAnchor, constant: -16)
        ])
    }

    private func updateStatus(_ message: String) {
        statusLabel.text = message
    }

    @objc private func signInTapped() {
        showAlert(title: "Google Drive", message: "Google Drive sign-in would be implemented here")
    }

    @objc private func refreshTapped() {
        updateStatus("🔄 Refreshing files from Google Drive...")
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) { [weak self] in
            self?.updateStatus("✅ Files refreshed successfully")
        }
    }

    @objc private func syncTapped() {
        updateStatus("☁️ Syncing with Google Drive...")
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) { [weak self] in
            self?.updateStatus("✅ Sync completed successfully")
        }
    }

    @objc private func settingsTapped() {
        showAlert(title: "Drive Settings", message: "Google Drive settings and preferences")
    }

    private func showAlert(title: String, message: String) {
        let alert = UIAlertController(title: title, message: message, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "OK", style: .default))
        present(alert, animated: true)
    }
}