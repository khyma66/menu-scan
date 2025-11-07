//
//  ViewController.swift
//  MenuOCR
//
//  Created by MenuOCR on 2025-01-07.
//

import UIKit

class ViewController: UIViewController {

    private let authViewModel = AuthViewModel()

    override func viewDidLoad() {
        super.viewDidLoad()

        // Check if user is already authenticated
        if case .authenticated = authViewModel.authState {
            // User is logged in, show main screen
            showMainScreen()
        } else {
            // User needs to log in
            showLoginScreen()
        }
    }

    private func showLoginScreen() {
        let loginVC = LoginViewController()
        let navigationController = UINavigationController(rootViewController: loginVC)
        navigationController.modalPresentationStyle = .fullScreen
        present(navigationController, animated: false)
    }

    private func showMainScreen() {
        let mainVC = MainViewController()
        let navigationController = UINavigationController(rootViewController: mainVC)
        navigationController.modalPresentationStyle = .fullScreen
        present(navigationController, animated: false)
    }
}