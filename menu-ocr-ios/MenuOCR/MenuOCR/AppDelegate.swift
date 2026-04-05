//
//  AppDelegate.swift
//  MenuOCR
//
//  Created by MenuOCR on 2025-01-07.
//

import UIKit
import AppTrackingTransparency
import AdSupport

@main
class AppDelegate: UIResponder, UIApplicationDelegate {
    var window: UIWindow?

    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {

        // Fallback window setup — if scene delegate is not called (e.g. iOS
        // cannot resolve the scene manifest), this guarantees the app shows UI.
        if #available(iOS 13, *) {
            // Scene-based apps should set up window in SceneDelegate.
            // But if something goes wrong, we set up here after a short delay.
            DispatchQueue.main.async {
                if self.window?.rootViewController == nil {
                    print("[AppDelegate] SceneDelegate did not set rootViewController — using fallback")
                    let window = UIWindow(frame: UIScreen.main.bounds)
                    let splashVC = SplashViewController()
                    splashVC.onAnimationComplete = {
                        let tabBarController = DoorDashTabBarController()
                        window.rootViewController = tabBarController
                        window.makeKeyAndVisible()
                    }
                    window.rootViewController = splashVC
                    window.makeKeyAndVisible()
                    self.window = window
                }
            }
        }

        if AppConfig.Features.enableAnalytics {
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                ATTrackingManager.requestTrackingAuthorization { status in
                    #if DEBUG
                    print("[ATT] Authorization status: \(status.rawValue)")
                    #endif
                }
            }
        }
        return true
    }

    // MARK: UISceneSession Lifecycle

    func application(_ application: UIApplication, configurationForConnecting connectingSceneSession: UISceneSession, options: UIScene.ConnectionOptions) -> UISceneConfiguration {
        print("[AppDelegate] configurationForConnecting called")
        let config = UISceneConfiguration(name: "Default Configuration", sessionRole: connectingSceneSession.role)
        config.delegateClass = SceneDelegate.self
        return config
    }

    func application(_ application: UIApplication, didDiscardSceneSessions sceneSessions: Set<UISceneSession>) {
        // Called when the user discards a scene session.
        // If any sessions were discarded while the application was not running, this will be called shortly after application:didFinishLaunchingWithOptions.
        // Use this method to release any resources that were specific to the discarded scenes, as they will not return.
    }
}
