//
//  DoorDashTabBarController.swift
//  MenuOCR
//
//  Main tab bar controller – 3 tabs: Health+, Scan, Account
//

import UIKit

class DoorDashTabBarController: UITabBarController {

    // MARK: - Properties

    private let apiService = ApiService()

    // MARK: - Lifecycle

    override func viewDidLoad() {
        super.viewDidLoad()
        setupAppearance()
        setupViewControllers()
        selectedIndex = 1 // Default to Scan (middle tab)
    }

    // MARK: - Setup

    private func setupAppearance() {
        let appearance = UITabBarAppearance()
        appearance.configureWithOpaqueBackground()
        appearance.backgroundColor = .systemBackground

        // Android: selected = #FA3D2E (DoorDash red)
        let selectedColor = UIColor(red: 0.98, green: 0.239, blue: 0.18, alpha: 1.0) // #FA3D2E

        appearance.stackedLayoutAppearance.selected.iconColor = selectedColor
        appearance.stackedLayoutAppearance.selected.titleTextAttributes = [
            .foregroundColor: selectedColor,
            .font: UIFont.systemFont(ofSize: 11, weight: .semibold)
        ]

        // Android: unselected = #717182 (gray_500)
        let unselectedColor = UIColor(red: 0.443, green: 0.443, blue: 0.51, alpha: 1.0) // #717182
        appearance.stackedLayoutAppearance.normal.iconColor = unselectedColor
        appearance.stackedLayoutAppearance.normal.titleTextAttributes = [
            .foregroundColor: unselectedColor,
            .font: UIFont.systemFont(ofSize: 11, weight: .medium)
        ]

        tabBar.layer.shadowColor = UIColor.black.cgColor
        tabBar.layer.shadowOffset = CGSize(width: 0, height: -1)
        tabBar.layer.shadowOpacity = 0.08
        tabBar.layer.shadowRadius = 4

        tabBar.standardAppearance = appearance
        if #available(iOS 15.0, *) {
            tabBar.scrollEdgeAppearance = appearance
        }
    }

    private func setupViewControllers() {
        let healthVC = createHealthConditionsVC()
        let menuOcrVC = createMenuOcrVC()
        let profileVC = createProfileVC()

        // Android order: Health+ | Scan | Account
        viewControllers = [healthVC, menuOcrVC, profileVC]
    }

    private func createMenuOcrVC() -> UINavigationController {
        let menuOcrVC = MenuOCRViewController()
        menuOcrVC.apiService = apiService

        menuOcrVC.tabBarItem = UITabBarItem(
            title: "Scan",
            image: UIImage(systemName: "camera"),
            selectedImage: UIImage(systemName: "camera.fill")
        )

        let navController = UINavigationController(rootViewController: menuOcrVC)
        navController.navigationBar.prefersLargeTitles = false
        navController.setNavigationBarHidden(true, animated: false)
        return navController
    }

    private func createHealthConditionsVC() -> UINavigationController {
        let healthVC = HealthConditionsViewController()

        healthVC.tabBarItem = UITabBarItem(
            title: "Health+",
            image: UIImage(systemName: "heart.text.square"),
            selectedImage: UIImage(systemName: "heart.text.square.fill")
        )

        let navController = UINavigationController(rootViewController: healthVC)
        navController.navigationBar.prefersLargeTitles = false
        navController.setNavigationBarHidden(true, animated: false)
        return navController
    }

    private func createProfileVC() -> UINavigationController {
        let profileVC = ProfileViewController()

        // Android: tab name is "Account"
        profileVC.tabBarItem = UITabBarItem(
            title: "Account",
            image: UIImage(systemName: "person.circle"),
            selectedImage: UIImage(systemName: "person.circle.fill")
        )

        let navController = UINavigationController(rootViewController: profileVC)
        navController.navigationBar.prefersLargeTitles = false
        navController.setNavigationBarHidden(true, animated: false)
        return navController
    }
}
