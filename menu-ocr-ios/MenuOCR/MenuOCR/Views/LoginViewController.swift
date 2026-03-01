//
//  LoginViewController.swift
//  MenuOCR
//
//  Created by MenuOCR on 2025-01-07.
//

import UIKit
import Combine
import AuthenticationServices

class LoginViewController: UIViewController {

    private let authViewModel = AuthViewModel()
    private var cancellables = Set<AnyCancellable>()

    private let scrollView: UIScrollView = {
        let scrollView = UIScrollView()
        scrollView.keyboardDismissMode = .interactive
        return scrollView
    }()
    
    private let contentView: UIView = {
        let view = UIView()
        return view
    }()
    
    private let titleLabel: UILabel = {
        let label = UILabel()
        label.text = "Welcome to Fooder"
        label.font = .systemFont(ofSize: 24, weight: .bold)
        label.textAlignment = .center
        label.textColor = UIColor(red: 0.15, green: 0.15, blue: 0.15, alpha: 1.0) // Off-black per UX playbook
        return label
    }()
    
    private let subtitleLabel: UILabel = {
        let label = UILabel()
        label.text = "Sign in to continue"
        label.font = .systemFont(ofSize: 16, weight: .regular)
        label.textColor = .secondaryLabel
        label.textAlignment = .center
        return label
    }()

    private let emailTextField: UITextField = {
        let textField = UITextField()
        textField.placeholder = "Email"
        textField.borderStyle = .roundedRect
        textField.keyboardType = .emailAddress
        textField.autocapitalizationType = .none
        textField.autocorrectionType = .no
        textField.returnKeyType = .next
        return textField
    }()

    private let passwordTextField: UITextField = {
        let textField = UITextField()
        textField.placeholder = "Password"
        textField.borderStyle = .roundedRect
        textField.isSecureTextEntry = true
        textField.returnKeyType = .done
        return textField
    }()

    private let signInButton: UIButton = {
        let button = UIButton(type: .system)
        button.setTitle("Sign In", for: .normal)
        button.backgroundColor = UIColor(red: 0.98, green: 0.24, blue: 0.18, alpha: 1.0)
        button.setTitleColor(.white, for: .normal)
        button.layer.cornerRadius = 12
        button.titleLabel?.font = .systemFont(ofSize: 16, weight: .semibold)
        return button
    }()

    private let signUpButton: UIButton = {
        let button = UIButton(type: .system)
        button.setTitle("Create Account", for: .normal)
        button.backgroundColor = UIColor(red: 0.98, green: 0.24, blue: 0.18, alpha: 0.12)
        button.setTitleColor(UIColor(red: 0.98, green: 0.24, blue: 0.18, alpha: 1.0), for: .normal)
        button.layer.cornerRadius = 12
        button.titleLabel?.font = .systemFont(ofSize: 16, weight: .semibold)
        return button
    }()
    
    private let forgotPasswordButton: UIButton = {
        let button = UIButton(type: .system)
        button.setTitle("Forgot Password?", for: .normal)
        button.setTitleColor(.systemGray, for: .normal)
        button.titleLabel?.font = .systemFont(ofSize: 14, weight: .regular)
        return button
    }()

    // Divider
    private let dividerView: UIView = {
        let view = UIView()
        return view
    }()
    
    private let dividerLabel: UILabel = {
        let label = UILabel()
        label.text = "or continue with"
        label.font = .systemFont(ofSize: 14, weight: .regular)
        label.textColor = .secondaryLabel
        label.textAlignment = .center
        return label
    }()
    
    private let leftDividerLine: UIView = {
        let view = UIView()
        view.backgroundColor = .separator
        return view
    }()
    
    private let rightDividerLine: UIView = {
        let view = UIView()
        view.backgroundColor = .separator
        return view
    }()

    // Apple Sign In Button (custom styled)
    private let appleSignInButton: UIButton = {
        let button = UIButton(type: .system)
        button.setTitle("  Sign in with Apple", for: .normal)
        button.backgroundColor = .black
        button.setTitleColor(.white, for: .normal)
        button.layer.cornerRadius = 12
        button.titleLabel?.font = .systemFont(ofSize: 16, weight: .semibold)
        // Add Apple logo
        let config = UIImage.SymbolConfiguration(pointSize: 20, weight: .medium)
        let appleLogo = UIImage(systemName: "apple.logo", withConfiguration: config)
        button.setImage(appleLogo, for: .normal)
        button.tintColor = .white
        return button
    }()

