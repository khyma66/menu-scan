//
//  HealthConditionsViewController.swift
//  MenuOCR
//
//  Health conditions management - equivalent to Android HealthConditionsFragment.kt
//

import UIKit

// MARK: - Health Profile Models

struct HealthProfile: Codable {
    let healthConditions: [String]
    let allergies: [String]
    let dietaryPreferences: [String]
    let medicalNotes: String?
    
    enum CodingKeys: String, CodingKey {
        case healthConditions = "health_conditions"
        case allergies
        case dietaryPreferences = "dietary_preferences"
        case medicalNotes = "medical_notes"
    }
}

struct HealthProfileWrapper: Codable {
    let healthProfile: HealthProfile?
    
    enum CodingKeys: String, CodingKey {
        case healthProfile = "health_profile"
    }
}

struct HealthProfileRequest: Codable {
    let healthConditions: [String]
    let allergies: [String]
    let dietaryPreferences: [String]
    let medicalNotes: String?
    
    enum CodingKeys: String, CodingKey {
        case healthConditions = "health_conditions"
        case allergies
        case dietaryPreferences = "dietary_preferences"
        case medicalNotes = "medical_notes"
    }
}

// MARK: - Health Conditions View Controller

class HealthConditionsViewController: UIViewController {
    
    // MARK: - Services
    
    private let apiService = ApiService()
    
    // MARK: - UI Components
    
    private let scrollView = UIScrollView()
    private let contentView = UIView()
    
    // Header
    private let headerView = UIView()
    private let headerIconLabel = UILabel()
    private let titleLabel = UILabel()
    private let subtitleLabel = UILabel()
    
    // Form
    private let formCard = UIView()
    private let healthConditionsTextView = UITextView()
    private let healthConditionsLabel = UILabel()
    private let allergiesTextView = UITextView()
    private let allergiesLabel = UILabel()
    private let dietaryPreferencesTextView = UITextView()
    private let dietaryPreferencesLabel = UILabel()
    private let medicalNotesTextView = UITextView()
    private let medicalNotesLabel = UILabel()
    
    // Buttons
    private let saveButton = UIButton()
    private let loadingIndicator = UIActivityIndicatorView(style: .medium)
    private let loadingContainer = UIView()
    private let loadingLabel = UILabel()
    
    // Status
    private let statusLabel = UILabel()
    
