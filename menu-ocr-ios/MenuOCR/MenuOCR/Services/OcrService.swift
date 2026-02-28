import UIKit
import Vision

class OcrService {
    private let textRecognitionRequest = VNRecognizeTextRequest()
    private let apiService: ApiService
    
    init(apiService: ApiService) {
        self.apiService = apiService
        configureTextRecognition()
    }
    
    private func configureTextRecognition() {
        textRecognitionRequest.recognitionLevel = .accurate
        textRecognitionRequest.usesLanguageCorrection = true
        textRecognitionRequest.usesCPUOnly = false
        textRecognitionRequest.recognitionLanguages = ["en-US", "es-ES", "fr-FR", "de-DE", "it-IT", "pt-BR", "zh-CN", "ja-JP", "ko-KR"]
    }
    
    // MARK: - Local Vision Framework OCR
    
    func processImageLocally(_ image: UIImage) async throws -> String {
        guard let cgImage = image.cgImage else {
            throw OCRError.invalidImage
        }
        
        let requestHandler = VNImageRequestHandler(cgImage: cgImage, options: [:])
        
        return try await withCheckedThrowingContinuation { continuation in
            do {
                try requestHandler.perform([textRecognitionRequest])
                guard let observations = textRecognitionRequest.results as? [VNRecognizedTextObservation] else {
                    continuation.resume(throwing: OCRError.noTextFound)
                    return
                }
                let recognizedText = self.extractTextFromObservations(observations)
                continuation.resume(returning: recognizedText)
            } catch {
                continuation.resume(throwing: error)
            }
        }
    }
    
    // MARK: - Backend API OCR Processing
    
    func processImageViaAPI(_ image: UIImage, language: String = "en") async throws -> MenuResponse {
        let base64String = try await compressAndEncodeImage(image, quality: 0.8, maxSize: 1024)
        let request = OcrRequest(image_base64: base64String)
        return try await apiService.processOcr(request: request)
    }
    
    func processImageBatchViaAPI(_ images: [UIImage], language: String = "en") async throws -> [MenuResponse] {
        var requests: [OcrRequest] = []
        for image in images {
            let base64String = try await compressAndEncodeImage(image, quality: 0.8, maxSize: 1024)
            requests.append(OcrRequest(image_base64: base64String))
        }
        return try await apiService.processOcrBatch(requests: requests)
    }
    
    // MARK: - Image Processing & Table Extraction
    
    func processImageForTableExtraction(_ image: UIImage) async throws -> TableExtractionResponse {
        let ocrText = try await processImageLocally(image)
        return try await apiService.extractTableFromOCR(ocrText: ocrText, imageUrl: nil)
    }
    
    func extractTableFromText(_ text: String, format: String = "markdown") async throws -> TableExtractionResponse {
        let request = TableExtractionRequest(
            text: text,
            source: "manual",
            imageUrl: nil
        )
        return try await apiService.extractTable(request: request)
    }
    
    // MARK: - Helper Methods
    
    private func extractTextFromObservations(_ observations: [VNRecognizedTextObservation]) -> String {
        var allText: [String] = []
        for observation in observations {
            if let candidate = observation.topCandidates(1).first {
                allText.append(candidate.string)
            }
        }
        return allText.joined(separator: "\n")
    }
    
    private func compressAndEncodeImage(_ image: UIImage, quality: CGFloat, maxSize: CGFloat) async throws -> String {
        return try await withCheckedThrowingContinuation { continuation in
            DispatchQueue.global(qos: .userInitiated).async {
                let compressedImage = self.resizeAndCompressImage(image, maxSize: maxSize, quality: quality)
                guard let data = compressedImage.jpegData(compressionQuality: quality) else {
                    continuation.resume(throwing: OCRError.imageCompressionFailed)
                    return
                }
                let base64String = data.base64EncodedString()
                continuation.resume(returning: base64String)
            }
        }
    }
    
