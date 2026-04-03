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

    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        // Request App Tracking Transparency permission.
        // Must be called after the first screen has rendered (iOS 14.5+).
        // NSUserTrackingUsageDescription in Info.plist is required or the app
        // will crash at this call. AppConfig.Features.enableAnalytics gates
        // actual data collection — ATT just requests the OS-level permission.
        if AppConfig.Features.enableAnalytics {
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                ATTrackingManager.requestTrackingAuthorization { status in
                    // status == .authorized  → IDFA available, analytics active
                    // status == .denied      → use anonymous session ID only
                    // status == .restricted  → device-level restriction in place
                    // status == .notDetermined → should not happen here
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
        // Called when a new scene session is being created.
        // Use this method to select a configuration to create the new scene with.
        return UISceneConfiguration(name: "Default Configuration", sessionRole: connectingSceneSession.role)
    }

    func application(_ application: UIApplication, didDiscardSceneSessions sceneSessions: Set<UISceneSession>) {
        // Called when the user discards a scene session.
        // If any sessions were discarded while the application was not running, this will be called shortly after application:didFinishLaunchingWithOptions.
        // Use this method to release any resources that were specific to the discarded scenes, as they will not return.
    }
}