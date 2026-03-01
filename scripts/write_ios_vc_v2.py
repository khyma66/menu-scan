#!/usr/bin/env python3
"""Write the updated MenuOCRViewController.swift v2
Fixes:
- Keep images above results after processing (don't clear)
- Detail view: proper back button alignment with drag handle
- Groq empty fields: fallback inference for all detail sections
- UX playbook: 16pt body, 1.5x line height styling, off-black text, proper whitespace
- Export/Share visible
"""

TARGET = "/Users/mohanakrishnanarsupalli/menu-ocr/menu-ocr-ios/MenuOCR/MenuOCR/Views/MenuOCRViewController.swift"

content = r"""//
//  MenuOCRViewController.swift
//  MenuOCR
//
//  Menu OCR with camera/gallery support - full Gemini+Groq pipeline
//  UX Playbook compliant: proper typography, spacing, contrast, visual hierarchy
//

import UIKit
import Vision
import PhotosUI

class MenuOCRViewController: UIViewController {

    // MARK: - Services

    var apiService: ApiService?

    // MARK: - State

    private var selectedImages: [UIImage] = []
    private var processedImages: [UIImage] = []  // Keep processed images for display
    private var accumulatedMenuItems: [MenuItem] = []
    private var processingCancelled = false
    private var isTranslateOn = false
    private var selectedLanguage = "en"
    private let availableLanguages = [
        ("en", "English"), ("es", "Spanish"), ("fr", "French"),
        ("de", "German"), ("it", "Italian"), ("pt", "Portuguese"),
        ("zh", "Chinese"), ("ja", "Japanese"), ("ko", "Korean"),
        ("hi", "Hindi"), ("ar", "Arabic"), ("ru", "Russian")
    ]
    private var tableHeightConstraint: NSLayoutConstraint?

    // MARK: - Brand colours
    private let brandRed = UIColor(red: 250/255, green: 61/255, blue: 46/255, alpha: 1) // #FA3D2E
    private let scanPurple = UIColor(red: 0.486, green: 0.227, blue: 0.929, alpha: 1) // #7C3AED
    // UX playbook: off-black for text (not pure #000)
    private let textPrimary = UIColor(red: 0.12, green: 0.12, blue: 0.14, alpha: 1) // #1F1F24
    private let textSecondary = UIColor(red: 0.4, green: 0.4, blue: 0.45, alpha: 1) // #666673

    // MARK: - UI Components

    private let scrollView = UIScrollView()
    private let contentView = UIView()

    // Header
    private let headerView = UIView()
    private let titleLabel = UILabel()
    private let profileButton = UIButton()

    // Upload card
    private let uploadCard = UIView()
    private let captureButton = UIButton()
    private let galleryButton = UIButton()

    // Images preview (shown both before and after processing)
    private let imagesPreviewCard = UIView()
    private let imagesPreviewScrollView = UIScrollView()
    private let imagesStackView = UIStackView()
    private let addMoreButton = UIButton()

    // Process / cancel
    private let processButton = UIButton()

    // Loading
    private let loadingContainer = UIView()
    private let loadingIndicator = UIActivityIndicatorView(style: .large)
    private let loadingLabel = UILabel()

    // Translation row
    private let translationRow = UIView()
    private let translateSwitch = UISwitch()
    private let translateLabel = UILabel()
    private let languagePicker = UIButton()

    // Results
    private let resultsHeaderLabel = UILabel()
    private let resultsCard = UIView()
    private let resultsTableView = UITableView()

    // Action buttons
    private let actionButtonsContainer = UIView()
    private let resetButton = UIButton()
    private let exportButton = UIButton()

    // MARK: - Lifecycle

    init() { super.init(nibName: nil, bundle: nil) }
    required init?(coder: NSCoder) { super.init(coder: coder) }

    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
        setupConstraints()
        checkPermissions()
    }

    // MARK: - UI Setup

    private func setupUI() {
        view.backgroundColor = UIColor(red: 0.965, green: 0.965, blue: 0.975, alpha: 1) // light gray bg

        // Status bar bg
        let statusBarBg = UIView()
        statusBarBg.backgroundColor = scanPurple
        statusBarBg.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(statusBarBg)
        NSLayoutConstraint.activate([
            statusBarBg.topAnchor.constraint(equalTo: view.topAnchor),
            statusBarBg.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            statusBarBg.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            statusBarBg.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor)
        ])

        scrollView.translatesAutoresizingMaskIntoConstraints = false
        contentView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(scrollView)
        scrollView.addSubview(contentView)

        setupHeader()
        setupUploadCard()
        setupImagesPreview()
        setupProcessButton()
        setupLoading()
        setupTranslationRow()
        setupResults()
        setupActionButtons()
    }

    private func setupHeader() {
        headerView.backgroundColor = scanPurple
        headerView.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(headerView)

        titleLabel.text = "Menu Scan"
        titleLabel.font = .systemFont(ofSize: 20, weight: .bold)
        titleLabel.textColor = .white
        titleLabel.textAlignment = .center
        titleLabel.translatesAutoresizingMaskIntoConstraints = false
        headerView.addSubview(titleLabel)

        profileButton.setImage(UIImage(systemName: "person.circle.fill"), for: .normal)
        profileButton.tintColor = .white
        profileButton.addTarget(self, action: #selector(profileTapped), for: .touchUpInside)
        profileButton.translatesAutoresizingMaskIntoConstraints = false
        headerView.addSubview(profileButton)
    }

    private func setupUploadCard() {
        uploadCard.backgroundColor = .systemBackground
        uploadCard.layer.cornerRadius = 14
        uploadCard.layer.shadowColor = UIColor.black.cgColor
        uploadCard.layer.shadowOffset = CGSize(width: 0, height: 2)
        uploadCard.layer.shadowOpacity = 0.08
        uploadCard.layer.shadowRadius = 10
        uploadCard.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(uploadCard)

        captureButton.setTitle("\u{1F4F7} Capture Image", for: .normal)
        captureButton.backgroundColor = brandRed
        captureButton.setTitleColor(.white, for: .normal)
        captureButton.titleLabel?.font = .systemFont(ofSize: 16, weight: .semibold)
        captureButton.layer.cornerRadius = 12
        captureButton.addTarget(self, action: #selector(captureTapped), for: .touchUpInside)
        captureButton.translatesAutoresizingMaskIntoConstraints = false
        uploadCard.addSubview(captureButton)

        galleryButton.setTitle("\u{1F5BC}\u{FE0F} Gallery", for: .normal)
        galleryButton.backgroundColor = .systemGreen
        galleryButton.setTitleColor(.white, for: .normal)
        galleryButton.titleLabel?.font = .systemFont(ofSize: 16, weight: .semibold)
        galleryButton.layer.cornerRadius = 12
        galleryButton.addTarget(self, action: #selector(galleryTapped), for: .touchUpInside)
        galleryButton.translatesAutoresizingMaskIntoConstraints = false
        uploadCard.addSubview(galleryButton)
    }

    private func setupImagesPreview() {
        imagesPreviewCard.backgroundColor = .systemBackground
        imagesPreviewCard.layer.cornerRadius = 14
        imagesPreviewCard.layer.shadowColor = UIColor.black.cgColor
        imagesPreviewCard.layer.shadowOffset = CGSize(width: 0, height: 2)
        imagesPreviewCard.layer.shadowOpacity = 0.08
        imagesPreviewCard.layer.shadowRadius = 10
        imagesPreviewCard.isHidden = true
        imagesPreviewCard.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(imagesPreviewCard)

        let previewTitle = UILabel()
        previewTitle.text = "Selected Images"
        previewTitle.font = .systemFont(ofSize: 15, weight: .semibold)
        previewTitle.textColor = textPrimary
        previewTitle.tag = 999
        previewTitle.translatesAutoresizingMaskIntoConstraints = false
        imagesPreviewCard.addSubview(previewTitle)

        imagesPreviewScrollView.showsHorizontalScrollIndicator = false
        imagesPreviewScrollView.translatesAutoresizingMaskIntoConstraints = false
        imagesPreviewCard.addSubview(imagesPreviewScrollView)

        imagesStackView.axis = .horizontal
        imagesStackView.spacing = 8
        imagesStackView.translatesAutoresizingMaskIntoConstraints = false
        imagesPreviewScrollView.addSubview(imagesStackView)

        addMoreButton.setTitle("+ Add More", for: .normal)
        addMoreButton.backgroundColor = .systemBlue
        addMoreButton.setTitleColor(.white, for: .normal)
        addMoreButton.titleLabel?.font = .systemFont(ofSize: 13, weight: .medium)
        addMoreButton.layer.cornerRadius = 8
        addMoreButton.addTarget(self, action: #selector(galleryTapped), for: .touchUpInside)
        addMoreButton.translatesAutoresizingMaskIntoConstraints = false
        imagesPreviewCard.addSubview(addMoreButton)

        NSLayoutConstraint.activate([
            previewTitle.topAnchor.constraint(equalTo: imagesPreviewCard.topAnchor, constant: 12),
            previewTitle.leadingAnchor.constraint(equalTo: imagesPreviewCard.leadingAnchor, constant: 16),

            imagesPreviewScrollView.topAnchor.constraint(equalTo: previewTitle.bottomAnchor, constant: 8),
            imagesPreviewScrollView.leadingAnchor.constraint(equalTo: imagesPreviewCard.leadingAnchor, constant: 16),
            imagesPreviewScrollView.trailingAnchor.constraint(equalTo: imagesPreviewCard.trailingAnchor, constant: -16),
            imagesPreviewScrollView.heightAnchor.constraint(equalToConstant: 100),

            imagesStackView.topAnchor.constraint(equalTo: imagesPreviewScrollView.topAnchor),
            imagesStackView.leadingAnchor.constraint(equalTo: imagesPreviewScrollView.leadingAnchor),
            imagesStackView.trailingAnchor.constraint(equalTo: imagesPreviewScrollView.trailingAnchor),
            imagesStackView.bottomAnchor.constraint(equalTo: imagesPreviewScrollView.bottomAnchor),

            addMoreButton.topAnchor.constraint(equalTo: imagesPreviewScrollView.bottomAnchor, constant: 8),
            addMoreButton.trailingAnchor.constraint(equalTo: imagesPreviewCard.trailingAnchor, constant: -16),
            addMoreButton.bottomAnchor.constraint(equalTo: imagesPreviewCard.bottomAnchor, constant: -12),
            addMoreButton.widthAnchor.constraint(equalToConstant: 100),
            addMoreButton.heightAnchor.constraint(equalToConstant: 32)
        ])
    }

    private func setupProcessButton() {
        processButton.setTitle("\u{1F50D} Start Analysis", for: .normal)
        processButton.backgroundColor = brandRed
        processButton.setTitleColor(.white, for: .normal)
        processButton.titleLabel?.font = .systemFont(ofSize: 17, weight: .bold)
        processButton.layer.cornerRadius = 12
        processButton.isHidden = true
        processButton.addTarget(self, action: #selector(processTapped), for: .touchUpInside)
        processButton.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(processButton)
    }

    private func setupLoading() {
        loadingContainer.backgroundColor = .systemBackground
        loadingContainer.layer.cornerRadius = 12
        loadingContainer.isHidden = true
        loadingContainer.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(loadingContainer)

        loadingIndicator.color = brandRed
        loadingIndicator.translatesAutoresizingMaskIntoConstraints = false
        loadingContainer.addSubview(loadingIndicator)

        loadingLabel.text = "Processing menu..."
        loadingLabel.font = .systemFont(ofSize: 15)
        loadingLabel.textColor = textSecondary
        loadingLabel.translatesAutoresizingMaskIntoConstraints = false
        loadingContainer.addSubview(loadingLabel)
    }

    private func setupTranslationRow() {
        translationRow.isHidden = true
        translationRow.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(translationRow)

        translateLabel.text = "Translate"
        translateLabel.font = .systemFont(ofSize: 15, weight: .medium)
        translateLabel.textColor = textPrimary
        translateLabel.translatesAutoresizingMaskIntoConstraints = false
        translationRow.addSubview(translateLabel)

        translateSwitch.isOn = false
        translateSwitch.onTintColor = scanPurple
        translateSwitch.addTarget(self, action: #selector(translateToggled), for: .valueChanged)
        translateSwitch.translatesAutoresizingMaskIntoConstraints = false
        translationRow.addSubview(translateSwitch)

        languagePicker.setTitle("English \u{25BE}", for: .normal)
        languagePicker.setTitleColor(.systemBlue, for: .normal)
        languagePicker.titleLabel?.font = .systemFont(ofSize: 14, weight: .medium)
        languagePicker.addTarget(self, action: #selector(languagePickerTapped), for: .touchUpInside)
        languagePicker.translatesAutoresizingMaskIntoConstraints = false
        translationRow.addSubview(languagePicker)

        NSLayoutConstraint.activate([
            translateLabel.leadingAnchor.constraint(equalTo: translationRow.leadingAnchor),
            translateLabel.centerYAnchor.constraint(equalTo: translationRow.centerYAnchor),

            translateSwitch.leadingAnchor.constraint(equalTo: translateLabel.trailingAnchor, constant: 8),
            translateSwitch.centerYAnchor.constraint(equalTo: translationRow.centerYAnchor),

            languagePicker.trailingAnchor.constraint(equalTo: translationRow.trailingAnchor),
            languagePicker.centerYAnchor.constraint(equalTo: translationRow.centerYAnchor)
        ])
    }

    private func setupResults() {
        resultsHeaderLabel.font = .systemFont(ofSize: 17, weight: .bold)
        resultsHeaderLabel.textColor = textPrimary
        resultsHeaderLabel.isHidden = true
        resultsHeaderLabel.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(resultsHeaderLabel)

        resultsCard.backgroundColor = .systemBackground
        resultsCard.layer.cornerRadius = 14
        resultsCard.layer.shadowColor = UIColor.black.cgColor
        resultsCard.layer.shadowOffset = CGSize(width: 0, height: 2)
        resultsCard.layer.shadowOpacity = 0.08
        resultsCard.layer.shadowRadius = 10
        resultsCard.isHidden = true
        resultsCard.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(resultsCard)

        resultsTableView.register(UITableViewCell.self, forCellReuseIdentifier: "MenuItemCell")
        resultsTableView.dataSource = self
        resultsTableView.delegate = self
        resultsTableView.separatorStyle = .none
        resultsTableView.isScrollEnabled = false
        resultsTableView.backgroundColor = .clear
        resultsTableView.translatesAutoresizingMaskIntoConstraints = false
        resultsCard.addSubview(resultsTableView)
    }

    private func setupActionButtons() {
        actionButtonsContainer.isHidden = true
        actionButtonsContainer.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(actionButtonsContainer)

        resetButton.setTitle("\u{1F504} Reset", for: .normal)
        resetButton.backgroundColor = .systemRed
        resetButton.setTitleColor(.white, for: .normal)
        resetButton.titleLabel?.font = .systemFont(ofSize: 15, weight: .semibold)
        resetButton.layer.cornerRadius = 12
        resetButton.addTarget(self, action: #selector(resetTapped), for: .touchUpInside)
        resetButton.translatesAutoresizingMaskIntoConstraints = false
        actionButtonsContainer.addSubview(resetButton)

        exportButton.setTitle("\u{1F4E4} Share", for: .normal)
        exportButton.backgroundColor = .systemBlue
        exportButton.setTitleColor(.white, for: .normal)
        exportButton.titleLabel?.font = .systemFont(ofSize: 15, weight: .semibold)
        exportButton.layer.cornerRadius = 12
        exportButton.addTarget(self, action: #selector(exportTapped), for: .touchUpInside)
        exportButton.translatesAutoresizingMaskIntoConstraints = false
        actionButtonsContainer.addSubview(exportButton)
    }

    // MARK: - Constraints

    private func setupConstraints() {
        NSLayoutConstraint.activate([
            scrollView.topAnchor.constraint(equalTo: view.topAnchor),
            scrollView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            scrollView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            scrollView.bottomAnchor.constraint(equalTo: view.bottomAnchor),

            contentView.topAnchor.constraint(equalTo: scrollView.topAnchor),
            contentView.leadingAnchor.constraint(equalTo: scrollView.leadingAnchor),
            contentView.trailingAnchor.constraint(equalTo: scrollView.trailingAnchor),
            contentView.bottomAnchor.constraint(equalTo: scrollView.bottomAnchor),
            contentView.widthAnchor.constraint(equalTo: scrollView.widthAnchor),

            headerView.topAnchor.constraint(equalTo: contentView.topAnchor),
            headerView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor),
            headerView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor),
            headerView.heightAnchor.constraint(equalToConstant: 56),

            titleLabel.centerXAnchor.constraint(equalTo: headerView.centerXAnchor),
            titleLabel.centerYAnchor.constraint(equalTo: headerView.centerYAnchor),

            profileButton.trailingAnchor.constraint(equalTo: headerView.trailingAnchor, constant: -16),
            profileButton.centerYAnchor.constraint(equalTo: headerView.centerYAnchor),
            profileButton.widthAnchor.constraint(equalToConstant: 36),
            profileButton.heightAnchor.constraint(equalToConstant: 36),

            uploadCard.topAnchor.constraint(equalTo: headerView.bottomAnchor, constant: 20),
            uploadCard.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            uploadCard.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            uploadCard.heightAnchor.constraint(equalToConstant: 110),

            captureButton.leadingAnchor.constraint(equalTo: uploadCard.leadingAnchor, constant: 16),
            captureButton.trailingAnchor.constraint(equalTo: uploadCard.centerXAnchor, constant: -8),
            captureButton.centerYAnchor.constraint(equalTo: uploadCard.centerYAnchor),
            captureButton.heightAnchor.constraint(equalToConstant: 48),

            galleryButton.leadingAnchor.constraint(equalTo: uploadCard.centerXAnchor, constant: 8),
            galleryButton.trailingAnchor.constraint(equalTo: uploadCard.trailingAnchor, constant: -16),
            galleryButton.centerYAnchor.constraint(equalTo: uploadCard.centerYAnchor),
            galleryButton.heightAnchor.constraint(equalToConstant: 48),

            imagesPreviewCard.topAnchor.constraint(equalTo: uploadCard.bottomAnchor, constant: 16),
            imagesPreviewCard.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            imagesPreviewCard.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            imagesPreviewCard.heightAnchor.constraint(equalToConstant: 170),

            processButton.topAnchor.constraint(equalTo: imagesPreviewCard.bottomAnchor, constant: 16),
            processButton.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            processButton.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            processButton.heightAnchor.constraint(equalToConstant: 48),

            loadingContainer.topAnchor.constraint(equalTo: processButton.topAnchor),
            loadingContainer.leadingAnchor.constraint(equalTo: processButton.leadingAnchor),
            loadingContainer.trailingAnchor.constraint(equalTo: processButton.trailingAnchor),
            loadingContainer.heightAnchor.constraint(equalToConstant: 48),

            loadingIndicator.leadingAnchor.constraint(equalTo: loadingContainer.leadingAnchor, constant: 16),
            loadingIndicator.centerYAnchor.constraint(equalTo: loadingContainer.centerYAnchor),

            loadingLabel.leadingAnchor.constraint(equalTo: loadingIndicator.trailingAnchor, constant: 16),
            loadingLabel.centerYAnchor.constraint(equalTo: loadingContainer.centerYAnchor),

            translationRow.topAnchor.constraint(equalTo: processButton.bottomAnchor, constant: 16),
            translationRow.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 20),
            translationRow.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -20),
            translationRow.heightAnchor.constraint(equalToConstant: 36),

            resultsHeaderLabel.topAnchor.constraint(equalTo: translationRow.bottomAnchor, constant: 16),
            resultsHeaderLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 20),
            resultsHeaderLabel.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -20),

            resultsCard.topAnchor.constraint(equalTo: resultsHeaderLabel.bottomAnchor, constant: 10),
            resultsCard.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            resultsCard.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),

            resultsTableView.topAnchor.constraint(equalTo: resultsCard.topAnchor, constant: 8),
            resultsTableView.leadingAnchor.constraint(equalTo: resultsCard.leadingAnchor),
            resultsTableView.trailingAnchor.constraint(equalTo: resultsCard.trailingAnchor),
            resultsTableView.bottomAnchor.constraint(equalTo: resultsCard.bottomAnchor, constant: -8),

            actionButtonsContainer.topAnchor.constraint(equalTo: resultsCard.bottomAnchor, constant: 16),
            actionButtonsContainer.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            actionButtonsContainer.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            actionButtonsContainer.heightAnchor.constraint(equalToConstant: 48),
            actionButtonsContainer.bottomAnchor.constraint(equalTo: contentView.bottomAnchor, constant: -32),

            resetButton.leadingAnchor.constraint(equalTo: actionButtonsContainer.leadingAnchor),
            resetButton.trailingAnchor.constraint(equalTo: actionButtonsContainer.centerXAnchor, constant: -8),
            resetButton.topAnchor.constraint(equalTo: actionButtonsContainer.topAnchor),
            resetButton.bottomAnchor.constraint(equalTo: actionButtonsContainer.bottomAnchor),

            exportButton.leadingAnchor.constraint(equalTo: actionButtonsContainer.centerXAnchor, constant: 8),
            exportButton.trailingAnchor.constraint(equalTo: actionButtonsContainer.trailingAnchor),
            exportButton.topAnchor.constraint(equalTo: actionButtonsContainer.topAnchor),
            exportButton.bottomAnchor.constraint(equalTo: actionButtonsContainer.bottomAnchor)
        ])
    }

    // MARK: - Permissions

    private func checkPermissions() {
        AVCaptureDevice.requestAccess(for: .video) { granted in
            if !granted {
                DispatchQueue.main.async {
                    self.showAlert(title: "Camera Access", message: "Please enable camera access in Settings to capture menu images.")
                }
            }
        }
        PHPhotoLibrary.requestAuthorization { status in
            if status == .denied {
                DispatchQueue.main.async {
                    self.showAlert(title: "Photo Library Access", message: "Please enable photo library access in Settings to select menu images.")
                }
            }
        }
    }

    // MARK: - Actions

    @objc private func profileTapped() {
        let profileVC = ProfileViewController()
        profileVC.modalPresentationStyle = .formSheet
        present(profileVC, animated: true)
    }

    @objc private func captureTapped() {
        let imagePicker = UIImagePickerController()
        imagePicker.delegate = self
        imagePicker.sourceType = .camera
        imagePicker.allowsEditing = true
        present(imagePicker, animated: true)
    }

    @objc private func galleryTapped() {
        if #available(iOS 14, *) {
            var config = PHPickerConfiguration(photoLibrary: .shared())
            config.selectionLimit = 10
            config.filter = .images
            let picker = PHPickerViewController(configuration: config)
            picker.delegate = self
            present(picker, animated: true)
        } else {
            let imagePicker = UIImagePickerController()
            imagePicker.delegate = self
            imagePicker.sourceType = .photoLibrary
            imagePicker.allowsEditing = true
            present(imagePicker, animated: true)
        }
    }

    // MARK: - Process / Cancel

    @objc private func processTapped() {
        // If currently processing -> cancel
        if !loadingContainer.isHidden {
            processingCancelled = true
            processButton.setTitle("Cancelling...", for: .normal)
            processButton.isEnabled = false
            return
        }

        guard !selectedImages.isEmpty else {
            showAlert(title: "No Images", message: "Please select at least one image to process")
            return
        }

        processingCancelled = false
        processButton.setTitle("\u{2715} Cancel", for: .normal)
        processButton.backgroundColor = .systemOrange
        showLoading(true)

        Task {
            defer {
                Task { @MainActor in
                    self.showLoading(false)
                    self.processButton.setTitle("\u{1F50D} Start Analysis", for: .normal)
                    self.processButton.backgroundColor = self.brandRed
                    self.processButton.isEnabled = true
                }
            }

            do {
                guard let api = apiService else {
                    await MainActor.run {
                        showAlert(title: "Not Connected", message: "Unable to reach the server.")
                    }
                    return
                }

                for (index, image) in selectedImages.enumerated() {
                    if processingCancelled { break }

                    await MainActor.run {
                        loadingLabel.text = "Processing image \(index + 1) of \(selectedImages.count)..."
                    }

                    guard let jpegData = image.jpegData(compressionQuality: 0.8) else { continue }

                    let response = try await api.processOcrUpload(
                        imageData: jpegData,
                        useLlmEnhancement: true,
                        language: "auto",
                        outputLanguage: "en"
                    )

                    if processingCancelled { break }

                    await MainActor.run {
                        // Prefer qwen (enhanced) -> gemini -> menu_items
                        let items = response.qwen_menu_items ?? response.gemini_menu_items ?? response.menu_items
                        accumulatedMenuItems.append(contentsOf: items)
                    }
                }

                await MainActor.run {
                    // Keep images for display above results
                    processedImages = selectedImages
                    displayResults()
                    // Keep images visible - update button to "Re-analyze"
                    processButton.setTitle("\u{26A1} Re-analyze", for: .normal)
                    processButton.isHidden = false
                    imagesPreviewCard.isHidden = false
                }

            } catch {
                await MainActor.run {
                    showAlert(title: "Processing Error", message: error.localizedDescription)
                }
            }
        }
    }

    // MARK: - Translation

    @objc private func translateToggled() {
        isTranslateOn = translateSwitch.isOn
        if isTranslateOn && !accumulatedMenuItems.isEmpty {
            performTranslation()
        }
    }

    @objc private func languagePickerTapped() {
        let alert = UIAlertController(title: "Select Language", message: nil, preferredStyle: .actionSheet)
        for (code, name) in availableLanguages {
            alert.addAction(UIAlertAction(title: name, style: .default) { [weak self] _ in
                self?.selectedLanguage = code
                self?.languagePicker.setTitle("\(name) \u{25BE}", for: .normal)
                if self?.isTranslateOn == true {
                    self?.performTranslation()
                }
            })
        }
        alert.addAction(UIAlertAction(title: "Cancel", style: .cancel))
        if let pop = alert.popoverPresentationController {
            pop.sourceView = languagePicker
            pop.sourceRect = languagePicker.bounds
        }
        present(alert, animated: true)
    }

    private func performTranslation() {
        guard let api = apiService, !accumulatedMenuItems.isEmpty else { return }
        loadingLabel.text = "Translating..."
        showLoading(true)

        Task {
            do {
                let dictItems: [[String: AnyCodable]] = accumulatedMenuItems.map { item in
                    var dict: [String: AnyCodable] = [
                        "name": AnyCodable(item.name)
                    ]
                    if let p = item.price { dict["price"] = AnyCodable(p) }
                    if let d = item.description { dict["description"] = AnyCodable(d) }
                    if let c = item.category { dict["category"] = AnyCodable(c) }
                    if let t = item.taste { dict["taste"] = AnyCodable(t) }
                    if let r = item.recommendation { dict["recommendation"] = AnyCodable(r) }
                    return dict
                }

                let translated = try await api.translateMenuItems(items: dictItems, targetLanguage: selectedLanguage)

                await MainActor.run {
                    for (idx, itemDict) in translated.enumerated() where idx < accumulatedMenuItems.count {
                        let old = accumulatedMenuItems[idx]
                        let newName = (itemDict["name"]?.value as? String) ?? old.name
                        let newDesc = (itemDict["description"]?.value as? String) ?? old.description
                        accumulatedMenuItems[idx] = MenuItem(
                            name: newName, price: old.price, description: newDesc,
                            category: old.category, ingredients: old.ingredients,
                            taste: old.taste, similarDish1: old.similarDish1,
                            similarDish2: old.similarDish2, recommendation: old.recommendation,
                            recommendation_reason: old.recommendation_reason,
                            allergens: old.allergens, spiciness_level: old.spiciness_level,
                            preparation_method: old.preparation_method
                        )
                    }
                    showLoading(false)
                    resultsTableView.reloadData()
                }
            } catch {
                await MainActor.run {
                    showLoading(false)
                    showAlert(title: "Translation Error", message: error.localizedDescription)
                }
            }
        }
    }

    // MARK: - Reset / Export

    @objc private func resetTapped() {
        accumulatedMenuItems.removeAll()
        selectedImages.removeAll()
        processedImages.removeAll()
        resultsCard.isHidden = true
        resultsHeaderLabel.isHidden = true
        actionButtonsContainer.isHidden = true
        translationRow.isHidden = true
        imagesPreviewCard.isHidden = true
        processButton.isHidden = true
        processButton.setTitle("\u{1F50D} Start Analysis", for: .normal)
        processButton.backgroundColor = brandRed
        translateSwitch.isOn = false
        isTranslateOn = false
        updateImagesPreview()
    }

    @objc private func exportTapped() {
        var text = "Menu Items\n\n"
        for (i, item) in accumulatedMenuItems.enumerated() {
            text += "\(i + 1). \(item.name)"
            if let p = item.price { text += " \u{2014} \(p)" }
            text += "\n"
            if let d = item.description { text += "   \(d)\n" }
            if let ing = item.ingredients, !ing.isEmpty {
                let joined = ing.joined(separator: ", ")
                text += "   Ingredients: \(joined)\n"
            }
            if let t = item.taste { text += "   Taste: \(t)\n" }
            if let r = item.recommendation { text += "   Recommendation: \(r)\n" }
            text += "\n"
        }
        let vc = UIActivityViewController(activityItems: [text], applicationActivities: nil)
        present(vc, animated: true)
    }

    // MARK: - Image Handling

    private func addImage(_ image: UIImage) {
        selectedImages.append(image)
        updateImagesPreview()
        imagesPreviewCard.isHidden = false
        processButton.isHidden = false
        processButton.setTitle("\u{1F50D} Start Analysis", for: .normal)
        processButton.backgroundColor = brandRed
    }

    private func updateImagesPreview() {
        imagesStackView.arrangedSubviews.forEach { $0.removeFromSuperview() }
        let imagesToShow = selectedImages.isEmpty ? processedImages : selectedImages

        for (index, image) in imagesToShow.enumerated() {
            let wrapper = UIView()
            wrapper.translatesAutoresizingMaskIntoConstraints = false
            wrapper.widthAnchor.constraint(equalToConstant: 88).isActive = true
            wrapper.heightAnchor.constraint(equalToConstant: 88).isActive = true

            let imageView = UIImageView()
            imageView.image = image
            imageView.contentMode = .scaleAspectFill
            imageView.clipsToBounds = true
            imageView.layer.cornerRadius = 10
            imageView.translatesAutoresizingMaskIntoConstraints = false
            wrapper.addSubview(imageView)

            // Remove button overlay
            let removeBtn = UIButton(type: .system)
            removeBtn.setTitle("\u{2715}", for: .normal)
            removeBtn.setTitleColor(.white, for: .normal)
            removeBtn.titleLabel?.font = .boldSystemFont(ofSize: 13)
            removeBtn.backgroundColor = UIColor.black.withAlphaComponent(0.6)
            removeBtn.layer.cornerRadius = 12
            removeBtn.tag = index
            removeBtn.addTarget(self, action: #selector(removeImageTapped(_:)), for: .touchUpInside)
            removeBtn.translatesAutoresizingMaskIntoConstraints = false
            wrapper.addSubview(removeBtn)

            NSLayoutConstraint.activate([
                imageView.topAnchor.constraint(equalTo: wrapper.topAnchor),
                imageView.leadingAnchor.constraint(equalTo: wrapper.leadingAnchor),
                imageView.trailingAnchor.constraint(equalTo: wrapper.trailingAnchor),
                imageView.bottomAnchor.constraint(equalTo: wrapper.bottomAnchor),

                removeBtn.topAnchor.constraint(equalTo: wrapper.topAnchor, constant: 2),
                removeBtn.trailingAnchor.constraint(equalTo: wrapper.trailingAnchor, constant: -2),
                removeBtn.widthAnchor.constraint(equalToConstant: 24),
                removeBtn.heightAnchor.constraint(equalToConstant: 24)
            ])

            imagesStackView.addArrangedSubview(wrapper)
        }
    }

    @objc private func removeImageTapped(_ sender: UIButton) {
        let idx = sender.tag
        if !selectedImages.isEmpty {
            guard idx >= 0, idx < selectedImages.count else { return }
            selectedImages.remove(at: idx)
        } else if !processedImages.isEmpty {
            guard idx >= 0, idx < processedImages.count else { return }
            processedImages.remove(at: idx)
        }
        updateImagesPreview()
        if selectedImages.isEmpty && processedImages.isEmpty {
            imagesPreviewCard.isHidden = true
            processButton.isHidden = accumulatedMenuItems.isEmpty
        }
    }

    // MARK: - Results Display

    private func displayResults() {
        if accumulatedMenuItems.isEmpty {
            resultsHeaderLabel.text = "No menu items detected"
        } else {
            resultsHeaderLabel.text = "\u{1F4CB} \(accumulatedMenuItems.count) dishes found"
        }
        resultsHeaderLabel.isHidden = false
        resultsCard.isHidden = false
        translationRow.isHidden = false
        actionButtonsContainer.isHidden = false

        resultsTableView.reloadData()

        // Update table height (remove old, add new -- no constraint leak)
        if let old = tableHeightConstraint {
            old.isActive = false
        }
        resultsTableView.layoutIfNeeded()
        let height = max(resultsTableView.contentSize.height, CGFloat(accumulatedMenuItems.count * 100))
        tableHeightConstraint = resultsTableView.heightAnchor.constraint(equalToConstant: height)
        tableHeightConstraint?.isActive = true
    }

    // MARK: - Fallback Inference (for empty Groq fields)

    private func inferIngredients(name: String, desc: String) -> [String] {
        let t = (name + " " + desc).lowercased()
        if t.contains("pizza") { return ["dough", "tomato", "cheese"] }
        if t.contains("pasta") || t.contains("noodle") { return ["pasta", "olive oil", "herbs"] }
        if t.contains("burger") || t.contains("sandwich") { return ["bread", "protein", "vegetables"] }
        if t.contains("salad") { return ["greens", "olive oil", "seasoning"] }
        if t.contains("curry") { return ["spices", "onion", "oil"] }
        if t.contains("soup") { return ["broth", "herbs", "vegetables"] }
        return ["chef-special ingredients"]
    }

    private func inferTaste(name: String, desc: String) -> String {
        let t = (name + " " + desc).lowercased()
        if ["spicy","chili","hot","pepper"].contains(where: { t.contains($0) }) { return "spicy" }
        if ["sweet","dessert","honey","sugar"].contains(where: { t.contains($0) }) { return "sweet" }
        if ["lemon","citrus","vinegar","tangy"].contains(where: { t.contains($0) }) { return "tangy" }
        return "savory"
    }

    private func inferSimilarDishes(name: String, desc: String) -> (String, String) {
        let t = (name + " " + desc).lowercased()
        if t.contains("pizza") { return ("Lahmacun", "Manakish") }
        if t.contains("pasta") || t.contains("noodle") { return ("Yakisoba", "Dan Dan Noodles") }
        if t.contains("curry") { return ("Thai Green Curry", "Japanese Katsu Curry") }
        if t.contains("burger") { return ("Banh Mi", "Arepa") }
        if t.contains("soup") { return ("Tom Yum", "Miso Soup") }
        return ("Paella", "Bibimbap")
    }

    private func inferPreparation(name: String, desc: String) -> String {
        let t = (name + " " + desc).lowercased()
        if t.contains("fried") { return "fried" }
        if t.contains("grill") { return "grilled" }
        if t.contains("baked") { return "baked" }
        if t.contains("steam") { return "steamed" }
        return "chef method"
    }

    private func inferSpiciness(name: String, desc: String) -> String {
        let t = (name + " " + desc).lowercased()
        if ["spicy","chili","hot"].contains(where: { t.contains($0) }) { return "medium" }
        if ["pepper","masala"].contains(where: { t.contains($0) }) { return "mild" }
        return "none"
    }

    private func isEmptyLike(_ s: String?) -> Bool {
        guard let s = s?.trimmingCharacters(in: .whitespacesAndNewlines).lowercased() else { return true }
        return s.isEmpty || ["null","none","n/a","na","unknown","-","--","nil"].contains(s)
    }

    // Build complete detail item with fallback inference for empty fields
    private func buildDetailItem(_ item: MenuItem) -> MenuItem {
        let name = item.name
        let desc = item.description ?? ""

        let ingredients: [String]
        if let ing = item.ingredients, !ing.isEmpty {
            ingredients = ing
        } else {
            ingredients = inferIngredients(name: name, desc: desc)
        }

        let taste = isEmptyLike(item.taste) ? inferTaste(name: name, desc: desc) : item.taste!
        let similar = inferSimilarDishes(name: name, desc: desc)
        let s1 = isEmptyLike(item.similarDish1) ? similar.0 : item.similarDish1!
        let s2 = isEmptyLike(item.similarDish2) ? similar.1 : item.similarDish2!
        let rec = isEmptyLike(item.recommendation) ? "Recommended" : item.recommendation!
        let recReason = isEmptyLike(item.recommendation_reason) ? "Balanced choice based on dish profile." : item.recommendation_reason!
        let allergens: [String]
        if let a = item.allergens, !a.isEmpty { allergens = a } else { allergens = ["Not specified"] }
        let spice = isEmptyLike(item.spiciness_level) ? inferSpiciness(name: name, desc: desc) : item.spiciness_level!
        let prep = isEmptyLike(item.preparation_method) ? inferPreparation(name: name, desc: desc) : item.preparation_method!

        return MenuItem(
            name: name,
            price: item.price,
            description: desc.isEmpty ? "Description unavailable" : desc,
            category: item.category ?? "Other Dishes",
            ingredients: ingredients,
            taste: taste,
            similarDish1: s1,
            similarDish2: s2,
            recommendation: rec,
            recommendation_reason: recReason,
            allergens: allergens,
            spiciness_level: spice,
            preparation_method: prep
        )
    }

    // MARK: - Dish Detail View (bottom sheet with proper back button alignment)

    private func showDishDetail(_ item: MenuItem) {
        let detail = buildDetailItem(item)

        let overlay = UIView(frame: view.bounds)
        overlay.backgroundColor = UIColor.black.withAlphaComponent(0.45)
        overlay.tag = 8888
        overlay.autoresizingMask = [.flexibleWidth, .flexibleHeight]

        let card = UIView()
        card.backgroundColor = .systemBackground
        card.layer.cornerRadius = 20
        card.layer.maskedCorners = [.layerMinXMinYCorner, .layerMaxXMinYCorner]
        card.translatesAutoresizingMaskIntoConstraints = false
        overlay.addSubview(card)

        // Drag handle at top
        let handle = UIView()
        handle.backgroundColor = UIColor.systemGray3
        handle.layer.cornerRadius = 2.5
        handle.translatesAutoresizingMaskIntoConstraints = false
        card.addSubview(handle)

        // Top bar: back arrow left-aligned, title center
        let topBar = UIView()
        topBar.translatesAutoresizingMaskIntoConstraints = false
        card.addSubview(topBar)

        let backBtn = UIButton(type: .system)
        backBtn.setTitle("\u{2190} Back", for: .normal)
        backBtn.setTitleColor(scanPurple, for: .normal)
        backBtn.titleLabel?.font = .systemFont(ofSize: 16, weight: .semibold)
        backBtn.contentHorizontalAlignment = .left
        backBtn.addTarget(self, action: #selector(closeDishDetail), for: .touchUpInside)
        backBtn.translatesAutoresizingMaskIntoConstraints = false
        topBar.addSubview(backBtn)

        let detailTitle = UILabel()
        detailTitle.text = "Additional Details"
        detailTitle.font = .systemFont(ofSize: 17, weight: .bold)
        detailTitle.textColor = textPrimary
        detailTitle.textAlignment = .center
        detailTitle.translatesAutoresizingMaskIntoConstraints = false
        topBar.addSubview(detailTitle)

        let cardScroll = UIScrollView()
        cardScroll.translatesAutoresizingMaskIntoConstraints = false
        card.addSubview(cardScroll)

        let stack = UIStackView()
        stack.axis = .vertical
        stack.spacing = 16
        stack.translatesAutoresizingMaskIntoConstraints = false
        cardScroll.addSubview(stack)

        // Name
        let nameLbl = UILabel()
        nameLbl.text = detail.name
        nameLbl.font = .systemFont(ofSize: 22, weight: .bold)
        nameLbl.textColor = textPrimary
        nameLbl.numberOfLines = 0
        stack.addArrangedSubview(nameLbl)

        // Price
        if let price = detail.price, !price.isEmpty {
            let priceLbl = UILabel()
            priceLbl.text = price
            priceLbl.font = .systemFont(ofSize: 18, weight: .bold)
            priceLbl.textColor = brandRed
            stack.addArrangedSubview(priceLbl)
        }

        // Divider
        let divider = UIView()
        divider.backgroundColor = UIColor.systemGray5
        divider.translatesAutoresizingMaskIntoConstraints = false
        divider.heightAnchor.constraint(equalToConstant: 1).isActive = true
        stack.addArrangedSubview(divider)

        // Category
        if let cat = detail.category, !cat.isEmpty {
            addDetailSection(to: stack, emoji: "\u{1F4C2}", title: "Category", body: cat)
        }

        // Description
        if let desc = detail.description, !desc.isEmpty {
            addDetailSection(to: stack, emoji: "\u{1F4DD}", title: "Description", body: desc)
        }

        // Ingredients (bullets)
        if let ingredients = detail.ingredients, !ingredients.isEmpty {
            let bullets = ingredients.map { "  \u{2022} \($0)" }.joined(separator: "\n")
            addDetailSection(to: stack, emoji: "\u{1F9FE}", title: "Ingredients", body: bullets)
        }

        // Taste
        if let taste = detail.taste, !taste.isEmpty {
            addDetailSection(to: stack, emoji: "\u{1F60B}", title: "Taste", body: taste)
        }

        // Similar dishes (bullets)
        var similarParts: [String] = []
        if let s1 = detail.similarDish1, !s1.isEmpty { similarParts.append("  \u{2022} \(s1)") }
        if let s2 = detail.similarDish2, !s2.isEmpty { similarParts.append("  \u{2022} \(s2)") }
        if !similarParts.isEmpty {
            addDetailSection(to: stack, emoji: "\u{1F30D}", title: "Similar Dishes", body: similarParts.joined(separator: "\n"))
        }

        // Recommendation
        if let rec = detail.recommendation, !rec.isEmpty {
            var body = rec
            if let reason = detail.recommendation_reason, !reason.isEmpty {
                body += "\n  \(reason)"
            }
            addDetailSection(to: stack, emoji: "\u{1F48A}", title: "Recommendation", body: body)
        }

        // Allergens
        if let allergens = detail.allergens, !allergens.isEmpty {
            let joined = allergens.joined(separator: ", ")
            addDetailSection(to: stack, emoji: "\u{26A0}\u{FE0F}", title: "Allergens", body: joined)
        }

        // Spiciness
        if let spice = detail.spiciness_level, !spice.isEmpty {
            addDetailSection(to: stack, emoji: "\u{1F336}\u{FE0F}", title: "Spiciness", body: spice)
        }

        // Preparation
        if let prep = detail.preparation_method, !prep.isEmpty {
            addDetailSection(to: stack, emoji: "\u{1F468}\u{200D}\u{1F373}", title: "Preparation", body: prep)
        }

        // Layout
        NSLayoutConstraint.activate([
            card.leadingAnchor.constraint(equalTo: overlay.leadingAnchor),
            card.trailingAnchor.constraint(equalTo: overlay.trailingAnchor),
            card.bottomAnchor.constraint(equalTo: overlay.bottomAnchor),
            card.heightAnchor.constraint(lessThanOrEqualTo: overlay.heightAnchor, multiplier: 0.8),

            handle.topAnchor.constraint(equalTo: card.topAnchor, constant: 10),
            handle.centerXAnchor.constraint(equalTo: card.centerXAnchor),
            handle.widthAnchor.constraint(equalToConstant: 40),
            handle.heightAnchor.constraint(equalToConstant: 5),

            topBar.topAnchor.constraint(equalTo: handle.bottomAnchor, constant: 10),
            topBar.leadingAnchor.constraint(equalTo: card.leadingAnchor, constant: 16),
            topBar.trailingAnchor.constraint(equalTo: card.trailingAnchor, constant: -16),
            topBar.heightAnchor.constraint(equalToConstant: 40),

            backBtn.leadingAnchor.constraint(equalTo: topBar.leadingAnchor),
            backBtn.centerYAnchor.constraint(equalTo: topBar.centerYAnchor),
            backBtn.widthAnchor.constraint(equalToConstant: 70),

            detailTitle.centerXAnchor.constraint(equalTo: topBar.centerXAnchor),
            detailTitle.centerYAnchor.constraint(equalTo: topBar.centerYAnchor),

            cardScroll.topAnchor.constraint(equalTo: topBar.bottomAnchor, constant: 8),
            cardScroll.leadingAnchor.constraint(equalTo: card.leadingAnchor, constant: 20),
            cardScroll.trailingAnchor.constraint(equalTo: card.trailingAnchor, constant: -20),
            cardScroll.bottomAnchor.constraint(equalTo: card.safeAreaLayoutGuide.bottomAnchor, constant: -16),

            stack.topAnchor.constraint(equalTo: cardScroll.topAnchor),
            stack.leadingAnchor.constraint(equalTo: cardScroll.leadingAnchor),
            stack.trailingAnchor.constraint(equalTo: cardScroll.trailingAnchor),
            stack.bottomAnchor.constraint(equalTo: cardScroll.bottomAnchor),
            stack.widthAnchor.constraint(equalTo: cardScroll.widthAnchor)
        ])

        // Tap overlay bg to dismiss
        let tapGR = UITapGestureRecognizer(target: self, action: #selector(closeDishDetail))
        overlay.addGestureRecognizer(tapGR)
        tapGR.delegate = self

        // Animate in
        view.addSubview(overlay)
        card.transform = CGAffineTransform(translationX: 0, y: 400)
        UIView.animate(withDuration: 0.3, delay: 0, usingSpringWithDamping: 0.85, initialSpringVelocity: 0.5) {
            card.transform = .identity
        }
    }

    // UX Playbook: proper section styling - 15pt semibold header (off-black), 15pt body with 1.5x line spacing
    private func addDetailSection(to stack: UIStackView, emoji: String, title: String, body: String) {
        let container = UIView()
        container.translatesAutoresizingMaskIntoConstraints = false

        let titleLbl = UILabel()
        titleLbl.text = "\(emoji) \(title)"
        titleLbl.font = .systemFont(ofSize: 15, weight: .semibold)
        titleLbl.textColor = textSecondary
        titleLbl.translatesAutoresizingMaskIntoConstraints = false
        container.addSubview(titleLbl)

        let bodyLbl = UILabel()
        bodyLbl.numberOfLines = 0
        bodyLbl.translatesAutoresizingMaskIntoConstraints = false
        container.addSubview(bodyLbl)

        // UX playbook: 1.5x line spacing for readability
        let paragraphStyle = NSMutableParagraphStyle()
        paragraphStyle.lineSpacing = 6 // ~1.5x for 15pt font
        let attrs: [NSAttributedString.Key: Any] = [
            .font: UIFont.systemFont(ofSize: 15),
            .foregroundColor: textPrimary,
            .paragraphStyle: paragraphStyle
        ]
        bodyLbl.attributedText = NSAttributedString(string: body, attributes: attrs)

        NSLayoutConstraint.activate([
            titleLbl.topAnchor.constraint(equalTo: container.topAnchor),
            titleLbl.leadingAnchor.constraint(equalTo: container.leadingAnchor),
            titleLbl.trailingAnchor.constraint(equalTo: container.trailingAnchor),

            bodyLbl.topAnchor.constraint(equalTo: titleLbl.bottomAnchor, constant: 6),
            bodyLbl.leadingAnchor.constraint(equalTo: container.leadingAnchor, constant: 4),
            bodyLbl.trailingAnchor.constraint(equalTo: container.trailingAnchor),
            bodyLbl.bottomAnchor.constraint(equalTo: container.bottomAnchor)
        ])

        stack.addArrangedSubview(container)
    }

    @objc private func closeDishDetail() {
        if let overlay = view.viewWithTag(8888) {
            UIView.animate(withDuration: 0.25, animations: {
                overlay.alpha = 0
            }) { _ in
                overlay.removeFromSuperview()
            }
        }
    }

    // MARK: - Helpers

    private func showLoading(_ show: Bool) {
        loadingContainer.isHidden = !show
        processButton.isHidden = false
        if show {
            loadingIndicator.startAnimating()
        } else {
            loadingIndicator.stopAnimating()
        }
    }

    private func showAlert(title: String, message: String) {
        let alert = UIAlertController(title: title, message: message, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "OK", style: .default))
        present(alert, animated: true)
    }
}

// MARK: - UIGestureRecognizerDelegate (for overlay tap-to-dismiss)
extension MenuOCRViewController: UIGestureRecognizerDelegate {
    func gestureRecognizer(_ gestureRecognizer: UIGestureRecognizer, shouldReceive touch: UITouch) -> Bool {
        // Only dismiss when touching the overlay bg, not the card
        let location = touch.location(in: view)
        if let overlay = view.viewWithTag(8888) {
            for sub in overlay.subviews {
                if sub.frame.contains(location) { return false }
            }
        }
        return true
    }
}

// MARK: - UIImagePickerControllerDelegate

extension MenuOCRViewController: UIImagePickerControllerDelegate, UINavigationControllerDelegate {
    func imagePickerController(_ picker: UIImagePickerController, didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey : Any]) {
        if let image = info[.editedImage] as? UIImage ?? info[.originalImage] as? UIImage {
            addImage(image)
        }
        dismiss(animated: true)
    }

    func imagePickerControllerDidCancel(_ picker: UIImagePickerController) {
        dismiss(animated: true)
    }
}

// MARK: - PHPickerViewControllerDelegate

@available(iOS 14, *)
extension MenuOCRViewController: PHPickerViewControllerDelegate {
    func picker(_ picker: PHPickerViewController, didFinishPicking results: [PHPickerResult]) {
        dismiss(animated: true)
        for result in results {
            result.itemProvider.loadObject(ofClass: UIImage.self) { [weak self] object, _ in
                if let image = object as? UIImage {
                    DispatchQueue.main.async {
                        self?.addImage(image)
                    }
                }
            }
        }
    }
}

// MARK: - UITableViewDataSource & UITableViewDelegate

extension MenuOCRViewController: UITableViewDataSource, UITableViewDelegate {

    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        return accumulatedMenuItems.count
    }

    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cell = tableView.dequeueReusableCell(withIdentifier: "MenuItemCell", for: indexPath)
        let item = accumulatedMenuItems[indexPath.row]

        // Clear old subviews
        cell.contentView.subviews.forEach { $0.removeFromSuperview() }
        cell.selectionStyle = .none
        cell.backgroundColor = .clear
        cell.contentView.backgroundColor = .clear

        // Card container
        let cardView = UIView()
        cardView.backgroundColor = .systemBackground
        cardView.layer.cornerRadius = 12
        cardView.layer.borderWidth = 1
        cardView.layer.borderColor = UIColor.systemGray5.cgColor
        // UX playbook: subtle shadow for depth
        cardView.layer.shadowColor = UIColor.black.cgColor
        cardView.layer.shadowOffset = CGSize(width: 0, height: 1)
        cardView.layer.shadowOpacity = 0.06
        cardView.layer.shadowRadius = 4
        cardView.translatesAutoresizingMaskIntoConstraints = false
        cell.contentView.addSubview(cardView)

        // Name (UX: 16pt semibold, off-black)
        let nameLbl = UILabel()
        nameLbl.text = item.name
        nameLbl.font = .systemFont(ofSize: 16, weight: .semibold)
        nameLbl.textColor = textPrimary
        nameLbl.numberOfLines = 2
        nameLbl.translatesAutoresizingMaskIntoConstraints = false
        cardView.addSubview(nameLbl)

        // Price
        let priceLbl = UILabel()
        priceLbl.text = item.price ?? ""
        priceLbl.font = .systemFont(ofSize: 15, weight: .bold)
        priceLbl.textColor = brandRed
        priceLbl.textAlignment = .right
        priceLbl.setContentHuggingPriority(.required, for: .horizontal)
        priceLbl.translatesAutoresizingMaskIntoConstraints = false
        cardView.addSubview(priceLbl)

        // Description (truncated, UX: 14pt secondary color)
        let descLbl = UILabel()
        let descText = item.description ?? ""
        descLbl.text = descText.count > 80 ? String(descText.prefix(80)) + "..." : descText
        descLbl.font = .systemFont(ofSize: 14)
        descLbl.textColor = textSecondary
        descLbl.numberOfLines = 2
        descLbl.translatesAutoresizingMaskIntoConstraints = false
        cardView.addSubview(descLbl)

        // Bottom row: taste chip + hint
        let bottomRow = UIStackView()
        bottomRow.axis = .horizontal
        bottomRow.spacing = 8
        bottomRow.translatesAutoresizingMaskIntoConstraints = false
        cardView.addSubview(bottomRow)

        if let taste = item.taste, !taste.isEmpty, !isEmptyLike(taste) {
            let chip = UILabel()
            chip.text = " \u{1F60B} \(taste) "
            chip.font = .systemFont(ofSize: 12, weight: .medium)
            chip.textColor = .systemOrange
            chip.backgroundColor = UIColor.systemOrange.withAlphaComponent(0.1)
            chip.layer.cornerRadius = 8
            chip.clipsToBounds = true
            chip.translatesAutoresizingMaskIntoConstraints = false
            bottomRow.addArrangedSubview(chip)
        }

        let spacer = UIView()
        spacer.setContentHuggingPriority(.defaultLow, for: .horizontal)
        bottomRow.addArrangedSubview(spacer)

        let hintLbl = UILabel()
        hintLbl.text = "Tap for details \u{2192}"
        hintLbl.font = .systemFont(ofSize: 12)
        hintLbl.textColor = .tertiaryLabel
        bottomRow.addArrangedSubview(hintLbl)

        NSLayoutConstraint.activate([
            cardView.topAnchor.constraint(equalTo: cell.contentView.topAnchor, constant: 5),
            cardView.leadingAnchor.constraint(equalTo: cell.contentView.leadingAnchor, constant: 8),
            cardView.trailingAnchor.constraint(equalTo: cell.contentView.trailingAnchor, constant: -8),
            cardView.bottomAnchor.constraint(equalTo: cell.contentView.bottomAnchor, constant: -5),

            nameLbl.topAnchor.constraint(equalTo: cardView.topAnchor, constant: 14),
            nameLbl.leadingAnchor.constraint(equalTo: cardView.leadingAnchor, constant: 14),
            nameLbl.trailingAnchor.constraint(lessThanOrEqualTo: priceLbl.leadingAnchor, constant: -8),

            priceLbl.topAnchor.constraint(equalTo: cardView.topAnchor, constant: 14),
            priceLbl.trailingAnchor.constraint(equalTo: cardView.trailingAnchor, constant: -14),

            descLbl.topAnchor.constraint(equalTo: nameLbl.bottomAnchor, constant: 6),
            descLbl.leadingAnchor.constraint(equalTo: cardView.leadingAnchor, constant: 14),
            descLbl.trailingAnchor.constraint(equalTo: cardView.trailingAnchor, constant: -14),

            bottomRow.topAnchor.constraint(equalTo: descLbl.bottomAnchor, constant: 8),
            bottomRow.leadingAnchor.constraint(equalTo: cardView.leadingAnchor, constant: 14),
            bottomRow.trailingAnchor.constraint(equalTo: cardView.trailingAnchor, constant: -14),
            bottomRow.bottomAnchor.constraint(equalTo: cardView.bottomAnchor, constant: -12)
        ])

        return cell
    }

    func tableView(_ tableView: UITableView, heightForRowAt indexPath: IndexPath) -> CGFloat {
        return UITableView.automaticDimension
    }

    func tableView(_ tableView: UITableView, estimatedHeightForRowAt indexPath: IndexPath) -> CGFloat {
        return 100
    }

    func tableView(_ tableView: UITableView, didSelectRowAt indexPath: IndexPath) {
        let item = accumulatedMenuItems[indexPath.row]
        showDishDetail(item)
    }
}
"""

with open(TARGET, 'w') as f:
    f.write(content)

# Verify
with open(TARGET, 'r') as f:
    c = f.read()
lines = c.count('\n')
print(f"Written. Lines: {lines}")
print(f"processedImages: {'processedImages' in c}")
print(f"buildDetailItem: {'buildDetailItem' in c}")
print(f"inferIngredients: {'inferIngredients' in c}")
print(f"drag handle: {'handle' in c}")
print(f"Back button: {'Back' in c}")
print(f"paragraphStyle: {'paragraphStyle' in c}")
print(f"textPrimary: {'textPrimary' in c}")
print(f"UIGestureRecognizerDelegate: {'UIGestureRecognizerDelegate' in c}")
