//
//  MenuModels.swift
//  MenuOCR
//
//  Created by MenuOCR on 2025-01-07.
//

import Foundation

struct Dish: Codable, Identifiable {
    let id = UUID()
    let name: String
    let price: Double?
    let description: String?

    enum CodingKeys: String, CodingKey {
        case name, price, description
    }
}

struct Menu: Codable {
    let dishes: [Dish]
}

struct OcrRequest: Codable {
    let image_base64: String
    let language: String = "en"
}

struct MenuResponse: Codable {
    let text: String
    let language: String
}

struct DishRequest: Codable {
    let text: String
    let language: String = "en"
}

struct DishResponse: Codable {
    let dishes: [Dish]
}

enum MenuState {
    case idle
    case loading
    case success(Menu)
    case error(String)
}

enum AuthState {
    case idle
    case loading
    case authenticated(User)
    case unauthenticated
    case error(String)
}

struct User {
    let id: String
    let email: String
    let name: String?
}

// MARK: - Payment Models

struct PaymentIntentRequest: Codable {
    let amount: Int
    let currency: String
    let description: String?
    let metadata: [String: String]?

    init(amount: Int, currency: String = "usd", description: String? = nil, metadata: [String: String]? = nil) {
        self.amount = amount
        self.currency = currency
        self.description = description
        self.metadata = metadata
    }
}

struct PaymentIntentResponse: Codable {
    let client_secret: String
    let payment_intent_id: String
    let amount: Int
    let currency: String
    let status: String
}

struct PaymentHistoryResponse: Codable {
    let payment_intents: [PaymentIntent]
    let subscriptions: [Subscription]
}

struct PaymentIntent: Codable {
    let id: String
    let amount: Int
    let currency: String
    let status: String
    let created: Int
    let description: String?
}

struct Subscription: Codable {
    let id: String
    let status: String
    let current_period_start: Int
    let current_period_end: Int
    let items: [SubscriptionItem]
}

struct SubscriptionItem: Codable {
    let price: Price
}

struct Price: Codable {
    let id: String
    let nickname: String?
    let unit_amount: Int?
    let currency: String
}