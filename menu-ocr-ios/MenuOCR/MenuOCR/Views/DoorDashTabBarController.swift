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
        // Tab bar appearance
        let appearance = UITabBarAppearance()
        appearance.configureWithOpaqueBackground()
        appearance.backgroundColor = .systemBackground
        
        // Selected item color (DoorDash orange)
        appearance.stackedLayoutAppearance.selected.iconColor = UIColor(red: 1.0, green: 0.3, blue: 0.22, alpha: 1.0)
        appearance.stackedLayoutAppearance.selected.titleTextAttributes = [
            .foregroundColor: UIColor(red: 1.0, green: 0.3, blue: 0.22, alpha: 1.0)
        ]
        
        // Normal item color
        appearance.stackedLayoutAppearance.normal.iconColor = .systemGray
        appearance.stackedLayoutAppearance.normal.titleTextAttributes = [
            .foregroundColor: UIColor.systemGray
        ]
        
        tabBar.standardAppearance = appearance
        if #available(iOS 15.0, *) {
            tabBar.scrollEdgeAppearance = appearance
        }
        
        // Navigation bar appearance
        let navAppearance = UINavigationBarAppearance()
        navAppearance.configureWithOpaqueBackground()
        navAppearance.backgroundColor = UIColor(red: 1.0, green: 0.3, blue: 0.22, alpha: 1.0)
        navAppearance.titleTextAttributes = [.foregroundColor: UIColor.white]
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
            title: "Nearby",
            image: UIImage(systemName: "fork.knife"),
            selectedImage: UIImage(systemName: "fork.knife.fill")
        )
        
        let navController = UINavigationController(rootViewController: restaurantVC)
        navController.navigationBar.prefersLargeTitles = true
        return navController
    }
    
    private func createMenuOcrVC() -> UINavigationController {
        let menuOcrVC = MenuOCRViewController()
        menuOcrVC.apiService = apiService
        
        menuOcrVC.tabBarItem = UITabBarItem(
            title: "Menu OCR",
            image: UIImage(systemName: "camera"),
            selectedImage: UIImage(systemName: "camera.fill")
        )
        
        let navController = UINavigationController(rootViewController: menuOcrVC)
        navController.navigationBar.prefersLargeTitles = true
        return navController
    }
    
    private func createHealthConditionsVC() -> UINavigationController {
        let healthVC = HealthConditionsViewController()
        
        healthVC.tabBarItem = UITabBarItem(
            title: "Health",
            image: UIImage(systemName: "heart.text.square"),
            selectedImage: UIImage(systemName: "heart.text.square.fill")
        )
        
        let navController = UINavigationController(rootViewController: healthVC)
        navController.navigationBar.prefersLargeTitles = true
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
