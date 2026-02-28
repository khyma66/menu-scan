//
//  LocationService.swift
//  MenuOCR
//
//  Location service for iOS - equivalent to Android LocationService.kt
//

import Foundation
import CoreLocation
import UIKit

// MARK: - Location Models

struct UserLocation {
    let latitude: Double
    let longitude: Double
    let accuracy: Double?
    let timestamp: Date
    
    init(latitude: Double, longitude: Double, accuracy: Double? = nil, timestamp: Date = Date()) {
        self.latitude = latitude
        self.longitude = longitude
        self.accuracy = accuracy
        self.timestamp = timestamp
    }
    
    init(from clLocation: CLLocation) {
        self.latitude = clLocation.coordinate.latitude
        self.longitude = clLocation.coordinate.longitude
        self.accuracy = clLocation.horizontalAccuracy > 0 ? clLocation.horizontalAccuracy : nil
        self.timestamp = clLocation.timestamp
    }
}

// MARK: - Location Service Delegate

protocol LocationServiceDelegate: AnyObject {
    func locationService(_ service: LocationService, didUpdateLocation location: UserLocation)
    func locationService(_ service: LocationService, didFailWithError error: Error)
    func locationServiceDidChangeAuthorization(_ service: LocationService)
}

// MARK: - Location Service

class LocationService: NSObject {
    
    // MARK: - Properties
    
    private let locationManager = CLLocationManager()
    private weak var delegate: LocationServiceDelegate?
    
    private(set) var currentLocation: UserLocation?
    private(set) var isLocationEnabled = false
    
    // MARK: - Initialization
    
    override init() {
        super.init()
        setupLocationManager()
    }
    
    convenience init(delegate: LocationServiceDelegate) {
        self.init()
        self.delegate = delegate
    }
    
    private func setupLocationManager() {
        locationManager.delegate = self
        locationManager.desiredAccuracy = kCLLocationAccuracyBest
        locationManager.distanceFilter = 10 // Update every 10 meters
        locationManager.activityType = .fitness
        locationManager.pausesLocationUpdatesAutomatically = true
    }
    
    // MARK: - Permission Methods
    
    func checkLocationPermission() -> CLAuthorizationStatus {
        return locationManager.authorizationStatus
    }
    
    func hasLocationPermission() -> Bool {
        let status = locationManager.authorizationStatus
        return status == .authorizedWhenInUse || status == .authorizedAlways
    }
    
    func requestLocationPermission() {
        locationManager.requestWhenInUseAuthorization()
    }
    
    // MARK: - Location Methods
    
    func startLocationUpdates() {
        guard hasLocationPermission() else {
            requestLocationPermission()
            return
        }
        
        isLocationEnabled = true
        locationManager.startUpdatingLocation()
    }
    
    func stopLocationUpdates() {
        locationManager.stopUpdatingLocation()
        isLocationEnabled = false
    }
    
    func getCurrentLocation() async throws -> UserLocation {
        // Check permission first
        guard hasLocationPermission() else {
            throw LocationError.permissionDenied
        }
        
        // Return cached location if recent (within 30 seconds)
        if let current = currentLocation,
           Date().timeIntervalSince(current.timestamp) < 30 {
            return current
        }
        
        // Request fresh location
        return try await withCheckedThrowingContinuation { continuation in
            let delegate = LocationContinuationDelegate(continuation: continuation)
            let tempManager = CLLocationManager()
            tempManager.delegate = delegate
            tempManager.desiredAccuracy = kCLLocationAccuracyBest
            tempManager.requestLocation()
            
            // Store reference to prevent deallocation
            objc_setAssociatedObject(self, "tempDelegate", delegate, .OBJC_ASSOCIATION_RETAIN_NONATOMIC)
            objc_setAssociatedObject(self, "tempManager", tempManager, .OBJC_ASSOCIATION_RETAIN_NONATOMIC)
        }
    }
    
    func getLastKnownLocation() -> UserLocation? {
        return currentLocation
    }
    
    // MARK: - Distance Calculation
    
    static func calculateDistance(from: UserLocation, to: UserLocation) -> Double {
        let fromLocation = CLLocation(latitude: from.latitude, longitude: from.longitude)
        let toLocation = CLLocation(latitude: to.latitude, longitude: to.longitude)
        return fromLocation.distance(from: toLocation) // Returns meters
    }
    
    static func metersToMiles(_ meters: Double) -> Double {
        return meters * 0.000621371
    }
    
    static func metersToKilometers(_ meters: Double) -> Double {
        return meters / 1000.0
    }
}

// MARK: - CLLocationManagerDelegate

extension LocationService: CLLocationManagerDelegate {
    
    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.last else { return }
        
        let userLocation = UserLocation(from: location)
        currentLocation = userLocation
        delegate?.locationService(self, didUpdateLocation: userLocation)
    }
    
    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        print("LocationService error: \(error.localizedDescription)")
        delegate?.locationService(self, didFailWithError: error)
    }
    
    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        let status = manager.authorizationStatus
        isLocationEnabled = (status == .authorizedWhenInUse || status == .authorizedAlways)
        delegate?.locationServiceDidChangeAuthorization(self)
    }
}

// MARK: - Location Continuation Delegate (for async/await)

private class LocationContinuationDelegate: NSObject, CLLocationManagerDelegate {
    let continuation: CheckedContinuation<UserLocation, Error>
    var hasResumed = false
    
    init(continuation: CheckedContinuation<UserLocation, Error>) {
        self.continuation = continuation
    }
    
    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard !hasResumed, let location = locations.last else { return }
        hasResumed = true
        continuation.resume(returning: UserLocation(from: location))
    }
    
    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        guard !hasResumed else { return }
        hasResumed = true
        continuation.resume(throwing: error)
    }
}

// MARK: - Location Error

enum LocationError: LocalizedError {
    case permissionDenied
    case locationUnavailable
    case timeout
    
    var errorDescription: String? {
        switch self {
        case .permissionDenied:
            return "Location permission denied. Please enable location access in Settings."
        case .locationUnavailable:
            return "Location is currently unavailable. Please try again."
        case .timeout:
            return "Location request timed out. Please try again."
        }
    }
}

// MARK: - Info.plist Keys Reminder
/*
 Add these keys to Info.plist:
 - NSLocationWhenInUseUsageDescription: "Location access is required to find nearby restaurants."
 - NSLocationAlwaysAndWhenInUseUsageDescription: "Location access is required to find nearby restaurants."
*/
