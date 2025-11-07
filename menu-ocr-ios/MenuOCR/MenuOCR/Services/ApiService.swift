//
//  ApiService.swift
//  MenuOCR
//
//  Created by MenuOCR on 2025-01-07.
//

import Foundation

class ApiService {
    private let baseURL = "http://localhost:8000" // Update for production
    private let session = URLSession.shared

    func processOcr(request: OcrRequest) async throws -> MenuResponse {
        let url = URL(string: "\(baseURL)/ocr/process")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let jsonData = try JSONEncoder().encode(request)
        urlRequest.httpBody = jsonData

        let (data, response) = try await session.data(for: urlRequest)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }

        return try JSONDecoder().decode(MenuResponse.self, from: data)
    }

    func extractDishes(request: DishRequest) async throws -> DishResponse {
        let url = URL(string: "\(baseURL)/dishes/extract")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let jsonData = try JSONEncoder().encode(request)
        urlRequest.httpBody = jsonData

        let (data, response) = try await session.data(for: urlRequest)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }

        return try JSONDecoder().decode(DishResponse.self, from: data)
    }

    func createPaymentIntent(request: PaymentIntentRequest) async throws -> PaymentIntentResponse {
        let url = URL(string: "\(baseURL)/payments/create-payment-intent")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let jsonData = try JSONEncoder().encode(request)
        urlRequest.httpBody = jsonData

        let (data, response) = try await session.data(for: urlRequest)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }

        return try JSONDecoder().decode(PaymentIntentResponse.self, from: data)
    }

    func getPaymentHistory() async throws -> PaymentHistoryResponse {
        let url = URL(string: "\(baseURL)/payments/history")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "GET"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let (data, response) = try await session.data(for: urlRequest)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw ApiError.invalidResponse
        }

        return try JSONDecoder().decode(PaymentHistoryResponse.self, from: data)
    }

    enum ApiError: Error {
        case invalidResponse
        case networkError(Error)
        case decodingError(Error)
    }
}