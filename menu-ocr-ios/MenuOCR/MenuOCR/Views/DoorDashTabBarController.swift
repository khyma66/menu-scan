//
//  DoorDashTabBarController.swift
//  MenuOCR
//
//  Main tab bar controller with DoorDash-like UI
//  Equivalent to Android DoorDashMainActivity.kt
//

import UIKit

class DoorDashTabBarController: UITabBarController {
    
    // MARK: - Properties
    
    private let locationService = LocationService()
    private let overpassService = OverpassApiService()
    private let apiService = ApiService()
    
    // MARK: - Lifecycle
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupAppearance()
        setupViewControllers()
        setupNavigationBar()
    }
    
    // MARK: - Setup
    
    private func setupAppearance() {
        // Tab bar appearance - UX playbook: clean, minimal, proper contrast
        let appearance = UITabBarAppearance()
        appearance.configureWithOpaqueBackground()
        appearance.backgroundColor = .systemBackground
        
        // Primary color (brand violet)
        let primaryColor = UIColor(red: 0.486, green: 0.227, blue: 0.929, alpha: 1.0) // #7C3AED
        
        // Selected item color
        appearance.stackedLayoutAppearance.selected.iconColor = primaryColor
        appearance.stackedLayoutAppearance.selected.titleTextAttributes = [
            .foregroundColor: primaryColor,
            .font: UIFont.systemFont(ofSize: 11, weight: .semibold)
        ]
        
        // Normal item color - off-black per UX playbook (avoid pure black)
        let offBlackGray = UIColor(red: 0.45, green: 0.45, blue: 0.45, alpha: 1.0)
        appearance.stackedLayoutAppearance.normal.iconColor = offBlackGray
        appearance.stackedLayoutAppearance.normal.titleTextAttributes = [
            .foregroundColor: offBlackGray,
            .font: UIFont.systemFont(ofSize: 11, weight: .medium)
        ]
        
        // Add subtle shadow to tab bar for depth
        tabBar.layer.shadowColor = UIColor.black.cgColor
        tabBar.layer.shadowOffset = CGSize(width: 0, height: -1)
        tabBar.layer.shadowOpacity = 0.08
        tabBar.layer.shadowRadius = 4
        
        tabBar.standardAppearance = appearance
        if #available(iOS 15.0, *) {
            tabBar.scrollEdgeAppearance = appearance
        }
        
        // Navigation bar appearance - clean centered title
        let navAppearance = UINavigationBarAppearance()
        navAppearance.configureWithOpaqueBackground()
        navAppearance.backgroundColor = UIColor(red: 0.486, green: 0.227, blue: 0.929, alpha: 1.0) // violet
        navAppearance.titleTextAttributes = [
            .foregroundColor: UIColor.white,
            .font: UIFont.systemFont(ofSize: 18, weight: .semibold)
        ]
        navAppearance.largeTitleTextAttributes = [.foregroundColor: UIColor.white]
        
        UINavigationBar.appearance().standardAppearance = navAppearance
        UINavigationBar.appearance().scrollEdgeAppearance = navAppearance
    }
    
    private func setupViewControllers() {
        // Create view controllers for each tab
        let restaurantVC = createRestaurantDiscoveryVC()
        let menuOcrVC = createMenuOcrVC()
        let healthVC = createHealthConditionsVC()
        
        viewControllers = [restaurantVC, menuOcrVC, healthVC]
    }
    
    private func createRestaurantDiscoveryVC() -> UINavigationController {
        let restaurantVC = RestaurantDiscoveryViewController()
        restaurantVC.locationService = locationService
        restaurantVC.overpassService = overpassService
        
        restaurantVC.tabBarItem = UITabBarItem(
            title: "Discover",
            image: UIImage(systemName: "fork.knife"),
            selectedImage: UIImage(systemName: "fork.knife.fill")
        )
        
        let navController = UINavigationController(rootViewController: restaurantVC)
        navController.navigationBar.prefersLargeTitles = false
        navController.setNavigationBarHidden(true, animated: false)
        return navController
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
    
    private func setupNavigationBar() {
        // Add profile button to navigation bar
        let profileButton = UIBarButtonItem(
            image: UIImage(systemName: "person.circle.fill"),
            style: .plain,
            target: self,
            action: #selector(profileTapped)
        )
        profileButton.tintColor = .white
        
        // Apply to all navigation controllers
        viewControllers?.forEach { vc in
            if let navVC = vc as? UINavigationController {
                navVC.viewControllers.first?.navigationItem.rightBarButtonItem = profileButton
            }
        }
    }
    
    // MARK: - Actions
    
    @objc private func profileTapped() {
        let profileVC = ProfileViewController()
        profileVC.modalPresentationStyle = .formSheet
        present(profileVC, animated: true)
    }
}

// MARK: - Restaurant Discovery View Controller (Updated)

extension RestaurantDiscoveryViewController {
    
    // Location and services are injected
    var locationService: LocationService? {
        get { objc_getAssociatedObject(self, &AssociatedKeys.locationService) as? LocationService }
        set { objc_setAssociatedObject(self, &AssociatedKeys.locationService, newValue, .OBJC_ASSOCIATION_RETAIN_NONATOMIC) }
    }
    
    var overpassService: OverpassApiService? {
        get { objc_getAssociatedObject(self, &AssociatedKeys.overpassService) as? OverpassApiService }
        set { objc_setAssociatedObject(self, &AssociatedKeys.overpassService, newValue, .OBJC_ASSOCIATION_RETAIN_NONATOMIC) }
    }
}

private struct AssociatedKeys {
    static var locationService = "locationService"
    static var overpassService = "overpassService"
}
