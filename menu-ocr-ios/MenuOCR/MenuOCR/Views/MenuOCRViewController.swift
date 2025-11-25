//
//  MenuOCRViewController.swift
//  MenuOCR
//
//  Created by MenuOCR on 2025-01-07.
//

import UIKit
import PhotosUI

class MenuOCRViewController: UIViewController, UIImagePickerControllerDelegate, UINavigationControllerDelegate, PHPickerViewControllerDelegate {

    private let scrollView = UIScrollView()
    private let contentView = UIView()

    // Status
    private let statusLabel = UILabel()

    // Buttons
    private let cameraButton = UIButton()
    private let galleryButton = UIButton()

    // Image preview
    private let imagePreviewCard = UIView()
    private let imagePreview = UIImageView()
    private let imageStatusLabel = UILabel()

    // Process button
    private let processButton = UIButton()

    // Loading indicator
    private let loadingView = UIView()
    private let activityIndicator = UIActivityIndicatorView()

    // Results
    private let resultsCard = UIView()
    private let resultsTextView = UITextView()

    private var selectedImage: UIImage?

    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
        setupConstraints()
        checkPermissions()
    }

    private func setupUI() {
        view.backgroundColor = UIColor.systemGray6

        // Status label
        statusLabel.text = "Ready to process images"
        statusLabel.textAlignment = .center
        statusLabel.font = UIFont.systemFont(ofSize: 14)
        statusLabel.textColor = .gray

        // Buttons
        cameraButton.setTitle("📷 Take Photo", for: .normal)
        cameraButton.backgroundColor = UIColor(red: 1.0, green: 0.3, blue: 0.22, alpha: 1.0)
        cameraButton.setTitleColor(.white, for: .normal)
        cameraButton.layer.cornerRadius = 8
        cameraButton.addTarget(self, action: #selector(cameraButtonTapped), for: .touchUpInside)

        galleryButton.setTitle("🖼️ Select from Gallery", for: .normal)
        galleryButton.backgroundColor = UIColor.systemBlue
        galleryButton.setTitleColor(.white, for: .normal)
        galleryButton.layer.cornerRadius = 8
        galleryButton.addTarget(self, action: #selector(galleryButtonTapped), for: .touchUpInside)

        // Image preview
        imagePreviewCard.backgroundColor = .white
        imagePreviewCard.layer.cornerRadius = 12
        imagePreviewCard.layer.shadowColor = UIColor.black.cgColor
        imagePreviewCard.layer.shadowOffset = CGSize(width: 0, height: 2)
        imagePreviewCard.layer.shadowOpacity = 0.1
        imagePreviewCard.layer.shadowRadius = 4
        imagePreviewCard.isHidden = true

        imagePreview.contentMode = .scaleAspectFit
        imagePreview.layer.cornerRadius = 8
        imagePreview.clipsToBounds = true

        imageStatusLabel.text = "Image selected"
        imageStatusLabel.font = UIFont.systemFont(ofSize: 14)
        imageStatusLabel.textColor = .gray
        imageStatusLabel.textAlignment = .center

        // Process button
        processButton.setTitle("⚡ Process OCR", for: .normal)
        processButton.backgroundColor = UIColor.systemGreen
        processButton.setTitleColor(.white, for: .normal)
        processButton.layer.cornerRadius = 8
        processButton.addTarget(self, action: #selector(processButtonTapped), for: .touchUpInside)
        processButton.isHidden = true

        // Loading view
        loadingView.backgroundColor = UIColor.black.withAlphaComponent(0.5)
        loadingView.layer.cornerRadius = 12
        loadingView.isHidden = true

        activityIndicator.style = .large
        activityIndicator.color = .white

        // Results
        resultsCard.backgroundColor = .white
        resultsCard.layer.cornerRadius = 12
        resultsCard.layer.shadowColor = UIColor.black.cgColor
        resultsCard.layer.shadowOffset = CGSize(width: 0, height: 2)
        resultsCard.layer.shadowOpacity = 0.1
        resultsCard.layer.shadowRadius = 4
        resultsCard.isHidden = true

        resultsTextView.font = UIFont.systemFont(ofSize: 14)
        resultsTextView.isEditable = false
        resultsTextView.textContainerInset = UIEdgeInsets(top: 16, left: 16, bottom: 16, right: 16)

        // Layout
        scrollView.translatesAutoresizingMaskIntoConstraints = false
        contentView.translatesAutoresizingMaskIntoConstraints = false

        view.addSubview(scrollView)
        scrollView.addSubview(contentView)

        contentView.addSubview(statusLabel)
        contentView.addSubview(cameraButton)
        contentView.addSubview(galleryButton)
        contentView.addSubview(imagePreviewCard)
        contentView.addSubview(processButton)
        contentView.addSubview(resultsCard)

        imagePreviewCard.addSubview(imagePreview)
        imagePreviewCard.addSubview(imageStatusLabel)

        loadingView.addSubview(activityIndicator)
        view.addSubview(loadingView)

        resultsCard.addSubview(resultsTextView)
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
        cameraButton.translatesAutoresizingMaskIntoConstraints = false
        galleryButton.translatesAutoresizingMaskIntoConstraints = false

        NSLayoutConstraint.activate([
            cameraButton.topAnchor.constraint(equalTo: statusLabel.bottomAnchor, constant: 20),
            cameraButton.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            cameraButton.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            cameraButton.heightAnchor.constraint(equalToConstant: 50),

            galleryButton.topAnchor.constraint(equalTo: cameraButton.bottomAnchor, constant: 12),
            galleryButton.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            galleryButton.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            galleryButton.heightAnchor.constraint(equalToConstant: 50)
        ])

        // Image preview
        imagePreviewCard.translatesAutoresizingMaskIntoConstraints = false
        imagePreview.translatesAutoresizingMaskIntoConstraints = false
        imageStatusLabel.translatesAutoresizingMaskIntoConstraints = false

        NSLayoutConstraint.activate([
            imagePreviewCard.topAnchor.constraint(equalTo: galleryButton.bottomAnchor, constant: 20),
            imagePreviewCard.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            imagePreviewCard.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            imagePreviewCard.heightAnchor.constraint(equalToConstant: 200),

            imagePreview.topAnchor.constraint(equalTo: imagePreviewCard.topAnchor, constant: 16),
            imagePreview.leadingAnchor.constraint(equalTo: imagePreviewCard.leadingAnchor, constant: 16),
            imagePreview.trailingAnchor.constraint(equalTo: imagePreviewCard.trailingAnchor, constant: -16),
            imagePreview.bottomAnchor.constraint(equalTo: imageStatusLabel.topAnchor, constant: -8),

            imageStatusLabel.bottomAnchor.constraint(equalTo: imagePreviewCard.bottomAnchor, constant: -16),
            imageStatusLabel.leadingAnchor.constraint(equalTo: imagePreviewCard.leadingAnchor, constant: 16),
            imageStatusLabel.trailingAnchor.constraint(equalTo: imagePreviewCard.trailingAnchor, constant: -16)
        ])

        // Process button
        processButton.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            processButton.topAnchor.constraint(equalTo: imagePreviewCard.bottomAnchor, constant: 20),
            processButton.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            processButton.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            processButton.heightAnchor.constraint(equalToConstant: 50)
        ])

        // Results
        resultsCard.translatesAutoresizingMaskIntoConstraints = false
        resultsTextView.translatesAutoresizingMaskIntoConstraints = false

        NSLayoutConstraint.activate([
            resultsCard.topAnchor.constraint(equalTo: processButton.bottomAnchor, constant: 20),
            resultsCard.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            resultsCard.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            resultsCard.heightAnchor.constraint(equalToConstant: 300),
            resultsCard.bottomAnchor.constraint(equalTo: contentView.bottomAnchor, constant: -20),

            resultsTextView.topAnchor.constraint(equalTo: resultsCard.topAnchor),
            resultsTextView.leadingAnchor.constraint(equalTo: resultsCard.leadingAnchor),
            resultsTextView.trailingAnchor.constraint(equalTo: resultsCard.trailingAnchor),
            resultsTextView.bottomAnchor.constraint(equalTo: resultsCard.bottomAnchor)
        ])

        // Loading view
        loadingView.translatesAutoresizingMaskIntoConstraints = false
        activityIndicator.translatesAutoresizingMaskIntoConstraints = false

        NSLayoutConstraint.activate([
            loadingView.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            loadingView.centerYAnchor.constraint(equalTo: view.centerYAnchor),
            loadingView.widthAnchor.constraint(equalToConstant: 120),
            loadingView.heightAnchor.constraint(equalToConstant: 120),

            activityIndicator.centerXAnchor.constraint(equalTo: loadingView.centerXAnchor),
            activityIndicator.centerYAnchor.constraint(equalTo: loadingView.centerYAnchor)
        ])
    }

    private func checkPermissions() {
        // Check camera permission
        let cameraStatus = AVCaptureDevice.authorizationStatus(for: .video)
        let photoStatus = PHPhotoLibrary.authorizationStatus()

        switch cameraStatus {
        case .authorized:
            statusLabel.text = "✅ Camera and gallery access granted"
        case .notDetermined:
            statusLabel.text = "Requesting permissions..."
            requestPermissions()
        case .denied, .restricted:
            statusLabel.text = "❌ Camera/gallery permissions required"
        @unknown default:
            break
        }
    }

    private func requestPermissions() {
        AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
            DispatchQueue.main.async {
                if granted {
                    PHPhotoLibrary.requestAuthorization { status in
                        DispatchQueue.main.async {
                            self?.checkPermissions()
                        }
                    }
                } else {
                    self?.statusLabel.text = "❌ Camera permission denied"
                }
            }
        }
    }

    @objc private func cameraButtonTapped() {
        let imagePicker = UIImagePickerController()
        imagePicker.delegate = self
        imagePicker.sourceType = .camera
        imagePicker.allowsEditing = true
        present(imagePicker, animated: true)
    }

    @objc private func galleryButtonTapped() {
        var config = PHPickerConfiguration()
        config.selectionLimit = 1
        config.filter = .images

        let picker = PHPickerViewController(configuration: config)
        picker.delegate = self
        present(picker, animated: true)
    }

    @objc private func processButtonTapped() {
        guard let image = selectedImage else { return }

        // Show loading
        loadingView.isHidden = false
        activityIndicator.startAnimating()
        processButton.isEnabled = false
        statusLabel.text = "🔄 Processing image..."

        // Convert image to base64
        guard let imageData = image.jpegData(compressionQuality: 0.8),
              let base64String = imageData.base64EncodedString() else {
            showError("Failed to process image")
            return
        }

        // Create API request
        let ocrRequest = OCRRequest(image_base64: base64String, language: "auto")

        // Call API
        Task {
            do {
                let apiService = ApiService()
                let response = try await apiService.processOCR(request: ocrRequest)

                DispatchQueue.main.async { [weak self] in
                    self?.showOCRResults(response)
                }
            } catch {
                DispatchQueue.main.async { [weak self] in
                    self?.showError("OCR processing failed: \(error.localizedDescription)")
                }
            }
        }
    }

    private func showOCRResults(_ response: MenuResponse) {
        // Hide loading
        loadingView.isHidden = true
        activityIndicator.stopAnimating()
        processButton.isEnabled = true

        // Show results
        resultsCard.isHidden = false

        var resultText = "📊 OCR Processing Results\n\n"
        resultText += "Processing Method: Regular OCR\n"
        resultText += "Processing Time: \(response.processing_time_ms)ms\n"
        resultText += "Enhanced: \(response.enhanced ? "Yes" : "No")\n"
        resultText += "Cached: \(response.cached ? "Yes" : "No")\n\n"

        resultText += "Raw Extracted Text:\n\(response.raw_text)\n\n"

        resultText += "Menu Items (\(response.menu_items.count) found):\n"
        for (index, item) in response.menu_items.enumerated() {
            resultText += "\(index + 1). \(item.name)"
            if let price = item.price {
                resultText += " - $\(String(format: "%.2f", price))"
            }
            resultText += "\n"
            if let description = item.description {
                resultText += "   \(description)\n"
            }
            if let category = item.category {
                resultText += "   Category: \(category)\n"
            }
            resultText += "\n"
        }

        resultsTextView.text = resultText
    }

    private func showError(_ message: String) {
        // Hide loading
        loadingView.isHidden = true
        activityIndicator.stopAnimating()
        processButton.isEnabled = true

        // Show error in results
        resultsCard.isHidden = false
        resultsTextView.text = "❌ Error: \(message)"
    }

    // MARK: - UIImagePickerControllerDelegate
    func imagePickerController(_ picker: UIImagePickerController, didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey : Any]) {
        if let image = info[.editedImage] as? UIImage ?? info[.originalImage] as? UIImage {
            selectedImage = image
            showImagePreview(image)
        }
        picker.dismiss(animated: true)
    }

    // MARK: - PHPickerViewControllerDelegate
    func picker(_ picker: PHPickerViewController, didFinishPicking results: [PHPickerResult]) {
        picker.dismiss(animated: true)

        guard let result = results.first else { return }

        result.itemProvider.loadObject(ofClass: UIImage.self) { [weak self] object, error in
            if let image = object as? UIImage {
                DispatchQueue.main.async {
                    self?.selectedImage = image
                    self?.showImagePreview(image)
                }
            }
        }
    }

    private func showImagePreview(_ image: UIImage) {
        imagePreview.image = image
        imagePreviewCard.isHidden = false
        processButton.isHidden = false
        imageStatusLabel.text = "Image selected! Ready for OCR processing"
    }
}