    private func resizeAndCompressImage(_ image: UIImage, maxSize: CGFloat, quality: CGFloat) -> UIImage {
        let size = image.size
        let maxDimension = max(size.width, size.height)
        
        if maxDimension <= maxSize {
            return image
        }
        
        let scale = maxSize / maxDimension
        let newSize = CGSize(width: size.width * scale, height: size.height * scale)
        
        UIGraphicsBeginImageContextWithOptions(newSize, false, 0.0)
        image.draw(in: CGRect(origin: .zero, size: newSize))
        let resizedImage = UIGraphicsGetImageFromCurrentImageContext()
        UIGraphicsEndImageContext()
        
        return resizedImage ?? image
    }
    
    // MARK: - OCR Analysis & Results
    
    func analyzeOcrResults(_ text: String) -> OcrAnalysisResult {
        let wordCount = text.components(separatedBy: .whitespacesAndNewlines).count
        let lineCount = text.components(separatedBy: .newlines).count
        let characterCount = text.count
        
        let isLikelyMenu = isLikelyMenuText(text)
        let potentialDishes = extractPotentialDishes(text)
        let potentialPrices = extractPotentialPrices(text)
        
        return OcrAnalysisResult(
            wordCount: wordCount,
            lineCount: lineCount,
            characterCount: characterCount,
            isLikelyMenu: isLikelyMenu,
            potentialDishes: potentialDishes,
            potentialPrices: potentialPrices,
            confidence: calculateConfidence(text)
        )
    }
    
    private func isLikelyMenuText(_ text: String) -> Bool {
        let menuIndicators = ["menu", "appetizer", "entree", "dessert", "beverage", "price", "$", "wine", "beer"]
        let lowerText = text.lowercased()
        return menuIndicators.contains { lowerText.contains($0) }
    }
    
    private func extractPotentialDishes(_ text: String) -> [String] {
        let lines = text.components(separatedBy: .newlines)
        return lines.filter { line in
            !line.trimmingCharacters(in: .whitespaces).isEmpty &&
            !line.contains("$") &&
            line.count > 3 &&
            line.count < 50
        }
    }
    
    private func extractPotentialPrices(_ text: String) -> [Double] {
        let pricePattern = #"\$?\d+\.?\d*"#
        let regex = try? NSRegularExpression(pattern: pricePattern)
        let range = NSRange(text.startIndex..<text.endIndex, in: text)
        
        var prices: [Double] = []
        regex?.enumerateMatches(in: text, options: [], range: range) { match, _, _ in
            if let matchRange = match?.range(at: 0),
               let swiftRange = Range(matchRange, in: text) {
                let priceString = text[swiftRange].replacingOccurrences(of: "$", with: "")
                if let price = Double(priceString) {
                    prices.append(price)
                }
            }
        }
        return prices
    }
    
    private func calculateConfidence(_ text: String) -> Float {
        let hasProperSpacing = text.range(of: #"\s{2,}"#, options: .regularExpression) == nil
        let hasReasonableLength = text.count > 10 && text.count < 5000
        let hasCommonWords = text.lowercased().contains("the") || text.lowercased().contains("and")
        
        var confidence: Float = 0.5
        if hasProperSpacing { confidence += 0.2 }
        if hasReasonableLength { confidence += 0.2 }
        if hasCommonWords { confidence += 0.1 }
        
        return min(confidence, 1.0)
    }
    
    enum OCRError: Error, LocalizedError {
        case invalidImage
        case noTextFound
        case imageProcessingFailed
        case imageCompressionFailed
        case cameraNotAvailable
        case galleryNotAvailable
        case processingFailed(String)
        case invalidImageFormat
        
        var errorDescription: String? {
            switch self {
            case .invalidImage:
                return "Invalid image provided for OCR processing"
            case .noTextFound:
                return "No text could be recognized in the image"
            case .imageProcessingFailed:
                return "Failed to process image for OCR"
            case .imageCompressionFailed:
                return "Failed to compress image for transmission"
            case .cameraNotAvailable:
                return "Camera is not available"
            case .galleryNotAvailable:
                return "Photo gallery is not available"
            case .processingFailed(let message):
                return "OCR processing failed: \(message)"
            case .invalidImageFormat:
                return "Invalid image format"
            }
        }
    }
}

// MARK: - Supporting Types

struct OcrAnalysisResult {
    let wordCount: Int
    let lineCount: Int
    let characterCount: Int
    let isLikelyMenu: Bool
    let potentialDishes: [String]
    let potentialPrices: [Double]
    let confidence: Float
}
