//
//  ScanLimitManager.swift
//  MenuOCR
//
//  Tracks per-device scan usage. Free tier: 3 scans total.
//  After 3, user must upgrade to Pro or Max plan.
//

import Foundation

final class ScanLimitManager {

    static let shared = ScanLimitManager()

    // MARK: - Constants

    static let freeLimit = 3

    // MARK: - UserDefaults Keys

    private let scanCountKey   = "com.menuocr.totalScanCount"
    private let isPremiumKey   = "com.menuocr.isPremium"
    private let planNameKey    = "com.menuocr.planName"

    private let defaults = UserDefaults.standard

    private init() {}

    // MARK: - Scan Count

    /// Total scans this device has performed
    var scanCount: Int {
        get { defaults.integer(forKey: scanCountKey) }
        set { defaults.set(newValue, forKey: scanCountKey) }
    }

    /// Remaining free scans
    var remainingFreeScans: Int {
        max(ScanLimitManager.freeLimit - scanCount, 0)
    }

    /// Whether the user has exceeded the free limit
    var isLimitReached: Bool {
        !isPremium && scanCount >= ScanLimitManager.freeLimit
    }

    /// Record one scan
    func recordScan() {
        scanCount += 1
    }

    // MARK: - Premium Status

    /// Whether the device has an active Pro/Max subscription
    var isPremium: Bool {
        get { defaults.bool(forKey: isPremiumKey) }
        set { defaults.set(newValue, forKey: isPremiumKey) }
    }

    /// Current plan name ("free", "pro", "max")
    var planName: String {
        get { defaults.string(forKey: planNameKey) ?? "free" }
        set { defaults.set(newValue, forKey: planNameKey) }
    }

    /// Upgrade the user to a paid plan
    func upgradeTo(plan: String) {
        planName = plan
        isPremium = true
    }

    /// Downgrade back to free (e.g. subscription expired)
    func downgrade() {
        planName = "free"
        isPremium = false
    }
}
