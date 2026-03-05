import UIKit
import Combine
import PhotosUI

class MainViewController: UIViewController, UIImagePickerControllerDelegate, UINavigationControllerDelegate {

    // MARK: - Services
    private let apiService = ApiService()
    private let ocrService: OcrService
    private let authViewModel = AuthViewModel()
    private var cancellables = Set<AnyCancellable>()

    // MARK: - UI Components
    private let scrollView: UIScrollView = {
        let scrollView = UIScrollView()
        scrollView.showsVerticalScrollIndicator = false
        return scrollView
    }()

    private let contentView: UIView = {
        let view = UIView()
        return view
    }()

    private let titleLabel: UILabel = {
        let label = UILabel()
        label.text = "Menu OCR - Test Version"
        label.font = .systemFont(ofSize: 24, weight: .bold)
        label.textAlignment = .center
        return label
    }()

    private let apiStatusLabel: UILabel = {
        let label = UILabel()
        let baseURL = AppConfig.MenuOcrApi.useLocal ? AppConfig.MenuOcrApi.localBaseURL : AppConfig.MenuOcrApi.baseURL
        label.text = "FastAPI Backend: \(baseURL)\nStatus: Testing Connection..."
        label.font = .systemFont(ofSize: 14)
        label.textAlignment = .center
        label.numberOfLines = 0
        label.textColor = .secondaryLabel
        return label
    }()

    private let statusLabel: UILabel = {
        let label = UILabel()
        label.text = "Ready to test OCR functionality"
        label.font = .systemFont(ofSize: 16, weight: .medium)
        label.textAlignment = .center
        label.numberOfLines = 0
        label.textColor = .label
        return label
    }()

    private let imageView: UIImageView = {
        let imageView = UIImageView()
        imageView.contentMode = .scaleAspectFit
        imageView.backgroundColor = .systemGray6
        imageView.layer.borderWidth = 1
        imageView.layer.borderColor = UIColor.systemGray4.cgColor
        imageView.layer.cornerRadius = 8
        imageView.clipsToBounds = true
        imageView.isUserInteractionEnabled = true
        return imageView
    }()

    private let captureButton: UIButton = {
        let button = UIButton(type: .system)
        button.setTitle("📷 Capture Image", for: .normal)
        button.backgroundColor = .systemBlue
        button.setTitleColor(.white, for: .normal)
        button.layer.cornerRadius = 8
        button.titleLabel?.font = .systemFont(ofSize: 16, weight: .medium)
        return button
    }()

    private let selectButton: UIButton = {
        let button = UIButton(type: .system)
        button.setTitle("🖼️ Select from Gallery", for: .normal)
        button.backgroundColor = .systemGreen
        button.setTitleColor(.white, for: .normal)
        button.layer.cornerRadius = 8
        button.titleLabel?.font = .systemFont(ofSize: 16, weight: .medium)
        return button
    }()

    private let testApiButton: UIButton = {
        let button = UIButton(type: .system)
        button.setTitle("🧪 Test API Connection", for: .normal)
        button.backgroundColor = .systemOrange
        button.setTitleColor(.white, for: .normal)
        button.layer.cornerRadius = 8
        button.titleLabel?.font = .systemFont(ofSize: 16, weight: .medium)
        return button
    }()

    private let tableExtractionButton: UIButton = {
        let button = UIButton(type: .system)
        button.setTitle("📊 Extract Table Data", for: .normal)
        button.backgroundColor = .systemPurple
        button.setTitleColor(.white, for: .normal)
        button.layer.cornerRadius = 8
        button.titleLabel?.font = .systemFont(ofSize: 16, weight: .medium)
        button.isHidden = true
        return button
    }()

    private let healthConditionsButton: UIButton = {
        let button = UIButton(type: .system)
        button.setTitle("💊 Health Conditions", for: .normal)
        button.backgroundColor = .systemRed
        button.setTitleColor(.white, for: .normal)
        button.layer.cornerRadius = 8
        button.titleLabel?.font = .systemFont(ofSize: 16, weight: .medium)
        button.isHidden = true
        return button
    }()

    private let profileButton: UIButton = {
        let button = UIButton(type: .system)
        button.setTitle("👤 User Profile", for: .normal)
        button.backgroundColor = .systemIndigo
        button.setTitleColor(.white, for: .normal)
        button.layer.cornerRadius = 8
        button.titleLabel?.font = .systemFont(ofSize: 16, weight: .medium)
        button.isHidden = true
        return button
    }()

    private let paymentButton: UIButton = {
        let button = UIButton(type: .system)
        button.setTitle("💳 Payment Test", for: .normal)
        button.backgroundColor = .systemGray
        button.setTitleColor(.white, for: .normal)
        button.layer.cornerRadius = 8
        button.titleLabel?.font = .systemFont(ofSize: 16, weight: .medium)
        button.isHidden = true
        return button
    }()