    // MARK: - Lifecycle
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
       setupConstraints()
        loadCurrentProfile()
    }
    
    // MARK: - UI Setup
    
    private func setupUI() {
        view.backgroundColor = .systemGray6
        
        // Scroll view
        scrollView.translatesAutoresizingMaskIntoConstraints = false
        contentView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(scrollView)
        scrollView.addSubview(contentView)
        
        // Header
        setupHeader()
        
        // Form
        setupForm()
        
        // Loading
        setupLoading()
        
        // Status
        statusLabel.font = .systemFont(ofSize: 14)
        statusLabel.textAlignment = .center
        statusLabel.numberOfLines = 0
        statusLabel.isHidden = true
        statusLabel.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(statusLabel)
    }
    
    private func setupHeader() {
        headerView.backgroundColor = UIColor(red: 1.0, green: 0.3, blue: 0.22, alpha: 1.0) // DoorDash orange
        headerView.layer.cornerRadius = 16
        headerView.layer.maskedCorners = [.layerMinXMaxYCorner, .layerMaxXMaxYCorner]
        headerView.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(headerView)
        
        headerIconLabel.text = "💊"
        headerIconLabel.font = .systemFont(ofSize: 40)
        headerIconLabel.textAlignment = .center
        headerIconLabel.translatesAutoresizingMaskIntoConstraints = false
        headerView.addSubview(headerIconLabel)
        
        titleLabel.text = "Health Conditions"
        titleLabel.font = .boldSystemFont(ofSize: 24)
        titleLabel.textColor = .white
        titleLabel.textAlignment = .center
        titleLabel.translatesAutoresizingMaskIntoConstraints = false
        headerView.addSubview(titleLabel)
        
        subtitleLabel.text = "Set your health conditions for personalized recommendations"
        subtitleLabel.font = .systemFont(ofSize: 14)
        subtitleLabel.textColor = .white.withAlphaComponent(0.9)
        subtitleLabel.textAlignment = .center
        subtitleLabel.numberOfLines = 0
        subtitleLabel.translatesAutoresizingMaskIntoConstraints = false
        headerView.addSubview(subtitleLabel)
    }
    
    private func setupForm() {
        // Form card
        formCard.backgroundColor = .systemBackground
        formCard.layer.cornerRadius = 12
        formCard.layer.shadowColor = UIColor.black.cgColor
        formCard.layer.shadowOffset = CGSize(width: 0, height: 2)
        formCard.layer.shadowOpacity = 0.1
        formCard.layer.shadowRadius = 4
        formCard.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(formCard)
        
        // Health Conditions
        healthConditionsLabel.text = "🏥 Health Conditions"
        healthConditionsLabel.font = .boldSystemFont(ofSize: 16)
        healthConditionsLabel.translatesAutoresizingMaskIntoConstraints = false
        formCard.addSubview(healthConditionsLabel)
        
        healthConditionsTextView.font = .systemFont(ofSize: 16)
        healthConditionsTextView.layer.borderColor = UIColor.systemGray4.cgColor
        healthConditionsTextView.layer.borderWidth = 1
        healthConditionsTextView.layer.cornerRadius = 8
        healthConditionsTextView.text = "e.g., Diabetes, High Blood Pressure"
        healthConditionsTextView.textColor = .placeholderText
        healthConditionsTextView.textContainerInset = UIEdgeInsets(top: 12, left: 8, bottom: 12, right: 8)
        healthConditionsTextView.delegate = self
        healthConditionsTextView.translatesAutoresizingMaskIntoConstraints = false
        formCard.addSubview(healthConditionsTextView)
        
        // Allergies
        allergiesLabel.text = "⚠️ Allergies"
        allergiesLabel.font = .boldSystemFont(ofSize: 16)
        allergiesLabel.translatesAutoresizingMaskIntoConstraints = false
        formCard.addSubview(allergiesLabel)
        
        allergiesTextView.font = .systemFont(ofSize: 16)
        allergiesTextView.layer.borderColor = UIColor.systemGray4.cgColor
        allergiesTextView.layer.borderWidth = 1
        allergiesTextView.layer.cornerRadius = 8
        allergiesTextView.text = "e.g., Peanuts, Shellfish, Gluten"
        allergiesTextView.textColor = .placeholderText
        allergiesTextView.textContainerInset = UIEdgeInsets(top: 12, left: 8, bottom: 12, right: 8)
        allergiesTextView.delegate = self
        allergiesTextView.translatesAutoresizingMaskIntoConstraints = false
        formCard.addSubview(allergiesTextView)
        
        // Dietary Preferences
        dietaryPreferencesLabel.text = "🥗 Dietary Preferences"
        dietaryPreferencesLabel.font = .boldSystemFont(ofSize: 16)
        dietaryPreferencesLabel.translatesAutoresizingMaskIntoConstraints = false
        formCard.addSubview(dietaryPreferencesLabel)
        
        dietaryPreferencesTextView.font = .systemFont(ofSize: 16)
        dietaryPreferencesTextView.layer.borderColor = UIColor.systemGray4.cgColor
        dietaryPreferencesTextView.layer.borderWidth = 1
        dietaryPreferencesTextView.layer.cornerRadius = 8
        dietaryPreferencesTextView.text = "e.g., Vegetarian, Vegan, Keto"
        dietaryPreferencesTextView.textColor = .placeholderText
        dietaryPreferencesTextView.textContainerInset = UIEdgeInsets(top: 12, left: 8, bottom: 12, right: 8)
        dietaryPreferencesTextView.delegate = self
        dietaryPreferencesTextView.translatesAutoresizingMaskIntoConstraints = false
        formCard.addSubview(dietaryPreferencesTextView)
        
        // Medical Notes
        medicalNotesLabel.text = "📝 Medical Notes"
        medicalNotesLabel.font = .boldSystemFont(ofSize: 16)
        medicalNotesLabel.translatesAutoresizingMaskIntoConstraints = false
        formCard.addSubview(medicalNotesLabel)
        
        medicalNotesTextView.font = .systemFont(ofSize: 16)
        medicalNotesTextView.layer.borderColor = UIColor.systemGray4.cgColor
        medicalNotesTextView.layer.borderWidth = 1
        medicalNotesTextView.layer.cornerRadius = 8
        medicalNotesTextView.text = "Any additional medical notes..."
        medicalNotesTextView.textColor = .placeholderText
        medicalNotesTextView.textContainerInset = UIEdgeInsets(top: 12, left: 8, bottom: 12, right: 8)
        medicalNotesTextView.delegate = self
        medicalNotesTextView.translatesAutoresizingMaskIntoConstraints = false
        formCard.addSubview(medicalNotesTextView)
        
        // Save Button
        saveButton.setTitle("💾 Save Profile", for: .normal)
        saveButton.backgroundColor = UIColor(red: 1.0, green: 0.3, blue: 0.22, alpha: 1.0)
        saveButton.setTitleColor(.white, for: .normal)
        saveButton.titleLabel?.font = .boldSystemFont(ofSize: 18)
        saveButton.layer.cornerRadius = 12
        saveButton.addTarget(self, action: #selector(saveProfileTapped), for: .touchUpInside)
        saveButton.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(saveButton)
    }
    
    private func setupLoading() {
        loadingContainer.backgroundColor = .systemBackground
        loadingContainer.layer.cornerRadius = 12
        loadingContainer.isHidden = true
        loadingContainer.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(loadingContainer)
        
        loadingIndicator.color = .systemOrange
        loadingIndicator.translatesAutoresizingMaskIntoConstraints = false
        loadingContainer.addSubview(loadingIndicator)
        
        loadingLabel.text = "Saving profile..."
        loadingLabel.font = .systemFont(ofSize: 16)
        loadingLabel.textColor = .secondaryLabel
        loadingLabel.translatesAutoresizingMaskIntoConstraints = false
        loadingContainer.addSubview(loadingLabel)
    }
    
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
            
            // Form card
            formCard.topAnchor.constraint(equalTo: headerView.bottomAnchor, constant: 20),
            formCard.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            formCard.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            
            // Health conditions
            healthConditionsLabel.topAnchor.constraint(equalTo: formCard.topAnchor, constant: 16),
            healthConditionsLabel.leadingAnchor.constraint(equalTo: formCard.leadingAnchor, constant: 16),
            healthConditionsLabel.trailingAnchor.constraint(equalTo: formCard.trailingAnchor, constant: -16),
            
            healthConditionsTextView.topAnchor.constraint(equalTo: healthConditionsLabel.bottomAnchor, constant: 8),
            healthConditionsTextView.leadingAnchor.constraint(equalTo: formCard.leadingAnchor, constant: 16),
            healthConditionsTextView.trailingAnchor.constraint(equalTo: formCard.trailingAnchor, constant: -16),
            healthConditionsTextView.heightAnchor.constraint(equalToConstant: 80),
            
            // Allergies
            allergiesLabel.topAnchor.constraint(equalTo: healthConditionsTextView.bottomAnchor, constant: 16),
            allergiesLabel.leadingAnchor.constraint(equalTo: formCard.leadingAnchor, constant: 16),
            allergiesLabel.trailingAnchor.constraint(equalTo: formCard.trailingAnchor, constant: -16),
            
            allergiesTextView.topAnchor.constraint(equalTo: allergiesLabel.bottomAnchor, constant: 8),
            allergiesTextView.leadingAnchor.constraint(equalTo: formCard.leadingAnchor, constant: 16),
            allergiesTextView.trailingAnchor.constraint(equalTo: formCard.trailingAnchor, constant: -16),
            allergiesTextView.heightAnchor.constraint(equalToConstant: 80),
            
            // Dietary preferences
            dietaryPreferencesLabel.topAnchor.constraint(equalTo: allergiesTextView.bottomAnchor, constant: 16),
            dietaryPreferencesLabel.leadingAnchor.constraint(equalTo: formCard.leadingAnchor, constant: 16),
            dietaryPreferencesLabel.trailingAnchor.constraint(equalTo: formCard.trailingAnchor, constant: -16),
            
            dietaryPreferencesTextView.topAnchor.constraint(equalTo: dietaryPreferencesLabel.bottomAnchor, constant: 8),
            dietaryPreferencesTextView.leadingAnchor.constraint(equalTo: formCard.leadingAnchor, constant: 16),
            dietaryPreferencesTextView.trailingAnchor.constraint(equalTo: formCard.trailingAnchor, constant: -16),
            dietaryPreferencesTextView.heightAnchor.constraint(equalToConstant: 80),
            
            // Medical notes
            medicalNotesLabel.topAnchor.constraint(equalTo: dietaryPreferencesTextView.bottomAnchor, constant: 16),
            medicalNotesLabel.leadingAnchor.constraint(equalTo: formCard.leadingAnchor, constant: 16),
            medicalNotesLabel.trailingAnchor.constraint(equalTo: formCard.trailingAnchor, constant: -16),
            
            medicalNotesTextView.topAnchor.constraint(equalTo: medicalNotesLabel.bottomAnchor, constant: 8),
            medicalNotesTextView.leadingAnchor.constraint(equalTo: formCard.leadingAnchor, constant: 16),
            medicalNotesTextView.trailingAnchor.constraint(equalTo: formCard.trailingAnchor, constant: -16),
            medicalNotesTextView.heightAnchor.constraint(equalToConstant: 80),
            medicalNotesTextView.bottomAnchor.constraint(equalTo: formCard.bottomAnchor, constant: -16),
            
            // Save button
            saveButton.topAnchor.constraint(equalTo: formCard.bottomAnchor, constant: 20),
            saveButton.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            saveButton.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            saveButton.heightAnchor.constraint(equalToConstant: 50),
            
            // Loading
            loadingContainer.topAnchor.constraint(equalTo: saveButton.topAnchor),
            loadingContainer.leadingAnchor.constraint(equalTo: saveButton.leadingAnchor),
            loadingContainer.trailingAnchor.constraint(equalTo: saveButton.trailingAnchor),
            loadingContainer.heightAnchor.constraint(equalToConstant: 50),
            
            loadingIndicator.leadingAnchor.constraint(equalTo: loadingContainer.leadingAnchor, constant: 16),
            loadingIndicator.centerYAnchor.constraint(equalTo: loadingContainer.centerYAnchor),
            
            loadingLabel.leadingAnchor.constraint(equalTo: loadingIndicator.trailingAnchor, constant: 8),
            loadingLabel.centerYAnchor.constraint(equalTo: loadingContainer.centerYAnchor),
            
            // Status
            statusLabel.topAnchor.constraint(equalTo: saveButton.bottomAnchor, constant: 16),
            statusLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            statusLabel.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            statusLabel.bottomAnchor.constraint(equalTo: contentView.bottomAnchor, constant: -32)
        ])
    }
    
    // MARK: - Data Loading
    
    private func loadCurrentProfile() {
        Task {
            do {
                let profile = try await apiService.getHealthProfile()
                await MainActor.run {
                    populateFields(with: profile)
                    updateStatus("✅ Profile loaded successfully", isSuccess: true)
                }
            } catch {
                await MainActor.run {
                    updateStatus("ℹ️ No existing profile found. Create a new one.", isSuccess: true)
                }
            }
        }
    }
    
    private func populateFields(with profile: HealthProfile) {
        if !profile.healthConditions.isEmpty {
            healthConditionsTextView.text = profile.healthConditions.joined(separator: ", ")
            healthConditionsTextView.textColor = .label
        }
        if !profile.allergies.isEmpty {
            allergiesTextView.text = profile.allergies.joined(separator: ", ")
            allergiesTextView.textColor = .label
        }
        if !profile.dietaryPreferences.isEmpty {
            dietaryPreferencesTextView.text = profile.dietaryPreferences.joined(separator: ", ")
            dietaryPreferencesTextView.textColor = .label
        }
        if let notes = profile.medicalNotes, !notes.isEmpty {
            medicalNotesTextView.text = notes
            medicalNotesTextView.textColor = .label
        }
    }
    
    // MARK: - Actions
    
    @objc private func saveProfileTapped() {
        // Parse input values
        let healthConditions = parseInput(healthConditionsTextView.text)
        let allergies = parseInput(allergiesTextView.text)
        let dietaryPreferences = parseInput(dietaryPreferencesTextView.text)
        let medicalNotes = parseMedicalNotes(medicalNotesTextView.text)
        
        // Validate
        if healthConditions.isEmpty && allergies.isEmpty && dietaryPreferences.isEmpty && medicalNotes == nil {
            showAlert(title: "Missing Information", message: "Please enter at least one health condition or preference")
            return
        }
        
        // Show loading
        showLoading(true)
        
        // Save profile
        Task {
            do {
                let request = HealthProfileRequest(
                    healthConditions: healthConditions,
                    allergies: allergies,
                    dietaryPreferences: dietaryPreferences,
                    medicalNotes: medicalNotes
                )
                _ = try await apiService.updateHealthProfile(request: request)
                
                await MainActor.run {
                    showLoading(false)
                    updateStatus("✅ Health profile saved successfully!", isSuccess: true)
                    showAlert(title: "Success", message: "Your health profile has been saved!")
                }
            } catch {
                await MainActor.run {
                    showLoading(false)
                    updateStatus("❌ Error: \(error.localizedDescription)", isSuccess: false)
                    showAlert(title: "Error", message: error.localizedDescription)
                }
            }
        }
    }
    
    private func parseInput(_ text: String) -> [String] {
        return text
            .replacingOccurrences(of: "e.g., ", with: "")
            .split(separator: ",")
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
    }
    
    private func parseMedicalNotes(_ text: String) -> String? {
        let cleaned = text.replacingOccurrences(of: "Any additional medical notes...", with: "")
            .trimmingCharacters(in: .whitespacesAndNewlines)
        return cleaned.isEmpty ? nil : cleaned
    }
    
    // MARK: - UI Helpers
    
    private func showLoading(_ show: Bool) {
        loadingContainer.isHidden = !show
        saveButton.isHidden = show
        if show {
            loadingIndicator.startAnimating()
        } else {
            loadingIndicator.stopAnimating()
        }
    }
    
    private func updateStatus(_ message: String, isSuccess: Bool) {
        statusLabel.text = message
        statusLabel.textColor = isSuccess ? .systemGreen : .systemRed
        statusLabel.isHidden = false
    }
    
    private func showAlert(title: String, message: String) {
        let alert = UIAlertController(title: title, message: message, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "OK", style: .default))
        present(alert, animated: true)
    }
}

