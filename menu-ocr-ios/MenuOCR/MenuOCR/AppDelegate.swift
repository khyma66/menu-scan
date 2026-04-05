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
        print("[AppDelegate] didFinishLaunchingWithOptions")

        // Set up window directly — no scene delegate needed for single-window app
        let window = UIWindow(frame: UIScreen.main.bounds)
        let splashVC = SplashViewController()
        splashVC.onAnimationComplete = { [weak self] in
            let tabBarController = DoorDashTabBarController()
            self?.window?.rootViewController = tabBarController
        }
        window.rootViewController = splashVC
        window.makeKeyAndVisible()
        self.window = window

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
}
