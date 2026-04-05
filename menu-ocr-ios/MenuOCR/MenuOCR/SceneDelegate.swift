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
        print("[SceneDelegate] scene willConnectTo called")
        guard let windowScene = (scene as? UIWindowScene) else { return }

        // Create the window
        window = UIWindow(windowScene: windowScene)

        // Show splash screen first with breathe-out animation
        let splashVC = SplashViewController()
        splashVC.onAnimationComplete = { [weak self] in
            guard let self = self else { return }
            // Transition to the main tab bar controller
            let tabBarController = DoorDashTabBarController()
            self.window?.rootViewController = tabBarController
            self.window?.makeKeyAndVisible()
        }

        window?.rootViewController = splashVC
        window?.makeKeyAndVisible()
    }

    func sceneDidDisconnect(_ scene: UIScene) {
        // Called as the scene is being released by the system.
    }

    func sceneDidBecomeActive(_ scene: UIScene) {
        // Called when the scene has moved from an inactive state to an active state.
    }

    func sceneWillResignActive(_ scene: UIScene) {
        // Called when the scene will move from an active state to an inactive state.
    }

    func sceneWillEnterForeground(_ scene: UIScene) {
        // Called as the scene transitions from the background to the foreground.
    }

    func sceneDidEnterBackground(_ scene: UIScene) {
        // Called as the scene transitions from the foreground to the background.
    }
}