    private let googleSignInButton: UIButton = {
        let button = UIButton(type: .system)
        button.setTitle("  Sign in with Google", for: .normal)
        button.backgroundColor = .white
        button.setTitleColor(UIColor(red: 0.13, green: 0.13, blue: 0.13, alpha: 1.0), for: .normal)
        button.layer.cornerRadius = 12
        button.layer.borderWidth = 1
        button.layer.borderColor = UIColor.separator.cgColor
        button.titleLabel?.font = .systemFont(ofSize: 16, weight: .semibold)
        return button
    }()

    private let activityIndicator: UIActivityIndicatorView = {
        let indicator = UIActivityIndicatorView(style: .medium)
        indicator.hidesWhenStopped = true
        return indicator
    }()
    
    private let skipButton: UIButton = {
        let button = UIButton(type: .system)
        button.setTitle("Skip for now", for: .normal)
        button.setTitleColor(.systemGray, for: .normal)
        button.titleLabel?.font = .systemFont(ofSize: 14, weight: .regular)
        return button
    }()

    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
        setupBindings()
        setupKeyboardHandling()
    }

    private func setupUI() {
        view.backgroundColor = .systemBackground
        
        // Add scroll view
        view.addSubview(scrollView)
        scrollView.addSubview(contentView)
        scrollView.translatesAutoresizingMaskIntoConstraints = false
        contentView.translatesAutoresizingMaskIntoConstraints = false
        
        // Add all components to content view
        [titleLabel, subtitleLabel, emailTextField, passwordTextField, 
         signInButton, signUpButton, forgotPasswordButton,
         dividerView, appleSignInButton, googleSignInButton, 
         activityIndicator, skipButton].forEach {
            $0.translatesAutoresizingMaskIntoConstraints = false
            contentView.addSubview($0)
        }
        
        // Setup divider view
        dividerView.addSubview(leftDividerLine)
        dividerView.addSubview(dividerLabel)
        dividerView.addSubview(rightDividerLine)
        leftDividerLine.translatesAutoresizingMaskIntoConstraints = false
        dividerLabel.translatesAutoresizingMaskIntoConstraints = false
        rightDividerLine.translatesAutoresizingMaskIntoConstraints = false
        
        setupConstraints()
        setupButtonActions()
    }
    
    private func setupConstraints() {
        let padding: CGFloat = 24
        let buttonHeight: CGFloat = 50
        
        NSLayoutConstraint.activate([
            // Scroll view
            scrollView.topAnchor.constraint(equalTo: view.topAnchor),
            scrollView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            scrollView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            scrollView.bottomAnchor.constraint(equalTo: view.bottomAnchor),
            
            // Content view
            contentView.topAnchor.constraint(equalTo: scrollView.topAnchor),
            contentView.leadingAnchor.constraint(equalTo: scrollView.leadingAnchor),
            contentView.trailingAnchor.constraint(equalTo: scrollView.trailingAnchor),
            contentView.bottomAnchor.constraint(equalTo: scrollView.bottomAnchor),
            contentView.widthAnchor.constraint(equalTo: scrollView.widthAnchor),
            
            // Title
            titleLabel.topAnchor.constraint(equalTo: contentView.topAnchor, constant: 60),
            titleLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: padding),
            titleLabel.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -padding),
            
            // Subtitle
            subtitleLabel.topAnchor.constraint(equalTo: titleLabel.bottomAnchor, constant: 8),
            subtitleLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: padding),
            subtitleLabel.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -padding),
            
            // Email
            emailTextField.topAnchor.constraint(equalTo: subtitleLabel.bottomAnchor, constant: 40),
            emailTextField.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: padding),
            emailTextField.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -padding),
            emailTextField.heightAnchor.constraint(equalToConstant: 50),
            
            // Password
            passwordTextField.topAnchor.constraint(equalTo: emailTextField.bottomAnchor, constant: 16),
            passwordTextField.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: padding),
            passwordTextField.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -padding),
            passwordTextField.heightAnchor.constraint(equalToConstant: 50),
            
            // Sign In Button
            signInButton.topAnchor.constraint(equalTo: passwordTextField.bottomAnchor, constant: 24),
            signInButton.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: padding),
            signInButton.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -padding),
            signInButton.heightAnchor.constraint(equalToConstant: buttonHeight),
            
            // Sign Up Button
            signUpButton.topAnchor.constraint(equalTo: signInButton.bottomAnchor, constant: 12),
            signUpButton.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: padding),
            signUpButton.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -padding),
            signUpButton.heightAnchor.constraint(equalToConstant: buttonHeight),
            
            // Forgot Password
            forgotPasswordButton.topAnchor.constraint(equalTo: signUpButton.bottomAnchor, constant: 16),
            forgotPasswordButton.centerXAnchor.constraint(equalTo: contentView.centerXAnchor),
            
            // Divider
            dividerView.topAnchor.constraint(equalTo: forgotPasswordButton.bottomAnchor, constant: 24),
            dividerView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: padding),
            dividerView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -padding),
            dividerView.heightAnchor.constraint(equalToConstant: 20),
            
            leftDividerLine.centerYAnchor.constraint(equalTo: dividerView.centerYAnchor),
            leftDividerLine.leadingAnchor.constraint(equalTo: dividerView.leadingAnchor),
            leftDividerLine.trailingAnchor.constraint(equalTo: dividerLabel.leadingAnchor, constant: -8),
            leftDividerLine.heightAnchor.constraint(equalToConstant: 1),
            
            dividerLabel.centerYAnchor.constraint(equalTo: dividerView.centerYAnchor),
            dividerLabel.centerXAnchor.constraint(equalTo: dividerView.centerXAnchor),
            
            rightDividerLine.centerYAnchor.constraint(equalTo: dividerView.centerYAnchor),
            rightDividerLine.leadingAnchor.constraint(equalTo: dividerLabel.trailingAnchor, constant: 8),
            rightDividerLine.trailingAnchor.constraint(equalTo: dividerView.trailingAnchor),
            rightDividerLine.heightAnchor.constraint(equalToConstant: 1),
            
            // Apple Sign In Button
            appleSignInButton.topAnchor.constraint(equalTo: dividerView.bottomAnchor, constant: 24),
            appleSignInButton.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: padding),
            appleSignInButton.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -padding),
            appleSignInButton.heightAnchor.constraint(equalToConstant: buttonHeight),
            
            // Google Sign In Button
            googleSignInButton.topAnchor.constraint(equalTo: appleSignInButton.bottomAnchor, constant: 12),
            googleSignInButton.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: padding),
            googleSignInButton.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -padding),
            googleSignInButton.heightAnchor.constraint(equalToConstant: buttonHeight),
            
            // Skip Button
            skipButton.topAnchor.constraint(equalTo: googleSignInButton.bottomAnchor, constant: 24),
            skipButton.centerXAnchor.constraint(equalTo: contentView.centerXAnchor),
            
            // Activity Indicator
            activityIndicator.centerXAnchor.constraint(equalTo: contentView.centerXAnchor),
            activityIndicator.topAnchor.constraint(equalTo: skipButton.bottomAnchor, constant: 20),
            
            // Content view bottom
            contentView.bottomAnchor.constraint(equalTo: activityIndicator.bottomAnchor, constant: 40)
        ])
    }
    
    private func setupButtonActions() {
        signInButton.addTarget(self, action: #selector(signInTapped), for: .touchUpInside)
        signUpButton.addTarget(self, action: #selector(signUpTapped), for: .touchUpInside)
        forgotPasswordButton.addTarget(self, action: #selector(forgotPasswordTapped), for: .touchUpInside)
        googleSignInButton.addTarget(self, action: #selector(googleSignInTapped), for: .touchUpInside)
        appleSignInButton.addTarget(self, action: #selector(appleSignInTapped), for: .touchUpInside)
        skipButton.addTarget(self, action: #selector(skipTapped), for: .touchUpInside)
        
        // Text field delegates
        emailTextField.delegate = self
        passwordTextField.delegate = self
    }
    
    private func setupKeyboardHandling() {
        // Add tap gesture to dismiss keyboard
        let tapGesture = UITapGestureRecognizer(target: self, action: #selector(dismissKeyboard))
        tapGesture.cancelsTouchesInView = false
        view.addGestureRecognizer(tapGesture)
        
        // Observe keyboard notifications
        NotificationCenter.default.addObserver(self, selector: #selector(keyboardWillShow), name: UIResponder.keyboardWillShowNotification, object: nil)
        NotificationCenter.default.addObserver(self, selector: #selector(keyboardWillHide), name: UIResponder.keyboardWillHideNotification, object: nil)
    }
    
    @objc private func dismissKeyboard() {
        view.endEditing(true)
    }
    
    @objc private func keyboardWillShow(notification: NSNotification) {
        guard let keyboardSize = (notification.userInfo?[UIResponder.keyboardFrameEndUserInfoKey] as? NSValue)?.cgRectValue else { return }
        scrollView.contentInset = UIEdgeInsets(top: 0, left: 0, bottom: keyboardSize.height + 20, right: 0)
        scrollView.scrollIndicatorInsets = scrollView.contentInset
    }
    
    @objc private func keyboardWillHide(notification: NSNotification) {
        scrollView.contentInset = .zero
        scrollView.scrollIndicatorInsets = .zero
    }

    private func setupBindings() {
        authViewModel.$authState
            .receive(on: DispatchQueue.main)
            .sink { [weak self] state in
                self?.handleAuthState(state)
            }
            .store(in: &cancellables)
    }

    private func handleAuthState(_ state: AuthState) {
        switch state {
        case .loading:
            activityIndicator.startAnimating()
            setButtonsEnabled(false)
        case .authenticated:
            activityIndicator.stopAnimating()
            navigateToMain()
        case .error(let message):
            activityIndicator.stopAnimating()
            setButtonsEnabled(true)
            showError(message)
        case .passwordResetSent:
            activityIndicator.stopAnimating()
            setButtonsEnabled(true)
            showMessage("Password reset email sent")
        default:
            activityIndicator.stopAnimating()
            setButtonsEnabled(true)
        }
    }

    private func setButtonsEnabled(_ enabled: Bool) {
        signInButton.isEnabled = enabled
        signUpButton.isEnabled = enabled
        googleSignInButton.isEnabled = enabled
        appleSignInButton.isEnabled = enabled
        skipButton.isEnabled = enabled
    }

    private func navigateToMain() {
        let mainVC = MainViewController()
        navigationController?.setViewControllers([mainVC], animated: true)
    }

    private func showError(_ message: String) {
        let alert = UIAlertController(title: "Error", message: message, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "OK", style: .default))
        present(alert, animated: true)
    }

    private func showMessage(_ message: String) {
        let alert = UIAlertController(title: "Success", message: message, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "OK", style: .default))
        present(alert, animated: true)
    }

    @objc private func signInTapped() {
        guard let email = emailTextField.text, !email.isEmpty,
              let password = passwordTextField.text, !password.isEmpty else {
            showError("Please fill in all fields")
            return
        }
        authViewModel.signInWithEmail(email: email, password: password)
    }

    @objc private func signUpTapped() {
        guard let email = emailTextField.text, !email.isEmpty,
              let password = passwordTextField.text, !password.isEmpty else {
            showError("Please fill in all fields")
            return
        }
        authViewModel.signUpWithEmail(email: email, password: password)
    }
    
    @objc private func forgotPasswordTapped() {
        let alert = UIAlertController(title: "Reset Password", message: "Enter your email address", preferredStyle: .alert)
        alert.addTextField { textField in
            textField.placeholder = "Email"
            textField.keyboardType = .emailAddress
            textField.text = self.emailTextField.text
        }
        alert.addAction(UIAlertAction(title: "Cancel", style: .cancel))
        alert.addAction(UIAlertAction(title: "Send", style: .default) { [weak self] _ in
            guard let email = alert.textFields?.first?.text, !email.isEmpty else {
                self?.showError("Please enter an email address")
                return
            }
            self?.authViewModel.resetPassword(email: email)
        })
        present(alert, animated: true)
    }

    @objc private func appleSignInTapped() {
        // Use authViewModel which properly creates a Supabase session
        authViewModel.signInWithApple()
    }
    
    @objc private func googleSignInTapped() {
        // Google Sign In would require GoogleSignIn SDK
        // For now, show a message that it requires additional setup
        showMessage("Google Sign In requires GoogleSignIn SDK setup. Please use email/password or Apple Sign In for now.")
    }
    
    @objc private func skipTapped() {
        navigateToMain()
    }
}

// MARK: - UITextFieldDelegate

extension LoginViewController: UITextFieldDelegate {
    func textFieldShouldReturn(_ textField: UITextField) -> Bool {
        if textField == emailTextField {
            passwordTextField.becomeFirstResponder()
        } else if textField == passwordTextField {
            signInTapped()
        }
        return true
    }
}

// Apple Sign In is now handled by authViewModel.signInWithApple()
// which properly creates a Supabase session via SupabaseService