// MARK: - UITextViewDelegate

extension HealthConditionsViewController: UITextViewDelegate {
    func textViewDidBeginEditing(_ textView: UITextView) {
        if textView.textColor == .placeholderText {
            textView.text = ""
            textView.textColor = .label
        }
    }
    
    func textViewDidEndEditing(_ textView: UITextView) {
        if textView.text.isEmpty {
            switch textView {
            case healthConditionsTextView:
                textView.text = "e.g., Diabetes, High Blood Pressure"
            case allergiesTextView:
                textView.text = "e.g., Peanuts, Shellfish, Gluten"
            case dietaryPreferencesTextView:
                textView.text = "e.g., Vegetarian, Vegan, Keto"
            case medicalNotesTextView:
                textView.text = "Any additional medical notes..."
            default:
                break
            }
            textView.textColor = .placeholderText
        }
    }
}

// MARK: - API Service Extension for Health Profile

extension ApiService {
    
    func getHealthProfile() async throws -> HealthProfile {
        let url = URL(string: "\(baseURL)/health/profile")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let authToken = await getAuthToken() {
            request.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        
        let wrapper = try JSONDecoder().decode(HealthProfileWrapper.self, from: data)
        return wrapper.healthProfile ?? HealthProfile(healthConditions: [], allergies: [], dietaryPreferences: [], medicalNotes: nil)
    }
    
    func updateHealthProfile(request: HealthProfileRequest) async throws -> HealthProfile {
        let url = URL(string: "\(baseURL)/health/profile")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let authToken = await getAuthToken() {
            urlRequest.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }
        
        let jsonData = try JSONEncoder().encode(request)
        urlRequest.httpBody = jsonData
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }
        
        let wrapper = try JSONDecoder().decode(HealthProfileWrapper.self, from: data)
        return wrapper.healthProfile!
    }
}
