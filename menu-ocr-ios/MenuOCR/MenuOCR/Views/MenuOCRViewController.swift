//
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
    private let brandViolet = UIColor(red: 0.486, green: 0.227, blue: 0.929, alpha: 1) // #7C3AED
    private let brandVioletLight = UIColor(red: 0.91, green: 0.87, blue: 1.0, alpha: 1) // #E8DEFF
    private let brandVioletBg = UIColor(red: 0.96, green: 0.94, blue: 1.0, alpha: 1) // #F5F0FF
    // Legacy alias kept for button highlight
    private let brandRed = UIColor(red: 0.486, green: 0.227, blue: 0.929, alpha: 1) // now violet
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

    // Scan limit badge
    private let scanBadgeLabel = UILabel()

    // Footer branding
    private let footerLabel = UILabel()

    // MARK: - Lifecycle

    init() { super.init(nibName: nil, bundle: nil) }
    required init?(coder: NSCoder) { super.init(coder: coder) }

    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
        setupConstraints()
        checkPermissions()
    }

    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        updateScanBadge()
    }

    // MARK: - UI Setup

    private func setupUI() {
        view.backgroundColor = UIColor(red: 0.96, green: 0.94, blue: 1.0, alpha: 1) // light violet bg

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
        setupScanBadge()
        setupFooter()
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
        captureButton.backgroundColor = brandViolet
        captureButton.setTitleColor(.white, for: .normal)
        captureButton.titleLabel?.font = .systemFont(ofSize: 16, weight: .semibold)
        captureButton.layer.cornerRadius = 12
        captureButton.addTarget(self, action: #selector(captureTapped), for: .touchUpInside)
        captureButton.translatesAutoresizingMaskIntoConstraints = false
        uploadCard.addSubview(captureButton)

        galleryButton.setTitle("\u{1F5BC}\u{FE0F} Gallery", for: .normal)
        galleryButton.backgroundColor = brandViolet.withAlphaComponent(0.75)
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
        translationRow.backgroundColor = .white
        translationRow.layer.cornerRadius = 12
        translationRow.layer.shadowColor = UIColor.black.cgColor
        translationRow.layer.shadowOffset = CGSize(width: 0, height: 1)
        translationRow.layer.shadowOpacity = 0.06
        translationRow.layer.shadowRadius = 4
        translationRow.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(translationRow)

        let globeIcon = UIImageView(image: UIImage(systemName: "globe"))
        globeIcon.tintColor = scanPurple
        globeIcon.translatesAutoresizingMaskIntoConstraints = false
        translationRow.addSubview(globeIcon)

        translateLabel.text = "Translate"
        translateLabel.font = .systemFont(ofSize: 15, weight: .semibold)
        translateLabel.textColor = textPrimary
        translateLabel.translatesAutoresizingMaskIntoConstraints = false
        translationRow.addSubview(translateLabel)

        translateSwitch.isOn = false
        translateSwitch.onTintColor = scanPurple
        translateSwitch.addTarget(self, action: #selector(translateToggled), for: .valueChanged)
        translateSwitch.translatesAutoresizingMaskIntoConstraints = false
        translationRow.addSubview(translateSwitch)

        languagePicker.setTitle("English \u{25BE}", for: .normal)
        languagePicker.setTitleColor(scanPurple, for: .normal)
        languagePicker.titleLabel?.font = .systemFont(ofSize: 14, weight: .semibold)
        languagePicker.backgroundColor = scanPurple.withAlphaComponent(0.08)
        languagePicker.layer.cornerRadius = 8
        languagePicker.contentEdgeInsets = UIEdgeInsets(top: 4, left: 10, bottom: 4, right: 10)
        languagePicker.addTarget(self, action: #selector(languagePickerTapped), for: .touchUpInside)
        languagePicker.translatesAutoresizingMaskIntoConstraints = false
        translationRow.addSubview(languagePicker)

        NSLayoutConstraint.activate([
            globeIcon.leadingAnchor.constraint(equalTo: translationRow.leadingAnchor, constant: 14),
            globeIcon.centerYAnchor.constraint(equalTo: translationRow.centerYAnchor),
            globeIcon.widthAnchor.constraint(equalToConstant: 20),
            globeIcon.heightAnchor.constraint(equalToConstant: 20),

            translateLabel.leadingAnchor.constraint(equalTo: globeIcon.trailingAnchor, constant: 8),
            translateLabel.centerYAnchor.constraint(equalTo: translationRow.centerYAnchor),

            translateSwitch.leadingAnchor.constraint(equalTo: translateLabel.trailingAnchor, constant: 8),
            translateSwitch.centerYAnchor.constraint(equalTo: translationRow.centerYAnchor),

            languagePicker.trailingAnchor.constraint(equalTo: translationRow.trailingAnchor, constant: -14),
            languagePicker.centerYAnchor.constraint(equalTo: translationRow.centerYAnchor)
        ])
    }

    private func setupResults() {
        resultsHeaderLabel.font = .systemFont(ofSize: 18, weight: .bold)
        resultsHeaderLabel.textColor = textPrimary
        resultsHeaderLabel.isHidden = true
        resultsHeaderLabel.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(resultsHeaderLabel)

        resultsCard.backgroundColor = UIColor(red: 0.96, green: 0.94, blue: 1.0, alpha: 1) // light violet bg
        resultsCard.layer.cornerRadius = 16
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

        resetButton.setTitle("\u{1F504} New Scan", for: .normal)
        resetButton.backgroundColor = UIColor.systemGray5
        resetButton.setTitleColor(textPrimary, for: .normal)
        resetButton.titleLabel?.font = .systemFont(ofSize: 15, weight: .semibold)
        resetButton.layer.cornerRadius = 12
        resetButton.addTarget(self, action: #selector(resetTapped), for: .touchUpInside)
        resetButton.translatesAutoresizingMaskIntoConstraints = false
        actionButtonsContainer.addSubview(resetButton)

        exportButton.setTitle("\u{1F4E4} Share", for: .normal)
        exportButton.backgroundColor = scanPurple
        exportButton.setTitleColor(.white, for: .normal)
        exportButton.titleLabel?.font = .systemFont(ofSize: 15, weight: .semibold)
        exportButton.layer.cornerRadius = 12
        exportButton.addTarget(self, action: #selector(exportTapped), for: .touchUpInside)
        exportButton.translatesAutoresizingMaskIntoConstraints = false
        actionButtonsContainer.addSubview(exportButton)
    }

    private func setupScanBadge() {
        scanBadgeLabel.font = .systemFont(ofSize: 13, weight: .semibold)
        scanBadgeLabel.textAlignment = .center
        scanBadgeLabel.layer.cornerRadius = 12
        scanBadgeLabel.clipsToBounds = true
        scanBadgeLabel.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(scanBadgeLabel)
        updateScanBadge()
    }

    private func updateScanBadge() {
        let limiter = ScanLimitManager.shared
        if limiter.isPremium {
            scanBadgeLabel.text = "  \u{2728} \(limiter.planName.capitalized) Plan  "
            scanBadgeLabel.textColor = brandViolet
            scanBadgeLabel.backgroundColor = brandVioletLight
        } else {
            let remaining = limiter.remainingFreeScans
            scanBadgeLabel.text = "  \(remaining) free scan\(remaining == 1 ? "" : "s") left  "
            scanBadgeLabel.textColor = remaining > 0 ? brandViolet : .systemRed
            scanBadgeLabel.backgroundColor = remaining > 0 ? brandVioletLight : UIColor.systemRed.withAlphaComponent(0.1)
        }
    }

    private func setupFooter() {
        footerLabel.text = "Fooder"
        footerLabel.font = .systemFont(ofSize: 14, weight: .semibold)
        footerLabel.textColor = brandViolet.withAlphaComponent(0.5)
        footerLabel.textAlignment = .center
        footerLabel.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(footerLabel)
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
            translationRow.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            translationRow.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            translationRow.heightAnchor.constraint(equalToConstant: 48),

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

            // Scan badge — between upload card and process button area
            scanBadgeLabel.topAnchor.constraint(equalTo: uploadCard.topAnchor, constant: -14),
            scanBadgeLabel.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -20),
            scanBadgeLabel.heightAnchor.constraint(equalToConstant: 26),

            // Footer
            footerLabel.topAnchor.constraint(equalTo: actionButtonsContainer.bottomAnchor, constant: 24),
            footerLabel.centerXAnchor.constraint(equalTo: contentView.centerXAnchor),
            footerLabel.bottomAnchor.constraint(equalTo: contentView.bottomAnchor, constant: -20),

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

        // ── Free limit gate ──
        let limiter = ScanLimitManager.shared
        if limiter.isLimitReached {
            showPaywall()
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
                    self.processButton.backgroundColor = self.brandViolet
                    self.processButton.isEnabled = true
                    self.updateScanBadge()
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

                    // Count this scan
                    limiter.recordScan()

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
                    showAlert(title: "Oops!", message: friendlyMessage(for: error))
                }
            }
        }
    }

    // MARK: - Paywall

    private func showPaywall() {
        let paywall = PaywallViewController()
        paywall.delegate = self
        paywall.modalPresentationStyle = .fullScreen
        present(paywall, animated: true)
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
                // Send ALL fields so the worker can translate everything
                let dictItems: [[String: AnyCodable]] = accumulatedMenuItems.map { item in
                    var dict: [String: AnyCodable] = [
                        "name": AnyCodable(item.name)
                    ]
                    if let p = item.price { dict["price"] = AnyCodable(p) }
                    if let d = item.description { dict["description"] = AnyCodable(d) }
                    if let c = item.category { dict["category"] = AnyCodable(c) }
                    if let ing = item.ingredients, !ing.isEmpty { dict["ingredients"] = AnyCodable(ing) }
                    if let t = item.taste { dict["taste"] = AnyCodable(t) }
                    if let s1 = item.similarDish1 { dict["similarDish1"] = AnyCodable(s1) }
                    if let s2 = item.similarDish2 { dict["similarDish2"] = AnyCodable(s2) }
                    if let r = item.recommendation { dict["recommendation"] = AnyCodable(r) }
                    if let rr = item.recommendation_reason { dict["recommendation_reason"] = AnyCodable(rr) }
                    if let a = item.allergens, !a.isEmpty { dict["allergens"] = AnyCodable(a) }
                    if let sl = item.spiciness_level { dict["spiciness_level"] = AnyCodable(sl) }
                    if let pm = item.preparation_method { dict["preparation_method"] = AnyCodable(pm) }
                    return dict
                }

                let translated = try await api.translateMenuItems(items: dictItems, targetLanguage: selectedLanguage)

                await MainActor.run {
                    for (idx, itemDict) in translated.enumerated() where idx < accumulatedMenuItems.count {
                        let old = accumulatedMenuItems[idx]
                        accumulatedMenuItems[idx] = MenuItem(
                            name: (itemDict["name"]?.value as? String) ?? old.name,
                            price: old.price,
                            description: (itemDict["description"]?.value as? String) ?? old.description,
                            category: (itemDict["category"]?.value as? String) ?? old.category,
                            ingredients: (itemDict["ingredients"]?.value as? [String]) ?? old.ingredients,
                            taste: (itemDict["taste"]?.value as? String) ?? old.taste,
                            similarDish1: (itemDict["similarDish1"]?.value as? String) ?? old.similarDish1,
                            similarDish2: (itemDict["similarDish2"]?.value as? String) ?? old.similarDish2,
                            recommendation: old.recommendation,
                            recommendation_reason: (itemDict["recommendation_reason"]?.value as? String) ?? old.recommendation_reason,
                            allergens: (itemDict["allergens"]?.value as? [String]) ?? old.allergens,
                            spiciness_level: old.spiciness_level,
                            preparation_method: (itemDict["preparation_method"]?.value as? String) ?? old.preparation_method
                        )
                    }
                    showLoading(false)
                    resultsTableView.reloadData()
                }
            } catch {
                await MainActor.run {
                    showLoading(false)
                    showAlert(title: "Oops!", message: friendlyMessage(for: error))
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

            // Remove button overlay — bold red ✕ for clear visibility
            let removeBtn = UIButton(type: .custom)
            let xConfig = UIImage.SymbolConfiguration(pointSize: 16, weight: .bold)
            let xImage = UIImage(systemName: "xmark.circle.fill", withConfiguration: xConfig)
            removeBtn.setImage(xImage, for: .normal)
            removeBtn.tintColor = .white
            removeBtn.backgroundColor = UIColor.systemRed
            removeBtn.layer.cornerRadius = 14
            removeBtn.layer.borderWidth = 2
            removeBtn.layer.borderColor = UIColor.white.cgColor
            removeBtn.layer.shadowColor = UIColor.black.cgColor
            removeBtn.layer.shadowOffset = CGSize(width: 0, height: 1)
            removeBtn.layer.shadowOpacity = 0.3
            removeBtn.layer.shadowRadius = 2
            removeBtn.tag = index
            removeBtn.addTarget(self, action: #selector(removeImageTapped(_:)), for: .touchUpInside)
            removeBtn.translatesAutoresizingMaskIntoConstraints = false
            wrapper.addSubview(removeBtn)

            NSLayoutConstraint.activate([
                imageView.topAnchor.constraint(equalTo: wrapper.topAnchor),
                imageView.leadingAnchor.constraint(equalTo: wrapper.leadingAnchor),
                imageView.trailingAnchor.constraint(equalTo: wrapper.trailingAnchor),
                imageView.bottomAnchor.constraint(equalTo: wrapper.bottomAnchor),

                removeBtn.topAnchor.constraint(equalTo: wrapper.topAnchor, constant: -4),
                removeBtn.trailingAnchor.constraint(equalTo: wrapper.trailingAnchor, constant: 4),
                removeBtn.widthAnchor.constraint(equalToConstant: 28),
                removeBtn.heightAnchor.constraint(equalToConstant: 28)
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
        overlay.backgroundColor = UIColor.black.withAlphaComponent(0.5)
        overlay.tag = 8888
        overlay.autoresizingMask = [.flexibleWidth, .flexibleHeight]

        let card = UIView()
        card.backgroundColor = UIColor(red: 0.97, green: 0.97, blue: 0.98, alpha: 1) // slight warm gray
        card.layer.cornerRadius = 24
        card.layer.maskedCorners = [.layerMinXMinYCorner, .layerMaxXMinYCorner]
        card.layer.shadowColor = UIColor.black.cgColor
        card.layer.shadowOffset = CGSize(width: 0, height: -4)
        card.layer.shadowOpacity = 0.15
        card.layer.shadowRadius = 16
        card.translatesAutoresizingMaskIntoConstraints = false
        overlay.addSubview(card)

        // Drag handle
        let handle = UIView()
        handle.backgroundColor = UIColor.systemGray3
        handle.layer.cornerRadius = 2.5
        handle.translatesAutoresizingMaskIntoConstraints = false
        card.addSubview(handle)

        // ─── Top Bar ────────────────────────────
        let topBar = UIView()
        topBar.translatesAutoresizingMaskIntoConstraints = false
        card.addSubview(topBar)

        // Close button — minimal circle X on right
        let closeBtn = UIButton(type: .custom)
        let xConfig = UIImage.SymbolConfiguration(pointSize: 13, weight: .semibold)
        let xImg = UIImage(systemName: "xmark", withConfiguration: xConfig)
        closeBtn.setImage(xImg, for: .normal)
        closeBtn.tintColor = .secondaryLabel
        closeBtn.backgroundColor = UIColor.systemGray5
        closeBtn.layer.cornerRadius = 16
        closeBtn.addTarget(self, action: #selector(closeDishDetail), for: .touchUpInside)
        closeBtn.translatesAutoresizingMaskIntoConstraints = false
        topBar.addSubview(closeBtn)

        let detailTitle = UILabel()
        detailTitle.text = "Dish Details"
        detailTitle.font = .systemFont(ofSize: 18, weight: .bold)
        detailTitle.textColor = textPrimary
        detailTitle.translatesAutoresizingMaskIntoConstraints = false
        topBar.addSubview(detailTitle)

        let cardScroll = UIScrollView()
        cardScroll.showsVerticalScrollIndicator = false
        cardScroll.translatesAutoresizingMaskIntoConstraints = false
        card.addSubview(cardScroll)

        let stack = UIStackView()
        stack.axis = .vertical
        stack.spacing = 12
        stack.translatesAutoresizingMaskIntoConstraints = false
        cardScroll.addSubview(stack)

        // ─── Hero: Name + Price ─────────────────
        let heroCard = UIView()
        heroCard.backgroundColor = .white
        heroCard.layer.cornerRadius = 16
        heroCard.layer.shadowColor = UIColor.black.cgColor
        heroCard.layer.shadowOffset = CGSize(width: 0, height: 1)
        heroCard.layer.shadowOpacity = 0.06
        heroCard.layer.shadowRadius = 6
        heroCard.translatesAutoresizingMaskIntoConstraints = false

        let nameLbl = UILabel()
        nameLbl.text = detail.name
        nameLbl.font = .systemFont(ofSize: 22, weight: .bold)
        nameLbl.textColor = textPrimary
        nameLbl.numberOfLines = 0
        nameLbl.translatesAutoresizingMaskIntoConstraints = false
        heroCard.addSubview(nameLbl)

        let priceLbl = UILabel()
        if let price = detail.price, !price.isEmpty {
            priceLbl.text = price
            priceLbl.font = .systemFont(ofSize: 20, weight: .heavy)
            priceLbl.textColor = scanPurple
        }
        priceLbl.translatesAutoresizingMaskIntoConstraints = false
        heroCard.addSubview(priceLbl)

        // Recommendation badge
        let recBadge = UILabel()
        if let rec = detail.recommendation, !rec.isEmpty {
            let bgColor: UIColor
            let icon: String
            switch rec.lowercased() {
            case let r where r.contains("most"):
                bgColor = UIColor.systemGreen; icon = "\u{2B50}"
            case let r where r.contains("not"):
                bgColor = UIColor.systemRed; icon = "\u{26A0}\u{FE0F}"
            default:
                bgColor = UIColor.systemBlue; icon = "\u{1F44D}"
            }
            recBadge.text = " \(icon) \(rec) "
            recBadge.font = .systemFont(ofSize: 12, weight: .bold)
            recBadge.textColor = .white
            recBadge.backgroundColor = bgColor
            recBadge.layer.cornerRadius = 10
            recBadge.clipsToBounds = true
        }
        recBadge.translatesAutoresizingMaskIntoConstraints = false
        heroCard.addSubview(recBadge)

        NSLayoutConstraint.activate([
            nameLbl.topAnchor.constraint(equalTo: heroCard.topAnchor, constant: 16),
            nameLbl.leadingAnchor.constraint(equalTo: heroCard.leadingAnchor, constant: 16),
            nameLbl.trailingAnchor.constraint(equalTo: heroCard.trailingAnchor, constant: -16),
            priceLbl.topAnchor.constraint(equalTo: nameLbl.bottomAnchor, constant: 6),
            priceLbl.leadingAnchor.constraint(equalTo: heroCard.leadingAnchor, constant: 16),
            recBadge.centerYAnchor.constraint(equalTo: priceLbl.centerYAnchor),
            recBadge.trailingAnchor.constraint(equalTo: heroCard.trailingAnchor, constant: -16),
            recBadge.heightAnchor.constraint(equalToConstant: 22),
            priceLbl.bottomAnchor.constraint(equalTo: heroCard.bottomAnchor, constant: -16),
        ])
        stack.addArrangedSubview(heroCard)

        // ─── Info Grid (Category, Taste, Spiciness) ────
        if detail.category != nil || detail.taste != nil || detail.spiciness_level != nil {
            let gridCard = UIView()
            gridCard.backgroundColor = .white
            gridCard.layer.cornerRadius = 16
            gridCard.layer.shadowColor = UIColor.black.cgColor
            gridCard.layer.shadowOffset = CGSize(width: 0, height: 1)
            gridCard.layer.shadowOpacity = 0.06
            gridCard.layer.shadowRadius = 6
            gridCard.translatesAutoresizingMaskIntoConstraints = false

            let gridStack = UIStackView()
            gridStack.axis = .horizontal
            gridStack.distribution = .fillEqually
            gridStack.spacing = 1
            gridStack.translatesAutoresizingMaskIntoConstraints = false
            gridCard.addSubview(gridStack)

            if let cat = detail.category, !cat.isEmpty {
                gridStack.addArrangedSubview(makeInfoPill(icon: "\u{1F4C2}", label: "Category", value: cat, color: .systemIndigo))
            }
            if let taste = detail.taste, !taste.isEmpty {
                gridStack.addArrangedSubview(makeInfoPill(icon: "\u{1F60B}", label: "Taste", value: taste, color: .systemOrange))
            }
            if let spice = detail.spiciness_level, !spice.isEmpty {
                let spiceIcon = spice.lowercased().contains("hot") ? "\u{1F525}" : "\u{1F336}\u{FE0F}"
                gridStack.addArrangedSubview(makeInfoPill(icon: spiceIcon, label: "Spice", value: spice, color: .systemRed))
            }

            NSLayoutConstraint.activate([
                gridStack.topAnchor.constraint(equalTo: gridCard.topAnchor, constant: 12),
                gridStack.leadingAnchor.constraint(equalTo: gridCard.leadingAnchor, constant: 12),
                gridStack.trailingAnchor.constraint(equalTo: gridCard.trailingAnchor, constant: -12),
                gridStack.bottomAnchor.constraint(equalTo: gridCard.bottomAnchor, constant: -12),
            ])
            stack.addArrangedSubview(gridCard)
        }

        // ─── Description ────────────────────────
        if let desc = detail.description, !desc.isEmpty {
            stack.addArrangedSubview(makeDetailCard(icon: "\u{1F4DD}", title: "Description", body: desc, accentColor: .systemBlue))
        }

        // ─── Ingredients ────────────────────────
        if let ingredients = detail.ingredients, !ingredients.isEmpty {
            let pills = ingredients.map { "  \u{2022} \($0)" }.joined(separator: "\n")
            stack.addArrangedSubview(makeDetailCard(icon: "\u{1F9FE}", title: "Ingredients", body: pills, accentColor: .systemGreen))
        }

        // ─── Similar Dishes ─────────────────────
        var similarParts: [String] = []
        if let s1 = detail.similarDish1, !s1.isEmpty { similarParts.append("  \u{2022} \(s1)") }
        if let s2 = detail.similarDish2, !s2.isEmpty { similarParts.append("  \u{2022} \(s2)") }
        if !similarParts.isEmpty {
            stack.addArrangedSubview(makeDetailCard(icon: "\u{1F30D}", title: "Similar Dishes", body: similarParts.joined(separator: "\n"), accentColor: .systemTeal))
        }

        // ─── Recommendation reason ──────────────
        if let reason = detail.recommendation_reason, !reason.isEmpty {
            stack.addArrangedSubview(makeDetailCard(icon: "\u{1F48A}", title: "Health Insight", body: reason, accentColor: .systemPurple))
        }

        // ─── Allergens ──────────────────────────
        if let allergens = detail.allergens, !allergens.isEmpty {
            let joined = allergens.joined(separator: ", ")
            stack.addArrangedSubview(makeDetailCard(icon: "\u{26A0}\u{FE0F}", title: "Allergens", body: joined, accentColor: .systemYellow))
        }

        // ─── Preparation ────────────────────────
        if let prep = detail.preparation_method, !prep.isEmpty {
            stack.addArrangedSubview(makeDetailCard(icon: "\u{1F468}\u{200D}\u{1F373}", title: "Preparation", body: prep, accentColor: .systemBrown))
        }

        // Layout
        NSLayoutConstraint.activate([
            card.leadingAnchor.constraint(equalTo: overlay.leadingAnchor),
            card.trailingAnchor.constraint(equalTo: overlay.trailingAnchor),
            card.bottomAnchor.constraint(equalTo: overlay.bottomAnchor),
            card.heightAnchor.constraint(lessThanOrEqualTo: overlay.heightAnchor, multiplier: 0.82),

            handle.topAnchor.constraint(equalTo: card.topAnchor, constant: 10),
            handle.centerXAnchor.constraint(equalTo: card.centerXAnchor),
            handle.widthAnchor.constraint(equalToConstant: 40),
            handle.heightAnchor.constraint(equalToConstant: 5),

            topBar.topAnchor.constraint(equalTo: handle.bottomAnchor, constant: 12),
            topBar.leadingAnchor.constraint(equalTo: card.leadingAnchor, constant: 20),
            topBar.trailingAnchor.constraint(equalTo: card.trailingAnchor, constant: -20),
            topBar.heightAnchor.constraint(equalToConstant: 36),

            detailTitle.leadingAnchor.constraint(equalTo: topBar.leadingAnchor),
            detailTitle.centerYAnchor.constraint(equalTo: topBar.centerYAnchor),

            closeBtn.trailingAnchor.constraint(equalTo: topBar.trailingAnchor),
            closeBtn.centerYAnchor.constraint(equalTo: topBar.centerYAnchor),
            closeBtn.widthAnchor.constraint(equalToConstant: 32),
            closeBtn.heightAnchor.constraint(equalToConstant: 32),

            cardScroll.topAnchor.constraint(equalTo: topBar.bottomAnchor, constant: 10),
            cardScroll.leadingAnchor.constraint(equalTo: card.leadingAnchor, constant: 16),
            cardScroll.trailingAnchor.constraint(equalTo: card.trailingAnchor, constant: -16),
            cardScroll.bottomAnchor.constraint(equalTo: card.safeAreaLayoutGuide.bottomAnchor, constant: -12),

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
        overlay.subviews.first { $0 != card }?.alpha = 0
        UIView.animate(withDuration: 0.35, delay: 0, usingSpringWithDamping: 0.85, initialSpringVelocity: 0.5) {
            card.transform = .identity
        }
    }

    // MARK: - Detail card builder (white card with colored left accent)

    private func makeDetailCard(icon: String, title: String, body: String, accentColor: UIColor) -> UIView {
        let wrapper = UIView()
        wrapper.backgroundColor = .white
        wrapper.layer.cornerRadius = 14
        wrapper.layer.shadowColor = UIColor.black.cgColor
        wrapper.layer.shadowOffset = CGSize(width: 0, height: 1)
        wrapper.layer.shadowOpacity = 0.05
        wrapper.layer.shadowRadius = 4
        wrapper.translatesAutoresizingMaskIntoConstraints = false

        // Color accent bar on left
        let accent = UIView()
        accent.backgroundColor = accentColor
        accent.layer.cornerRadius = 2
        accent.translatesAutoresizingMaskIntoConstraints = false
        wrapper.addSubview(accent)

        let titleLbl = UILabel()
        titleLbl.text = "\(icon)  \(title)"
        titleLbl.font = .systemFont(ofSize: 14, weight: .bold)
        titleLbl.textColor = accentColor
        titleLbl.translatesAutoresizingMaskIntoConstraints = false
        wrapper.addSubview(titleLbl)

        let bodyLbl = UILabel()
        bodyLbl.numberOfLines = 0
        bodyLbl.translatesAutoresizingMaskIntoConstraints = false
        wrapper.addSubview(bodyLbl)

        let paragraphStyle = NSMutableParagraphStyle()
        paragraphStyle.lineSpacing = 5
        let attrs: [NSAttributedString.Key: Any] = [
            .font: UIFont.systemFont(ofSize: 15),
            .foregroundColor: textPrimary,
            .paragraphStyle: paragraphStyle
        ]
        bodyLbl.attributedText = NSAttributedString(string: body, attributes: attrs)

        NSLayoutConstraint.activate([
            accent.leadingAnchor.constraint(equalTo: wrapper.leadingAnchor, constant: 0),
            accent.topAnchor.constraint(equalTo: wrapper.topAnchor, constant: 12),
            accent.bottomAnchor.constraint(equalTo: wrapper.bottomAnchor, constant: -12),
            accent.widthAnchor.constraint(equalToConstant: 4),

            titleLbl.topAnchor.constraint(equalTo: wrapper.topAnchor, constant: 14),
            titleLbl.leadingAnchor.constraint(equalTo: accent.trailingAnchor, constant: 14),
            titleLbl.trailingAnchor.constraint(equalTo: wrapper.trailingAnchor, constant: -14),

            bodyLbl.topAnchor.constraint(equalTo: titleLbl.bottomAnchor, constant: 6),
            bodyLbl.leadingAnchor.constraint(equalTo: accent.trailingAnchor, constant: 14),
            bodyLbl.trailingAnchor.constraint(equalTo: wrapper.trailingAnchor, constant: -14),
            bodyLbl.bottomAnchor.constraint(equalTo: wrapper.bottomAnchor, constant: -14)
        ])

        // Clip accent bar to card corners
        wrapper.clipsToBounds = true
        accent.layer.cornerRadius = 0

        return wrapper
    }

    // MARK: - Info pill (for grid: Category / Taste / Spiciness)

    private func makeInfoPill(icon: String, label: String, value: String, color: UIColor) -> UIView {
        let pill = UIView()
        pill.translatesAutoresizingMaskIntoConstraints = false

        let iconLbl = UILabel()
        iconLbl.text = icon
        iconLbl.font = .systemFont(ofSize: 22)
        iconLbl.textAlignment = .center
        iconLbl.translatesAutoresizingMaskIntoConstraints = false
        pill.addSubview(iconLbl)

        let labelLbl = UILabel()
        labelLbl.text = label.uppercased()
        labelLbl.font = .systemFont(ofSize: 10, weight: .bold)
        labelLbl.textColor = .tertiaryLabel
        labelLbl.textAlignment = .center
        labelLbl.translatesAutoresizingMaskIntoConstraints = false
        pill.addSubview(labelLbl)

        let valueLbl = UILabel()
        valueLbl.text = value
        valueLbl.font = .systemFont(ofSize: 13, weight: .semibold)
        valueLbl.textColor = color
        valueLbl.textAlignment = .center
        valueLbl.numberOfLines = 2
        valueLbl.translatesAutoresizingMaskIntoConstraints = false
        pill.addSubview(valueLbl)

        NSLayoutConstraint.activate([
            iconLbl.topAnchor.constraint(equalTo: pill.topAnchor, constant: 4),
            iconLbl.centerXAnchor.constraint(equalTo: pill.centerXAnchor),
            labelLbl.topAnchor.constraint(equalTo: iconLbl.bottomAnchor, constant: 2),
            labelLbl.centerXAnchor.constraint(equalTo: pill.centerXAnchor),
            valueLbl.topAnchor.constraint(equalTo: labelLbl.bottomAnchor, constant: 2),
            valueLbl.centerXAnchor.constraint(equalTo: pill.centerXAnchor),
            valueLbl.leadingAnchor.constraint(greaterThanOrEqualTo: pill.leadingAnchor, constant: 4),
            valueLbl.trailingAnchor.constraint(lessThanOrEqualTo: pill.trailingAnchor, constant: -4),
            valueLbl.bottomAnchor.constraint(equalTo: pill.bottomAnchor, constant: -4),
        ])
        pill.heightAnchor.constraint(greaterThanOrEqualToConstant: 70).isActive = true

        return pill
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

    /// Maps any error to a safe, user-friendly message (no technical details leak)
    private func friendlyMessage(for error: Error) -> String {
        // URLSession timeout
        if (error as NSError).code == NSURLErrorTimedOut {
            return "The request took too long. Please try again with a clearer photo."
        }
        // No internet
        if (error as NSError).code == NSURLErrorNotConnectedToInternet ||
           (error as NSError).code == NSURLErrorNetworkConnectionLost {
            return "No internet connection. Please check your network and try again."
        }
        // Cancelled by user
        if (error as NSError).code == NSURLErrorCancelled {
            return "Request was cancelled."
        }
        // Our own ApiError already returns user-friendly strings
        if error is ApiService.ApiError {
            return error.localizedDescription
        }
        // Catch-all
        return "Something went wrong. Please try again."
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
        cardView.backgroundColor = .white
        cardView.layer.cornerRadius = 14
        cardView.layer.shadowColor = UIColor.black.cgColor
        cardView.layer.shadowOffset = CGSize(width: 0, height: 2)
        cardView.layer.shadowOpacity = 0.07
        cardView.layer.shadowRadius = 8
        cardView.translatesAutoresizingMaskIntoConstraints = false
        cell.contentView.addSubview(cardView)

        // Recommendation color indicator (left accent bar)
        let accentBar = UIView()
        let recColor: UIColor
        switch (item.recommendation ?? "").lowercased() {
        case let r where r.contains("most"): recColor = .systemGreen
        case let r where r.contains("not"): recColor = .systemRed
        default: recColor = scanPurple
        }
        accentBar.backgroundColor = recColor
        accentBar.layer.cornerRadius = 2
        accentBar.translatesAutoresizingMaskIntoConstraints = false
        cardView.addSubview(accentBar)

        // Row number badge
        let numBadge = UILabel()
        numBadge.text = "\(indexPath.row + 1)"
        numBadge.font = .systemFont(ofSize: 11, weight: .bold)
        numBadge.textColor = .white
        numBadge.textAlignment = .center
        numBadge.backgroundColor = scanPurple.withAlphaComponent(0.85)
        numBadge.layer.cornerRadius = 11
        numBadge.clipsToBounds = true
        numBadge.translatesAutoresizingMaskIntoConstraints = false
        cardView.addSubview(numBadge)

        // Name (bold, off-black)
        let nameLbl = UILabel()
        nameLbl.text = item.name
        nameLbl.font = .systemFont(ofSize: 16, weight: .bold)
        nameLbl.textColor = textPrimary
        nameLbl.numberOfLines = 2
        nameLbl.translatesAutoresizingMaskIntoConstraints = false
        cardView.addSubview(nameLbl)

        // Price (right-aligned, brand purple)
        let priceLbl = UILabel()
        priceLbl.text = item.price ?? ""
        priceLbl.font = .systemFont(ofSize: 16, weight: .heavy)
        priceLbl.textColor = scanPurple
        priceLbl.textAlignment = .right
        priceLbl.setContentHuggingPriority(.required, for: .horizontal)
        priceLbl.translatesAutoresizingMaskIntoConstraints = false
        cardView.addSubview(priceLbl)

        // Description (truncated)
        let descLbl = UILabel()
        let descText = item.description ?? ""
        descLbl.text = descText.count > 85 ? String(descText.prefix(85)) + "..." : descText
        descLbl.font = .systemFont(ofSize: 13)
        descLbl.textColor = textSecondary
        descLbl.numberOfLines = 2
        descLbl.translatesAutoresizingMaskIntoConstraints = false
        cardView.addSubview(descLbl)

        // Bottom chips row
        let bottomRow = UIStackView()
        bottomRow.axis = .horizontal
        bottomRow.spacing = 6
        bottomRow.translatesAutoresizingMaskIntoConstraints = false
        cardView.addSubview(bottomRow)

        // Recommendation chip
        if let rec = item.recommendation, !rec.isEmpty, !isEmptyLike(rec) {
            let chip = makeMiniChip(text: rec, color: recColor)
            bottomRow.addArrangedSubview(chip)
        }

        // Taste chip
        if let taste = item.taste, !taste.isEmpty, !isEmptyLike(taste) {
            let chip = makeMiniChip(text: "\u{1F60B} \(taste)", color: .systemOrange)
            bottomRow.addArrangedSubview(chip)
        }

        // Spiciness chip
        if let spice = item.spiciness_level, !spice.isEmpty, !isEmptyLike(spice), spice.lowercased() != "none" {
            let chip = makeMiniChip(text: "\u{1F336}\u{FE0F} \(spice)", color: .systemRed)
            bottomRow.addArrangedSubview(chip)
        }

        let spacer = UIView()
        spacer.setContentHuggingPriority(.defaultLow, for: .horizontal)
        bottomRow.addArrangedSubview(spacer)

        // Arrow hint
        let arrow = UIImageView(image: UIImage(systemName: "chevron.right"))
        arrow.tintColor = .tertiaryLabel
        arrow.translatesAutoresizingMaskIntoConstraints = false
        arrow.widthAnchor.constraint(equalToConstant: 12).isActive = true
        arrow.heightAnchor.constraint(equalToConstant: 14).isActive = true
        arrow.contentMode = .scaleAspectFit
        bottomRow.addArrangedSubview(arrow)

        NSLayoutConstraint.activate([
            cardView.topAnchor.constraint(equalTo: cell.contentView.topAnchor, constant: 4),
            cardView.leadingAnchor.constraint(equalTo: cell.contentView.leadingAnchor, constant: 6),
            cardView.trailingAnchor.constraint(equalTo: cell.contentView.trailingAnchor, constant: -6),
            cardView.bottomAnchor.constraint(equalTo: cell.contentView.bottomAnchor, constant: -4),

            accentBar.leadingAnchor.constraint(equalTo: cardView.leadingAnchor),
            accentBar.topAnchor.constraint(equalTo: cardView.topAnchor, constant: 10),
            accentBar.bottomAnchor.constraint(equalTo: cardView.bottomAnchor, constant: -10),
            accentBar.widthAnchor.constraint(equalToConstant: 4),

            numBadge.leadingAnchor.constraint(equalTo: accentBar.trailingAnchor, constant: 10),
            numBadge.topAnchor.constraint(equalTo: cardView.topAnchor, constant: 14),
            numBadge.widthAnchor.constraint(equalToConstant: 22),
            numBadge.heightAnchor.constraint(equalToConstant: 22),

            nameLbl.topAnchor.constraint(equalTo: cardView.topAnchor, constant: 14),
            nameLbl.leadingAnchor.constraint(equalTo: numBadge.trailingAnchor, constant: 8),
            nameLbl.trailingAnchor.constraint(lessThanOrEqualTo: priceLbl.leadingAnchor, constant: -8),

            priceLbl.topAnchor.constraint(equalTo: cardView.topAnchor, constant: 14),
            priceLbl.trailingAnchor.constraint(equalTo: cardView.trailingAnchor, constant: -14),

            descLbl.topAnchor.constraint(equalTo: nameLbl.bottomAnchor, constant: 4),
            descLbl.leadingAnchor.constraint(equalTo: numBadge.trailingAnchor, constant: 8),
            descLbl.trailingAnchor.constraint(equalTo: cardView.trailingAnchor, constant: -14),

            bottomRow.topAnchor.constraint(equalTo: descLbl.bottomAnchor, constant: 8),
            bottomRow.leadingAnchor.constraint(equalTo: numBadge.trailingAnchor, constant: 8),
            bottomRow.trailingAnchor.constraint(equalTo: cardView.trailingAnchor, constant: -14),
            bottomRow.bottomAnchor.constraint(equalTo: cardView.bottomAnchor, constant: -12)
        ])

        return cell
    }

    private func makeMiniChip(text: String, color: UIColor) -> UILabel {
        let chip = UILabel()
        chip.text = " \(text) "
        chip.font = .systemFont(ofSize: 11, weight: .semibold)
        chip.textColor = color
        chip.backgroundColor = color.withAlphaComponent(0.1)
        chip.layer.cornerRadius = 8
        chip.clipsToBounds = true
        return chip
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

// MARK: - PaywallDelegate

extension MenuOCRViewController: PaywallDelegate {
    func paywallDidPurchase(plan: String) {
        updateScanBadge()
        // Proceed with the scan that was blocked
        processTapped()
    }

    func paywallDidDismiss() {
        // User closed paywall without purchasing — do nothing
    }
}
