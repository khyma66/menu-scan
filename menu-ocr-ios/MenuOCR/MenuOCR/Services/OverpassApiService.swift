//
//  OverpassApiService.swift
//  MenuOCR
//
//  Service to query OpenStreetMap Overpass API for nearby restaurants
//  Equivalent to Android OverpassApiService.kt
//

import Foundation
import CoreLocation

// MARK: - Restaurant Model

struct OverpassRestaurant: Codable, Identifiable {
    let id: Int64
    let name: String
    let latitude: Double
    let longitude: Double
    let cuisine: String
    let address: String?
    let phone: String?
    let website: String?
    let openingHours: String?
    let delivery: Bool
    let takeaway: Bool
    let wheelchair: Bool
    let outdoorSeating: Bool
    let wifi: Bool
    let tags: [String]
    
    enum CodingKeys: String, CodingKey {
        case id, name, latitude, longitude, cuisine, address, phone, website
        case openingHours = "opening_hours"
        case delivery, takeaway, wheelchair
        case outdoorSeating = "outdoor_seating"
        case wifi, tags
    }
    
    // Calculate distance from a given location
    func distanceFrom(_ latitude: Double, _ longitude: Double) -> Double {
        let fromLocation = CLLocation(latitude: latitude, longitude: longitude)
        let toLocation = CLLocation(latitude: self.latitude, longitude: self.longitude)
        return fromLocation.distance(from: toLocation) // Returns meters
    }
    
    // Get display-friendly cuisine name
    func getCuisineDisplayName() -> String {
        if cuisine.isEmpty || cuisine == "Unknown" {
            return "Restaurant"
        }
        // Capitalize first letter of each word
        return cuisine.split(separator: ";")
            .first?
            .trimmingCharacters(in: .whitespaces)
            .capitalized ?? "Restaurant"
    }
}

// MARK: - Overpass API Response

struct OverpassElement: Codable {
    let type: String
    let id: Int64
    let lat: Double?
    let lon: Double?
    let tags: [String: String]?
    
    enum CodingKeys: String, CodingKey {
        case type, id, lat, lon, tags
    }
}

struct OverpassResponse: Codable {
    let elements: [OverpassElement]
}

// MARK: - Overpass API Service

class OverpassApiService {
    
    private let session: URLSession
    private let baseURL = AppConfig.Overpass.baseURL
    private let interpreterEndpoint = AppConfig.Overpass.interpreterEndpoint
    private let timeout: TimeInterval = TimeInterval(AppConfig.Overpass.timeoutSeconds)
    