    private let tableView: UITableView = {
        let tableView = UITableView()
        tableView.register(DishTableViewCell.self, forCellReuseIdentifier: "DishCell")
        tableView.isHidden = true
        tableView.layer.borderWidth = 1
        tableView.layer.borderColor = UIColor.systemGray4.cgColor
        tableView.layer.cornerRadius = 8
        return tableView
    }()

    private let activityIndicator: UIActivityIndicatorView = {
        let indicator = UIActivityIndicatorView(style: .large)
        indicator.hidesWhenStopped = true
        indicator.color = .systemBlue
        return indicator
    }()

    private let textView: UITextView = {
        let textView = UITextView()
        textView.isEditable = false
        textView.isScrollEnabled = true
        textView.font = .monospacedSystemFont(ofSize: 12, weight: .regular)
        textView.backgroundColor = .systemGray6
        textView.layer.cornerRadius = 8
        textView.isHidden = true
        return textView
    }()

    // MARK: - State
    private var currentMenu: Menu?
    private var extractedText: String = ""
    private var extractedTableData: String = ""

    // MARK: - Initialization
    init() {
        ocrService = OcrService(apiService: apiService)
        super.init(nibName: nil, bundle: nil)
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
        setupNavigationBar()
        checkPermissions()
        testApiConnection()
    }

