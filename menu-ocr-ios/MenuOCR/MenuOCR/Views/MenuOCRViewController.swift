//
//  MenuOCRViewController.swift
//  MenuOCR
//
//  Menu OCR with camera/gallery support - equivalent to Android MenuOcrFragment.kt
//

import UIKit
import Vision
import PhotosUI

class MenuOCRViewController: UIViewController {
    
    // MARK: - Services
    
    var apiService: ApiService?
    private let ocrService: OcrService?
    
    // MARK: - State
    
    private var selectedImages: [UIImage] = []
    private var accumulatedMenuItems: [MenuItem] = []
    
    // MARK: - UI Components
    
    private let scrollView = UIScrollView()
    private let contentView = UIView()
    
    // Header
    private let headerView = UIView()
    private let headerIconLabel = UILabel()
    private let titleLabel = UILabel()
    private let subtitleLabel = UILabel()
    
    // Upload card
    private let uploadCard = UIView()
    private let captureButton = UIButton()
    private let galleryButton = UIButton()
    
    // Images preview
    private let imagesPreviewCard = UIView()
    private let imagesPreviewScrollView = UIScrollView()
    private let imagesStackView = UIStackView()
    private let addMoreButton = UIButton()
    
    // Process button
    private let processButton = UIButton()
    
    // Loading
    private let loadingContainer = UIView()
    private let loadingIndicator = UIActivityIndicatorView(style: .large)
    private let loadingLabel = UILabel()
    
    // Results
    private let resultsCard = UIView()
    private let resultsTitleLabel = UILabel()
    private let resultsTableView = UITableView()
    private let resultsTextView = UITextView()
    
    // Action buttons
    private let actionButtonsContainer = UIView()
    private let clearButton = UIButton()
    private let exportButton = UIButton()
    
    // MARK: - Initialization
    
    init() {
        self.ocrService = apiService.map { OcrService(apiService: $0) }
        super.init(nibName: nil, bundle: nil)
    }
    
    required init?(coder: NSCoder) {
        self.ocrService = nil
        super.init(coder: coder)
    }
    
