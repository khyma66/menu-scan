//
//  DoorDashTabBarController.swift
//  MenuOCR
//
//  Main tab bar controller – 3 tabs: Scan, Health+, Profile
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
    }

    // MARK: - Setup

    private func setupAppearance() {
        let appearance = UITabBarAppearance()
        appearance.configureWithOpaqueBackground()
        appearance.backgroundColor = .systemBackground

        let primaryColor = UIColor(red: 0.486, green: 0.227, blue: 0.929, alpha: 1.0)

        appearance.stackedLayoutAppearance.selected.iconColor = primaryColor
        appearance.stackedLayoutAppearance.selected.titleTextAttributes = [
            .foregroundColor: primaryColor,
            .font: UIFont.systemFont(ofSize: 11, weight: .semibold)
        ]

        let offBlackGray = UIColor(red: 0.45, green: 0.45, blue: 0.45, alpha: 1.0)
        appearance.stackedLayoutAppearance.normal.iconColor = offBlackGray
        appearance.stackedLayoutAppearance.normal.titleTextAttributes = [
            .foregroundColor: offBlackGray,
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

        let navAppearance = UINavigationBarAppearance()
        navAppearance.configureWithOpaqueBackground()
        navAppearance.backgroundColor = UIColor(red: 0.486, green: 0.227, blue: 0.929, alpha: 1.0)
        navAppearance.titleTextAttributes = [
            .foregroundColor: UIColor.white,
            .font: UIFont.systemFont(ofSize: 18, weight: .semibold)
        ]
        navAppearance.largeTitleTextAttributes = [.foregroundColor: UIColor.white]

        UINavigationBar.appearance().standardAppearance = navAppearance
        UINavigationBar.appearance().scrollEdgeAppearance = navAppearance
    }

    private func setupViewControllers() {
        let menuOcrVC = createMenuOcrVC()
        let healthVC = createHealthConditionsVC()
        let profileVC = createProfileVC()

        viewControllers = [menuOcrVC, healthVC, profileVC]
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

        profileVC.tabBarItem = UITabBarItem(
            title: "Profile",
            image: UIImage(systemName: "person.circle"),
            selectedImage: UIImage(systemName: "person.circle.fill")
        )

        let navController = UINavigationController(rootViewController: profileVC)
        navController.navigationBar.prefersLargeTitles = false
        navController.setNavigationBarHidden(true, animated: false)
        return navController
    }
}
