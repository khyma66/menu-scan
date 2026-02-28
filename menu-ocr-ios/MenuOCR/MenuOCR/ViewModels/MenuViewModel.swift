//
//  MenuViewModel.swift
//  MenuOCR
//
//  Created by MenuOCR on 2025-01-07.
//

import UIKit
import Combine

class MenuViewModel: ObservableObject {
    @Published var menuState: MenuState = .idle

    private let apiService = ApiService()
    private lazy var ocrService = OcrService(apiService: apiService)

    func processImage(_ image: UIImage) {
        menuState = .loading

        Task {
            do {
                // First, try local OCR
                let extractedText = try await ocrService.processImageLocally(image)

                // Then send to backend for menu processing
                let base64Image = imageToBase64(image)
                let ocrRequest = OcrRequest(image_base64: base64Image)

                do {
                    let menuResponse = try await apiService.processOcr(request: ocrRequest)

                    // Extract dishes from the processed text
                    let dishRequest = DishRequest(text: menuResponse.raw_text)
                    let dishResponse = try await apiService.extractDishes(request: dishRequest)

                    let menu = Menu(dishes: dishResponse.dishes)
                    await MainActor.run {
                        menuState = .success(menu)
                    }
                } catch {
                    // Fallback to local OCR result
                    let fallbackDishes = parseDishesFromText(extractedText)
                    let menu = Menu(dishes: fallbackDishes)
                    await MainActor.run {
                        menuState = .success(menu)
                    }
                }
            } catch {
                await MainActor.run {
                    menuState = .error(error.localizedDescription)
                }
            }
        }
    }

    private func imageToBase64(_ image: UIImage) -> String {
        guard let imageData = image.jpegData(compressionQuality: 0.8) else {
            return ""
        }
        return imageData.base64EncodedString()
    }

    private func parseDishesFromText(_ text: String) -> [Dish] {
        // Simple fallback parsing - in a real app, you'd want more sophisticated parsing
        let lines = text.components(separatedBy: .newlines)
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty && $0.count > 3 }

        return lines.map { line in
            Dish(name: line, price: nil, description: nil)
        }
    }
}