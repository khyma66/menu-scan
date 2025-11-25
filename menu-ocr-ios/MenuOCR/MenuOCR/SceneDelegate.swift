//
//  SceneDelegate.swift
//  MenuOCR
//
//  Created by MenuOCR on 2025-01-07.
//

import UIKit

class SceneDelegate: UIResponder, UIWindowSceneDelegate {

    var window: UIWindow?

    func scene(_ scene: UIScene, willConnectTo session: UISceneSession, options connectionOptions: UIScene.ConnectionOptions) {
        // Use this method to optionally configure and attach the UIWindow `window` to the provided UIWindowScene `scene`.
        // If using a storyboard, the `window` property will automatically be initialized and attached to the scene.
        // This delegate does not imply the connecting scene or session are new (see `application:configurationForConnectingSceneSession` instead).
        guard let windowScene = (scene as? UIWindowScene) else { return }

        // Create the window
        window = UIWindow(windowScene: windowScene)

        // Create tab bar controller
        let tabBarController = UITabBarController()
        tabBarController.tabBar.tintColor = UIColor(red: 1.0, green: 0.3, blue: 0.22, alpha: 1.0) // DoorDash orange

        // Create view controllers for each tab
        let restaurantDiscoveryVC = RestaurantDiscoveryViewController()
        restaurantDiscoveryVC.tabBarItem = UITabBarItem(title: "🍽️ Discovery", image: UIImage(systemName: "fork.knife"), tag: 0)

        let menuOCVC = MenuOCRViewController()
        menuOCVC.tabBarItem = UITabBarItem(title: "📱 OCR", image: UIImage(systemName: "camera"), tag: 1)

        let googleDriveVC = GoogleDriveViewController()
        googleDriveVC.tabBarItem = UITabBarItem(title: "☁️ Drive", image: UIImage(systemName: "icloud"), tag: 2)

        // Set view controllers
        tabBarController.viewControllers = [restaurantDiscoveryVC, menuOCVC, googleDriveVC]

        // Set root view controller
        window?.rootViewController = tabBarController
        window?.makeKeyAndVisible()
    }

    func sceneDidDisconnect(_ scene: UIScene) {
        // Called as the scene is being released by the system.
        // This occurs shortly after the scene enters the background, or when its session is discarded.
        // Release any resources associated with this scene that can be re-created the next time the scene connects.
        // The scene may re-connect later, as its session was not necessarily discarded (see `application:configurationForConnectingSceneSession` instead).
    }

    func sceneDidBecomeActive(_ scene: UIScene) {
        // Called when the scene has moved from an inactive state to an active state.
        // Use this method to restart any tasks that were paused (or not yet started) when the scene was inactive.
    }

    func sceneWillResignActive(_ scene: UIScene) {
        // Called when the scene will move from an active state to an inactive state.
        // This may occur due to temporary interruptions (ex. an incoming phone call).
    }

    func sceneWillEnterForeground(_ scene: UIScene) {
        // Called as the scene transitions from the background to the foreground.
        // Use this method to undo the changes made on entering the background.
    }

    func sceneDidEnterBackground(_ scene: UIScene) {
        // Called as the scene transitions from the foreground to the background.
        // Use this method to save data, release shared resources, and store enough scene-specific state information
        // to restore the scene back to its current state.
    }
}