    // MARK: - UI Setup
    private func setupUI() {
        view.backgroundColor = .systemBackground
        
        // Setup scroll view
        view.addSubview(scrollView)
        scrollView.addSubview(contentView)
        
        scrollView.translatesAutoresizingMaskIntoConstraints = false
        contentView.translatesAutoresizingMaskIntoConstraints = false
        
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
        
        // Add all components to content view
        [titleLabel, apiStatusLabel, statusLabel, captureButton, selectButton,
         testApiButton, tableExtractionButton, healthConditionsButton, profileButton,
         paymentButton, imageView, tableView, textView, activityIndicator].forEach {
            $0.translatesAutoresizingMaskIntoConstraints = false
            contentView.addSubview($0)
        }
        
        // Setup table view
        tableView.dataSource = self
        tableView.delegate = self
        
        // Setup image view tap gesture
        let tapGesture = UITapGestureRecognizer(target: self, action: #selector(imageViewTapped))
        imageView.addGestureRecognizer(tapGesture)
        
        // Layout constraints
        setupConstraints()
        
        // Button actions
        captureButton.addTarget(self, action: #selector(captureImageTapped), for: .touchUpInside)
        selectButton.addTarget(self, action: #selector(selectImageTapped), for: .touchUpInside)
        testApiButton.addTarget(self, action: #selector(testApiConnection), for: .touchUpInside)
        tableExtractionButton.addTarget(self, action: #selector(extractTableData), for: .touchUpInside)
        healthConditionsButton.addTarget(self, action: #selector(showHealthConditions), for: .touchUpInside)
        profileButton.addTarget(self, action: #selector(showUserProfile), for: .touchUpInside)
        paymentButton.addTarget(self, action: #selector(testPayment), for: .touchUpInside)
    }
    
    private func setupConstraints() {
        let padding: CGFloat = 20
        let buttonHeight: CGFloat = 50
        
        NSLayoutConstraint.activate([
            // Title
            titleLabel.topAnchor.constraint(equalTo: contentView.topAnchor, constant: 20),
            titleLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: padding),
            titleLabel.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -padding),
            
            // API Status
            apiStatusLabel.topAnchor.constraint(equalTo: titleLabel.bottomAnchor, constant: 10),
            apiStatusLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: padding),
            apiStatusLabel.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -padding),
            
            // Status
            statusLabel.topAnchor.constraint(equalTo: apiStatusLabel.bottomAnchor, constant: 10),
            statusLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: padding),
            statusLabel.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -padding),
            
            // Capture Button
            captureButton.topAnchor.constraint(equalTo: statusLabel.bottomAnchor, constant: 20),
            captureButton.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: padding),
            captureButton.trailingAnchor.constraint(equalTo: contentView.centerXAnchor, constant: -5),
            captureButton.heightAnchor.constraint(equalToConstant: buttonHeight),
            
            // Select Button
            selectButton.topAnchor.constraint(equalTo: statusLabel.bottomAnchor, constant: 20),
            selectButton.leadingAnchor.constraint(equalTo: contentView.centerXAnchor, constant: 5),
            selectButton.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -padding),
            selectButton.heightAnchor.constraint(equalToConstant: buttonHeight),
            
            // Test API Button
            testApiButton.topAnchor.constraint(equalTo: captureButton.bottomAnchor, constant: 10),
            testApiButton.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: padding),
            testApiButton.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -padding),
            testApiButton.heightAnchor.constraint(equalToConstant: buttonHeight),
            
            // Table Extraction Button
            tableExtractionButton.topAnchor.constraint(equalTo: testApiButton.bottomAnchor, constant: 10),
            tableExtractionButton.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: padding),
            tableExtractionButton.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -padding),
            tableExtractionButton.heightAnchor.constraint(equalToConstant: buttonHeight),
            
            // Health Conditions Button
            healthConditionsButton.topAnchor.constraint(equalTo: tableExtractionButton.bottomAnchor, constant: 10),
            healthConditionsButton.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: padding),
            healthConditionsButton.trailingAnchor.constraint(equalTo: contentView.centerXAnchor, constant: -5),
            healthConditionsButton.heightAnchor.constraint(equalToConstant: buttonHeight),
            
            // Profile Button
            profileButton.topAnchor.constraint(equalTo: tableExtractionButton.bottomAnchor, constant: 10),
            profileButton.leadingAnchor.constraint(equalTo: contentView.centerXAnchor, constant: 5),
            profileButton.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -padding),
            profileButton.heightAnchor.constraint(equalToConstant: buttonHeight),
            
            // Payment Button
            paymentButton.topAnchor.constraint(equalTo: healthConditionsButton.bottomAnchor, constant: 10),
            paymentButton.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: padding),
            paymentButton.trailingAnchor.constraint(equalTo: contentView.centerXAnchor, constant: -5),
            paymentButton.heightAnchor.constraint(equalToConstant: buttonHeight),
            
            // Image View
            imageView.topAnchor.constraint(equalTo: paymentButton.bottomAnchor, constant: 20),
            imageView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: padding),
            imageView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -padding),
            imageView.heightAnchor.constraint(equalToConstant: 300),
            
            // Table View
            tableView.topAnchor.constraint(equalTo: imageView.bottomAnchor, constant: 20),
            tableView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: padding),
            tableView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -padding),
            tableView.heightAnchor.constraint(equalToConstant: 200),
            
            // Text View
            textView.topAnchor.constraint(equalTo: imageView.bottomAnchor, constant: 20),
            textView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: padding),
            textView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -padding),
            textView.heightAnchor.constraint(equalToConstant: 200),
            
            // Activity Indicator
            activityIndicator.centerXAnchor.constraint(equalTo: contentView.centerXAnchor),
            activityIndicator.centerYAnchor.constraint(equalTo: contentView.centerYAnchor),
            
            // Content View Bottom
            contentView.bottomAnchor.constraint(equalTo: tableView.bottomAnchor, constant: padding)
        ])
    }

    private func setupNavigationBar() {
        navigationItem.title = "Menu OCR"
        navigationItem.rightBarButtonItem = UIBarButtonItem(
            title: "Sign Out",
            style: .plain,
            target: self,
            action: #selector(signOutTapped)
        )
    }

    // MARK: - Permissions
    private func checkPermissions() {
        // Request camera permission
        AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
            DispatchQueue.main.async {
                if granted {
                    self?.statusLabel.text = "Camera access granted! Ready to capture images"
                } else {
                    self?.statusLabel.text = "Camera access denied. Please enable in Settings"
                }
            }
        }
    }

    // MARK: - API Testing
    @objc private func testApiConnection() {
        let baseURL = AppConfig.MenuOcrApi.useLocal ? AppConfig.MenuOcrApi.localBaseURL : AppConfig.MenuOcrApi.baseURL
        apiStatusLabel.text = "FastAPI Backend: \(baseURL)\nStatus: Testing Connection..."
        statusLabel.text = "🧪 Testing API connection..."

        Task {
            do {
                let isConnected = await apiService.testApiConnection()
                await MainActor.run {
                    if isConnected {
                        apiStatusLabel.text = "✅ FastAPI Backend: \(baseURL)\nStatus: Connected Successfully"
                        statusLabel.text = "✅ API connection successful!\n✅ Backend services available\n✅ iOS app integration ready!"
                        showAdvancedButtons()
                    } else {
                        apiStatusLabel.text = "❌ FastAPI Backend: \(baseURL)\nStatus: Connection Failed"
                        statusLabel.text = "❌ API connection failed\n❌ Backend may be offline"
                    }
                }
            } catch {
                await MainActor.run {
                    apiStatusLabel.text = "❌ FastAPI Backend: \(baseURL)\nStatus: Error"
                    statusLabel.text = "❌ API test failed: \(error.localizedDescription)"
                }
            }
        }
    }

    private func showAdvancedButtons() {
        tableExtractionButton.isHidden = false
        healthConditionsButton.isHidden = false
        profileButton.isHidden = false
        paymentButton.isHidden = false
    }

    // MARK: - Image Handling
    @objc private func captureImageTapped() {
        let imagePicker = UIImagePickerController()
        imagePicker.delegate = self
        imagePicker.sourceType = .camera
        imagePicker.allowsEditing = true
        present(imagePicker, animated: true)
    }

    @objc private func selectImageTapped() {
        let imagePicker = UIImagePickerController()
        imagePicker.delegate = self
        imagePicker.sourceType = .photoLibrary
        imagePicker.allowsEditing = true
        present(imagePicker, animated: true)
    }

    @objc private func imageViewTapped() {
        let alert = UIAlertController(title: "Image Options", message: "Choose an action", preferredStyle: .actionSheet)
        alert.addAction(UIAlertAction(title: "Capture New", style: .default) { _ in
            self.captureImageTapped()
        })
        alert.addAction(UIAlertAction(title: "Select from Gallery", style: .default) { _ in
            self.selectImageTapped()
        })
        alert.addAction(UIAlertAction(title: "Cancel", style: .cancel))
        present(alert, animated: true)
    }

    // MARK: - OCR Processing
    private func processImage(_ image: UIImage) {
        activityIndicator.startAnimating()
        statusLabel.text = "Processing image with OCR..."

        Task {
            do {
                // First try local Vision framework
                let localText = try await ocrService.processImageLocally(image)
                await MainActor.run {
                    self.extractedText = localText
                    self.textView.text = localText
                    self.textView.isHidden = false
                    self.tableView.isHidden = true
                    self.statusLabel.text = "✅ OCR completed!\n📝 Text extracted locally\n🌐 Ready for backend processing"
                }

                // Then try backend processing
                let menuResponse = try await ocrService.processImageViaAPI(image)
                await MainActor.run {
                    self.statusLabel.text = "✅ Full processing completed!\n📝 Ready for dish extraction"
                }

            } catch {
                await MainActor.run {
                    self.statusLabel.text = "❌ OCR processing failed: \(error.localizedDescription)"
                    self.activityIndicator.stopAnimating()
                }
            }
        }
    }

    // MARK: - Advanced Features
    @objc private func extractTableData() {
        guard !extractedText.isEmpty else {
            statusLabel.text = "⚠️ Please process an image first"
            return
        }

        activityIndicator.startAnimating()
        statusLabel.text = "🧠 Extracting table data with Qwen AI..."

        Task {
            do {
                let tableResponse = try await ocrService.extractTableFromText(extractedText, format: "markdown")
                await MainActor.run {
                    self.extractedTableData = tableResponse.rawTable
                    self.textView.text = tableResponse.rawTable
                    self.textView.isScrollEnabled = true
                    self.statusLabel.text = "✅ Table extraction completed!\n🤖 Model: \(tableResponse.modelUsed)\n💰 Tokens used: \(tableResponse.tokensUsed)"
                    self.activityIndicator.stopAnimating()
                }
            } catch {
                await MainActor.run {
                    self.statusLabel.text = "❌ Table extraction failed: \(error.localizedDescription)"
                    self.activityIndicator.stopAnimating()
                }
            }
        }
    }

    @objc private func showHealthConditions() {
        let alert = UIAlertController(title: "Health Conditions", message: "Backend feature ready", preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "OK", style: .default))
        present(alert, animated: true)
    }

    @objc private func showUserProfile() {
        let alert = UIAlertController(title: "User Profile", message: "User preferences feature ready", preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "OK", style: .default))
        present(alert, animated: true)
    }

    @objc private func testPayment() {
        let alert = UIAlertController(title: "Payment Test", message: "Payment processing feature ready", preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "OK", style: .default))
        present(alert, animated: true)
    }

    @objc private func signOutTapped() {
        authViewModel.signOut()
        navigationController?.popToRootViewController(animated: true)
    }

    // MARK: - UIImagePickerControllerDelegate
    func imagePickerController(_ picker: UIImagePickerController, didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey : Any]) {
        if let image = info[.editedImage] as? UIImage ?? info[.originalImage] as? UIImage {
            imageView.image = image
            processImage(image)
        }
        dismiss(animated: true)
    }

    func imagePickerControllerDidCancel(_ picker: UIImagePickerController) {
        dismiss(animated: true)
    }
}

extension MainViewController: UITableViewDataSource, UITableViewDelegate {
    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        return currentMenu?.dishes.count ?? 0
    }

    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        guard let cell = tableView.dequeueReusableCell(withIdentifier: "DishCell", for: indexPath) as? DishTableViewCell else {
            return UITableViewCell()
        }
        if let dish = currentMenu?.dishes[indexPath.row] {
            cell.configure(with: dish)
        }
        return cell
    }

    func tableView(_ tableView: UITableView, heightForRowAt indexPath: IndexPath) -> CGFloat {
        return 80
    }
}