    init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = timeout
        config.timeoutIntervalForResource = timeout * 2
        self.session = URLSession(configuration: config)
    }
    
    // MARK: - Query Restaurants
    
    /// Query restaurants near a location using Overpass API
    /// - Parameters:
    ///   - latitude: Center latitude
    ///   - longitude: Center longitude
    ///   - radius: Search radius in meters
    /// - Returns: Array of restaurants sorted by distance
    func queryRestaurants(latitude: Double, longitude: Double, radius: Int) async throws -> [OverpassRestaurant] {
        // Build Overpass QL query
        let query = buildOverpassQuery(latitude: latitude, longitude: longitude, radius: radius)
        
        // Create URL
        guard let url = URL(string: "\(baseURL)\(interpreterEndpoint)") else {
            throw OverpassError.invalidURL
        }
        
        // Create request
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        request.httpBody = "data=\(query.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? query)".data(using: .utf8)
        
        // Perform request with retry
        let config = RetryConfig(enabled: true, delaySeconds: 2.0, maxAttempts: 3, backoffMultiplier: 1.0)
        return try await RetryHelper.retry(config: config) {
            let (data, response) = try await self.session.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw OverpassError.invalidResponse
            }
            
            guard httpResponse.statusCode == 200 else {
                throw OverpassError.serverError(httpResponse.statusCode)
            }
            
            // Parse response
            let overpassResponse = try JSONDecoder().decode(OverpassResponse.self, from: data)
            
            // Convert to restaurants
            return self.parseRestaurants(from: overpassResponse.elements, userLat: latitude, userLon: longitude)
        }
    }
    
    // MARK: - Query Building
    
    private func buildOverpassQuery(latitude: Double, longitude: Double, radius: Int) -> String {
        """
        [out:json][timeout:25];
        (
          node["amenity"="restaurant"](around:\(radius),\(latitude),\(longitude));
          node["amenity"="fast_food"](around:\(radius),\(latitude),\(longitude));
          way["amenity"="restaurant"](around:\(radius),\(latitude),\(longitude));
          way["amenity"="fast_food"](around:\(radius),\(latitude),\(longitude));
        );
        out center tags;
        """
    }
    
    // MARK: - Response Parsing
    
    private func parseRestaurants(from elements: [OverpassElement], userLat: Double, userLon: Double) -> [OverpassRestaurant] {
        var restaurants: [OverpassRestaurant] = []
        
        for element in elements {
            // Get coordinates - for ways, use center if available
            guard let lat = element.lat,
                  let lon = element.lon,
                  let tags = element.tags,
                  let name = tags["name"], !name.isEmpty else {
                continue
            }
            
            // Extract cuisine
            let cuisine = tags["cuisine"] ?? tags["food"] ?? "Unknown"
            
            // Extract address
            var addressComponents: [String] = []
            if let street = tags["addr:street"] {
                if let housenumber = tags["addr:housenumber"] {
                    addressComponents.append("\(housenumber) \(street)")
                } else {
                    addressComponents.append(street)
                }
            }
            if let city = tags["addr:city"] {
                addressComponents.append(city)
            }
            let address = addressComponents.isEmpty ? nil : addressComponents.joined(separator: ", ")
            
            // Extract other properties
            let phone = tags["phone"]
            let website = tags["website"] ?? tags["url"]
            let openingHours = tags["opening_hours"]
            
            // Boolean properties
            let delivery = tags["delivery"] == "yes"
            let takeaway = tags["takeaway"] == "yes" || tags["take_away"] == "yes"
            let wheelchair = tags["wheelchair"] == "yes"
            let outdoorSeating = tags["outdoor_seating"] == "yes" || tags["outdoor"] == "yes"
            let wifi = tags["wifi"] == "yes" || tags["internet_access"] == "wlan"
            
            // Build tags array
            var tagList: [String] = []
            if delivery { tagList.append("Delivery") }
            if takeaway { tagList.append("Takeaway") }
            if wheelchair { tagList.append("Wheelchair") }
            if outdoorSeating { tagList.append("Outdoor Seating") }
            if wifi { tagList.append("WiFi") }
            
            let restaurant = OverpassRestaurant(
                id: element.id,
                name: name,
                latitude: lat,
                longitude: lon,
                cuisine: cuisine,
                address: address,
                phone: phone,
                website: website,
                openingHours: openingHours,
                delivery: delivery,
                takeaway: takeaway,
                wheelchair: wheelchair,
                outdoorSeating: outdoorSeating,
                wifi: wifi,
                tags: tagList
            )
            
            restaurants.append(restaurant)
        }
        
        // Sort by distance
        return restaurants.sorted { $0.distanceFrom(userLat, userLon) < $1.distanceFrom(userLat, userLon) }
    }
}

// MARK: - Overpass Error

enum OverpassError: LocalizedError {
    case invalidURL
    case invalidResponse
    case serverError(Int)
    case noData
    case parsingError
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid API URL"
        case .invalidResponse:
            return "Invalid response from server"
        case .serverError(let code):
            return "Server error: HTTP \(code)"
        case .noData:
            return "No restaurant data available"
        case .parsingError:
            return "Failed to parse restaurant data"
        }
    }
}

// MARK: - Mock Data for Testing

extension OverpassApiService {
    
    /// Get mock restaurants for testing without API
    static func getMockRestaurants() -> [OverpassRestaurant] {
        return [
            OverpassRestaurant(
                id: 1,
                name: "Tony's Pizzeria",
                latitude: 37.7749,
                longitude: -122.4194,
                cuisine: "italian;pizza",
                address: "123 Main St, San Francisco",
                phone: "+1-555-123-4567",
                website: "https://tonyspizza.example.com",
                openingHours: "Mo-Su 11:00-22:00",
                delivery: true,
                takeaway: true,
                wheelchair: true,
                outdoorSeating: true,
                wifi: true,
                tags: ["Delivery", "Takeaway", "WiFi"]
            ),
            OverpassRestaurant(
                id: 2,
                name: "El Corazón Mexican",
                latitude: 37.7849,
                longitude: -122.4094,
                cuisine: "mexican",
                address: "456 Mission St, San Francisco",
                phone: "+1-555-987-6543",
                website: nil,
                openingHours: "Mo-Sa 10:00-23:00",
                delivery: true,
                takeaway: true,
                wheelchair: false,
                outdoorSeating: false,
                wifi: false,
                tags: ["Delivery", "Takeaway"]
            ),
            OverpassRestaurant(
                id: 3,
                name: "Sushi Express",
                latitude: 37.7649,
                longitude: -122.4294,
                cuisine: "japanese;sushi",
                address: "789 Market St, San Francisco",
                phone: nil,
                website: "https://sushiexpress.example.com",
                openingHours: nil,
                delivery: false,
                takeaway: true,
                wheelchair: true,
                outdoorSeating: false,
                wifi: true,
                tags: ["Takeaway", "Wheelchair", "WiFi"]
            )
        ]
    }
}