    // MARK: - Lifecycle
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
        setupConstraints()
        checkPermissions()
    }
    
    // MARK: - UI Setup
    
    private func setupUI() {
        view.backgroundColor = .systemGray6
        
        // Setup navigation
        title = "Menu OCR"
        navigationController?.navigationBar.prefersLargeTitles = true
        
        // Scroll view
        scrollView.translatesAutoresizingMaskIntoConstraints = false
        contentView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(scrollView)
        scrollView.addSubview(contentView)
        
        // Header
        setupHeader()
        
        // Upload card
        setupUploadCard()
        
        // Images preview
        setupImagesPreview()
        
        // Process button
        setupProcessButton()
        
        // Loading
        setupLoading()
        
        // Results
        setupResults()
        
        // Action buttons
        setupActionButtons()
    }
    
    private func setupHeader() {
        headerView.backgroundColor = UIColor(red: 1.0, green: 0.3, blue: 0.22, alpha: 1.0)
        headerView.layer.cornerRadius = 16
        headerView.layer.maskedCorners = [.layerMinXMaxYCorner, .layerMaxXMaxYCorner]
        headerView.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(headerView)
        
        headerIconLabel.text = "📷"
        headerIconLabel.font = .systemFont(ofSize: 40)
        headerIconLabel.textAlignment = .center
        headerIconLabel.translatesAutoresizingMaskIntoConstraints = false
        headerView.addSubview(headerIconLabel)
        
        titleLabel.text = "Menu OCR"
        titleLabel.font = .boldSystemFont(ofSize: 24)
        titleLabel.textColor = .white
        titleLabel.textAlignment = .center
        titleLabel.translatesAutoresizingMaskIntoConstraints = false
        headerView.addSubview(titleLabel)
        
        subtitleLabel.text = "Scan menus with AI-powered OCR"
        subtitleLabel.font = .systemFont(ofSize: 14)
        subtitleLabel.textColor = .white.withAlphaComponent(0.9)
        subtitleLabel.textAlignment = .center
        subtitleLabel.translatesAutoresizingMaskIntoConstraints = false
        headerView.addSubview(subtitleLabel)
    }
    
    private func setupUploadCard() {
        uploadCard.backgroundColor = .systemBackground
        uploadCard.layer.cornerRadius = 12
        uploadCard.layer.shadowColor = UIColor.black.cgColor
        uploadCard.layer.shadowOffset = CGSize(width: 0, height: 2)
        uploadCard.layer.shadowOpacity = 0.1
        uploadCard.layer.shadowRadius = 4
        uploadCard.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(uploadCard)
        
        captureButton.setTitle("📷 Capture Image", for: .normal)
        captureButton.backgroundColor = UIColor(red: 1.0, green: 0.3, blue: 0.22, alpha: 1.0)
        captureButton.setTitleColor(.white, for: .normal)
        captureButton.titleLabel?.font = .boldSystemFont(ofSize: 16)
        captureButton.layer.cornerRadius = 12
        captureButton.addTarget(self, action: #selector(captureTapped), for: .touchUpInside)
        captureButton.translatesAutoresizingMaskIntoConstraints = false
        uploadCard.addSubview(captureButton)
        
        galleryButton.setTitle("🖼️ Select from Gallery", for: .normal)
        galleryButton.backgroundColor = .systemGreen
        galleryButton.setTitleColor(.white, for: .normal)
        galleryButton.titleLabel?.font = .boldSystemFont(ofSize: 16)
        galleryButton.layer.cornerRadius = 12
        galleryButton.addTarget(self, action: #selector(galleryTapped), for: .touchUpInside)
        galleryButton.translatesAutoresizingMaskIntoConstraints = false
        uploadCard.addSubview(galleryButton)
    }
    
    private func setupImagesPreview() {
        imagesPreviewCard.backgroundColor = .systemBackground
        imagesPreviewCard.layer.cornerRadius = 12
        imagesPreviewCard.layer.shadowColor = UIColor.black.cgColor
        imagesPreviewCard.layer.shadowOffset = CGSize(width: 0, height: 2)
        imagesPreviewCard.layer.shadowOpacity = 0.1
        imagesPreviewCard.layer.shadowRadius = 4
        imagesPreviewCard.isHidden = true
        imagesPreviewCard.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(imagesPreviewCard)
        
        let previewTitle = UILabel()
        previewTitle.text = "Selected Images"
        previewTitle.font = .boldSystemFont(ofSize: 16)
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
        addMoreButton.titleLabel?.font = .systemFont(ofSize: 14)
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
        processButton.setTitle("🔍 Get Menu", for: .normal)
        processButton.backgroundColor = UIColor(red: 1.0, green: 0.3, blue: 0.22, alpha: 1.0)
        processButton.setTitleColor(.white, for: .normal)
        processButton.titleLabel?.font = .boldSystemFont(ofSize: 18)
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
        
        loadingIndicator.color = UIColor(red: 1.0, green: 0.3, blue: 0.22, alpha: 1.0)
        loadingIndicator.translatesAutoresizingMaskIntoConstraints = false
        loadingContainer.addSubview(loadingIndicator)
        
        loadingLabel.text = "Processing menu..."
        loadingLabel.font = .systemFont(ofSize: 16)
        loadingLabel.textColor = .secondaryLabel
        loadingLabel.translatesAutoresizingMaskIntoConstraints = false
        loadingContainer.addSubview(loadingLabel)
    }
    
    private func setupResults() {
        resultsCard.backgroundColor = .systemBackground
        resultsCard.layer.cornerRadius = 12
        resultsCard.layer.shadowColor = UIColor.black.cgColor
        resultsCard.layer.shadowOffset = CGSize(width: 0, height: 2)
        resultsCard.layer.shadowOpacity = 0.1
        resultsCard.layer.shadowRadius = 4
        resultsCard.isHidden = true
        resultsCard.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(resultsCard)
        
        resultsTitleLabel.text = "📋 Menu Items"
        resultsTitleLabel.font = .boldSystemFont(ofSize: 18)
        resultsTitleLabel.translatesAutoresizingMaskIntoConstraints = false
        resultsCard.addSubview(resultsTitleLabel)
        
        resultsTableView.register(DishTableViewCell.self, forCellReuseIdentifier: "DishCell")
        resultsTableView.dataSource = self
        resultsTableView.delegate = self
        resultsTableView.separatorStyle = .none
        resultsTableView.isScrollEnabled = false
        resultsTableView.translatesAutoresizingMaskIntoConstraints = false
        resultsCard.addSubview(resultsTableView)
        
        resultsTextView.font = .monospacedSystemFont(ofSize: 12, weight: .regular)
        resultsTextView.isEditable = false
        resultsTextView.backgroundColor = .systemGray6
        resultsTextView.layer.cornerRadius = 8
        resultsTextView.isHidden = true
        resultsTextView.translatesAutoresizingMaskIntoConstraints = false
        resultsCard.addSubview(resultsTextView)
    }
    
    private func setupActionButtons() {
        actionButtonsContainer.isHidden = true
        actionButtonsContainer.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(actionButtonsContainer)
        
        clearButton.setTitle("🗑️ Clear", for: .normal)
        clearButton.backgroundColor = .systemRed
        clearButton.setTitleColor(.white, for: .normal)
        clearButton.titleLabel?.font = .boldSystemFont(ofSize: 16)
        clearButton.layer.cornerRadius = 12
        clearButton.addTarget(self, action: #selector(clearTapped), for: .touchUpInside)
        clearButton.translatesAutoresizingMaskIntoConstraints = false
        actionButtonsContainer.addSubview(clearButton)
        
        exportButton.setTitle("📤 Export", for: .normal)
        exportButton.backgroundColor = .systemBlue
        exportButton.setTitleColor(.white, for: .normal)
        exportButton.titleLabel?.font = .boldSystemFont(ofSize: 16)
        exportButton.layer.cornerRadius = 12
        exportButton.addTarget(self, action: #selector(exportTapped), for: .touchUpInside)
        exportButton.translatesAutoresizingMaskIntoConstraints = false
        actionButtonsContainer.addSubview(exportButton)
    }
    
    // MARK: - Constraints
    
    private func setupConstraints() {
        NSLayoutConstraint.activate([
            // Scroll view
            scrollView.topAnchor.constraint(equalTo: view.topAnchor),
            scrollView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            scrollView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            scrollView.bottomAnchor.constraint(equalTo: view.bottomAnchor),
            
            contentView.topAnchor.constraint(equalTo: scrollView.topAnchor),
            contentView.leadingAnchor.constraint(equalTo: scrollView.leadingAnchor),
            contentView.trailingAnchor.constraint(equalTo: scrollView.trailingAnchor),
            contentView.bottomAnchor.constraint(equalTo: scrollView.bottomAnchor),
            contentView.widthAnchor.constraint(equalTo: scrollView.widthAnchor),
            
            // Header
            headerView.topAnchor.constraint(equalTo: contentView.topAnchor),
            headerView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor),
            headerView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor),
            headerView.heightAnchor.constraint(equalToConstant: 140),
            
            headerIconLabel.topAnchor.constraint(equalTo: headerView.topAnchor, constant: 16),
            headerIconLabel.centerXAnchor.constraint(equalTo: headerView.centerXAnchor),
            
            titleLabel.topAnchor.constraint(equalTo: headerIconLabel.bottomAnchor, constant: 8),
            titleLabel.leadingAnchor.constraint(equalTo: headerView.leadingAnchor, constant: 16),
            titleLabel.trailingAnchor.constraint(equalTo: headerView.trailingAnchor, constant: -16),
            
            subtitleLabel.topAnchor.constraint(equalTo: titleLabel.bottomAnchor, constant: 4),
            subtitleLabel.leadingAnchor.constraint(equalTo: headerView.leadingAnchor, constant: 16),
            subtitleLabel.trailingAnchor.constraint(equalTo: headerView.trailingAnchor, constant: -16),
            
            // Upload card
            uploadCard.topAnchor.constraint(equalTo: headerView.bottomAnchor, constant: 20),
            uploadCard.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            uploadCard.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            uploadCard.heightAnchor.constraint(equalToConstant: 120),
            
            captureButton.leadingAnchor.constraint(equalTo: uploadCard.leadingAnchor, constant: 16),
            captureButton.trailingAnchor.constraint(equalTo: uploadCard.centerXAnchor, constant: -8),
            captureButton.centerYAnchor.constraint(equalTo: uploadCard.centerYAnchor),
            captureButton.heightAnchor.constraint(equalToConstant: 50),
            
            galleryButton.leadingAnchor.constraint(equalTo: uploadCard.centerXAnchor, constant: 8),
            galleryButton.trailingAnchor.constraint(equalTo: uploadCard.trailingAnchor, constant: -16),
            galleryButton.centerYAnchor.constraint(equalTo: uploadCard.centerYAnchor),
            galleryButton.heightAnchor.constraint(equalToConstant: 50),
            
            // Images preview
            imagesPreviewCard.topAnchor.constraint(equalTo: uploadCard.bottomAnchor, constant: 16),
            imagesPreviewCard.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            imagesPreviewCard.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            imagesPreviewCard.heightAnchor.constraint(equalToConstant: 170),
            
            // Process button
            processButton.topAnchor.constraint(equalTo: imagesPreviewCard.bottomAnchor, constant: 16),
            processButton.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            processButton.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            processButton.heightAnchor.constraint(equalToConstant: 50),
            
            // Loading
            loadingContainer.topAnchor.constraint(equalTo: processButton.topAnchor),
            loadingContainer.leadingAnchor.constraint(equalTo: processButton.leadingAnchor),
            loadingContainer.trailingAnchor.constraint(equalTo: processButton.trailingAnchor),
            loadingContainer.heightAnchor.constraint(equalToConstant: 50),
            
            loadingIndicator.leadingAnchor.constraint(equalTo: loadingContainer.leadingAnchor, constant: 16),
            loadingIndicator.centerYAnchor.constraint(equalTo: loadingContainer.centerYAnchor),
            
            loadingLabel.leadingAnchor.constraint(equalTo: loadingIndicator.trailingAnchor, constant: 16),
            loadingLabel.centerYAnchor.constraint(equalTo: loadingContainer.centerYAnchor),
            
            // Results
            resultsCard.topAnchor.constraint(equalTo: processButton.bottomAnchor, constant: 16),
            resultsCard.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            resultsCard.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            
            resultsTitleLabel.topAnchor.constraint(equalTo: resultsCard.topAnchor, constant: 16),
            resultsTitleLabel.leadingAnchor.constraint(equalTo: resultsCard.leadingAnchor, constant: 16),
            
            resultsTableView.topAnchor.constraint(equalTo: resultsTitleLabel.bottomAnchor, constant: 12),
            resultsTableView.leadingAnchor.constraint(equalTo: resultsCard.leadingAnchor, constant: 16),
            resultsTableView.trailingAnchor.constraint(equalTo: resultsCard.trailingAnchor, constant: -16),
            resultsTableView.bottomAnchor.constraint(equalTo: resultsCard.bottomAnchor, constant: -16),
            
            resultsTextView.topAnchor.constraint(equalTo: resultsTitleLabel.bottomAnchor, constant: 12),
            resultsTextView.leadingAnchor.constraint(equalTo: resultsCard.leadingAnchor, constant: 16),
            resultsTextView.trailingAnchor.constraint(equalTo: resultsCard.trailingAnchor, constant: -16),
            resultsTextView.heightAnchor.constraint(equalToConstant: 200),
            resultsTextView.bottomAnchor.constraint(equalTo: resultsCard.bottomAnchor, constant: -16),
            
            // Action buttons
            actionButtonsContainer.topAnchor.constraint(equalTo: resultsCard.bottomAnchor, constant: 16),
            actionButtonsContainer.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            actionButtonsContainer.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            actionButtonsContainer.heightAnchor.constraint(equalToConstant: 50),
            actionButtonsContainer.bottomAnchor.constraint(equalTo: contentView.bottomAnchor, constant: -32),
            
            clearButton.leadingAnchor.constraint(equalTo: actionButtonsContainer.leadingAnchor),
            clearButton.trailingAnchor.constraint(equalTo: actionButtonsContainer.centerXAnchor, constant: -8),
            clearButton.topAnchor.constraint(equalTo: actionButtonsContainer.topAnchor),
            clearButton.bottomAnchor.constraint(equalTo: actionButtonsContainer.bottomAnchor),
            
            exportButton.leadingAnchor.constraint(equalTo: actionButtonsContainer.centerXAnchor, constant: 8),
            exportButton.trailingAnchor.constraint(equalTo: actionButtonsContainer.trailingAnchor),
            exportButton.topAnchor.constraint(equalTo: actionButtonsContainer.topAnchor),
            exportButton.bottomAnchor.constraint(equalTo: actionButtonsContainer.bottomAnchor)
        ])
    }
    
    // MARK: - Permissions
    
    private func checkPermissions() {
        // Camera permission
        AVCaptureDevice.requestAccess(for: .video) { granted in
            if !granted {
                DispatchQueue.main.async {
                    self.showAlert(title: "Camera Access", message: "Please enable camera access in Settings to capture menu images.")
                }
            }
        }
        
        // Photo library permission
        PHPhotoLibrary.requestAuthorization { status in
            if status == .denied {
                DispatchQueue.main.async {
                    self.showAlert(title: "Photo Library Access", message: "Please enable photo library access in Settings to select menu images.")
                }
            }
        }
    }
    
    // MARK: - Actions
    
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
    
    @objc private func processTapped() {
        guard !selectedImages.isEmpty else {
            showAlert(title: "No Images", message: "Please select at least one image to process")
            return
        }
        
        showLoading(true)
        
        Task {
            do {
                for (index, image) in selectedImages.enumerated() {
                    await MainActor.run {
                        loadingLabel.text = "Processing image \(index + 1) of \(selectedImages.count)..."
                    }
                    
                    // Convert image to base64
                    guard let imageData = image.jpegData(compressionQuality: 0.8) else { continue }
                    let base64String = imageData.base64EncodedString()
                    
                    // Create OCR request
                    let request = OcrRequest(image_base64: base64String)
                    
                    // Process with API
                    if let apiService = apiService {
                        let response = try await apiService.processOcr(request: request)
                        
                        await MainActor.run {
                            accumulatedMenuItems.append(contentsOf: response.menu_items)
                        }
                    }
                }
                
                await MainActor.run {
                    showLoading(false)
                    displayResults()
                    clearSelectedImages()
                }
                
            } catch {
                await MainActor.run {
                    showLoading(false)
                    showAlert(title: "Processing Error", message: error.localizedDescription)
                }
            }
        }
    }
    
    @objc private func clearTapped() {
        accumulatedMenuItems.removeAll()
        resultsCard.isHidden = true
        actionButtonsContainer.isHidden = true
    }
    
    @objc private func exportTapped() {
        // Export as text
        var exportText = "Menu Items\n\n"
        for (index, item) in accumulatedMenuItems.enumerated() {
            exportText += "\(index + 1). \(item.name)"
            if let price = item.price {
                exportText += " - $\(price)"
            }
            exportText += "\n"
            if let description = item.description {
                exportText += "   \(description)\n"
            }
            if let category = item.category {
                exportText += "   Category: \(category)\n"
            }
            exportText += "\n"
        }
        
        let activityVC = UIActivityViewController(activityItems: [exportText], applicationActivities: nil)
        present(activityVC, animated: true)
    }
    
    // MARK: - Image Handling
    
    private func addImage(_ image: UIImage) {
        selectedImages.append(image)
        updateImagesPreview()
        
        imagesPreviewCard.isHidden = false
        processButton.isHidden = false
    }
    
    private func updateImagesPreview() {
        imagesStackView.arrangedSubviews.forEach { $0.removeFromSuperview() }
        
        for image in selectedImages {
            let imageView = UIImageView()
            imageView.image = image
            imageView.contentMode = .scaleAspectFill
            imageView.clipsToBounds = true
            imageView.layer.cornerRadius = 8
            imageView.translatesAutoresizingMaskIntoConstraints = false
            
            imageView.widthAnchor.constraint(equalToConstant: 80).isActive = true
            imageView.heightAnchor.constraint(equalToConstant: 80).isActive = true
            
            imagesStackView.addArrangedSubview(imageView)
        }
    }
    
    private func clearSelectedImages() {
        selectedImages.removeAll()
        imagesPreviewCard.isHidden = true
        processButton.isHidden = true
    }
    
    // MARK: - Results Display
    
    private func displayResults() {
        if accumulatedMenuItems.isEmpty {
            resultsTextView.text = "No menu items detected"
            resultsTextView.isHidden = false
            resultsTableView.isHidden = true
        } else {
            resultsTableView.isHidden = false
            resultsTextView.isHidden = true
            resultsTableView.reloadData()
            
            // Update table height
            resultsTableView.layoutIfNeeded()
            let height = resultsTableView.contentSize.height
            resultsTableView.heightAnchor.constraint(equalToConstant: min(height, 400)).isActive = true
        }
        
        resultsCard.isHidden = false
        actionButtonsContainer.isHidden = false
    }
    
    // MARK: - Helpers
    
    private func showLoading(_ show: Bool) {
        loadingContainer.isHidden = !show
        processButton.isHidden = show
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
            result.itemProvider.loadObject(ofClass: UIImage.self) { [weak self] object, error in
                if let image = object as? UIImage {
                    DispatchQueue.main.async {
                        self?.addImage(image)
                    }
                }
            }
        }
    }
}

// MARK: - UITableViewDataSource, UITableViewDelegate

extension MenuOCRViewController: UITableViewDataSource, UITableViewDelegate {
    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        return accumulatedMenuItems.count
    }
    
    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cell = tableView.dequeueReusableCell(withIdentifier: "DishCell", for: indexPath) as! DishTableViewCell
        let item = accumulatedMenuItems[indexPath.row]
        
        // Create a Dish from MenuItem for the cell
        let dish = Dish(
            id: item.id ?? UUID().uuidString,
            name: item.name,
            price: item.price,
            description: item.description,
            ingredients: nil,
            dietaryInfo: nil
        )
        cell.configure(with: dish)
        
        return cell
    }
    
    func tableView(_ tableView: UITableView, heightForRowAt indexPath: IndexPath) -> CGFloat {
        return 80
    }
}
