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
        
        // Preprocess image for better OCR results
        let processedImage = preprocessImage(image)
        guard let processedCGImage = processedImage.cgImage else {
            throw OCRError.imageProcessingFailed
        }
        
        let requestHandler = VNImageRequestHandler(cgImage: processedCGImage, options: [:])
        
        return try await withCheckedThrowingContinuation { continuation in
            textRecognitionRequest.completionHandler = { request, error in
                if let error = error {
                    continuation.resume(throwing: error)
                    return
                }
                
                guard let observations = request.results as? [VNRecognizedTextObservation] else {
                    continuation.resume(throwing: OCRError.noTextFound)
                    return
                }
                
                let recognizedText = self.extractTextFromObservations(observations)
                continuation.resume(returning: recognizedText)
            }
            
            do {
                try requestHandler.perform([textRecognitionRequest])
            } catch {
                continuation.resume(throwing: error)
            }
        }
    }
    
    // MARK: - Backend API OCR Processing
    
    func processImageViaAPI(_ image: UIImage, language: String = "en") async throws -> MenuResponse {
        // Convert image to base64 with compression
        let base64String = try await compressAndEncodeImage(image, quality: 0.8, maxSize: 1024)
        
        let request = OcrRequest(image_base64: base64String, language: language)
        return try await apiService.processOcr(request: request)
    }
    
    func processImageBatchViaAPI(_ images: [UIImage], language: String = "en") async throws -> [MenuResponse] {
        let requests = try await images.asyncMap { image in
            let base64String = try await compressAndEncodeImage(image, quality: 0.8, maxSize: 1024)
            return OcrRequest(image_base64: base64String, language: language)
        }
        
        return try await apiService.processOcrBatch(requests: requests)
    }
    
    // MARK: - Image Processing & Table Extraction
    
    func processImageForTableExtraction(_ image: UIImage) async throws -> TableExtractionResponse {
        // First get OCR text
        let ocrText = try await processImageLocally(image)
        
        // Then extract table data using Qwen AI
        return try await apiService.extractTableFromOCR(ocrText: ocrText, imageUrl: nil)
    }
    
    func extractTableFromText(_ text: String, format: String = "markdown") async throws -> TableExtractionResponse {
        let request = TableExtractionRequest(
            text: text,
            format: format,
            source: "manual"
        )
        return try await apiService.extractTable(request: request)
    }
    
    // MARK: - Translation Services
    
    func translateRecognizedText(_ text: String, targetLanguage: String, sourceLanguage: String? = nil) async throws -> String {
        // Use backend translation service
        // This would call the translation endpoint from the FastAPI backend
        let translationRequest = TranslationRequest(
            text: text,
            targetLanguage: targetLanguage,
            sourceLanguage: sourceLanguage
        )
        
        // For now, return original text as translation is handled by backend
        // In a real implementation, you'd call the translation API
        return text
    }
    
    // MARK: - Helper Methods
    
    private func preprocessImage(_ image: UIImage) -> UIImage {
        // Convert to grayscale for better text recognition
        guard let ciImage = CIImage(image: image) else { return image }
        
        let context = CIContext(options: nil)
        guard let filter = CIFilter.colorControls() else { return image }
        
        filter.inputImage = ciImage
        filter.saturation = 0.0 // Remove color
        filter.contrast = 1.1   // Slightly increase contrast
        
        guard let outputImage = filter.outputImage,
              let cgImage = context.createCGImage(outputImage, from: outputImage.extent) else {
            return image
        }
        
        return UIImage(cgImage: cgImage)
    }
    
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
                do {
                    let compressedImage = self.resizeAndCompressImage(image, maxSize: maxSize, quality: quality)
                    
                    guard let data = compressedImage.jpegData(compressionQuality: quality) else {
                        continuation.resume(throwing: OCRError.imageCompressionFailed)
                        return
                    }
                    
                    let base64String = data.base64EncodedString()
                    continuation.resume(returning: base64String)
                } catch {
                    continuation.resume(throwing: error)
                }
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
    
    // MARK: - Camera & Gallery Integration
    
    func captureImageFromCamera() async throws -> UIImage {
        return try await withCheckedThrowingContinuation { continuation in
            // This would integrate with UIImagePickerController for camera capture
            // Implementation depends on the view controller that calls this method
            continuation.resume(throwing: OCRError.cameraNotAvailable)
        }
    }
    
    func selectImageFromGallery() async throws -> UIImage {
        return try await withCheckedThrowingContinuation { continuation in
            // This would integrate with UIImagePickerController for gallery selection
            continuation.resume(throwing: OCRError.galleryNotAvailable)
        }
    }
    
    // MARK: - OCR Analysis & Results
    
    func analyzeOcrResults(_ text: String) -> OcrAnalysisResult {
        let wordCount = text.components(separatedBy: .whitespacesAndNewlines).count
        let lineCount = text.components(separatedBy: .newlines).count
        let characterCount = text.count
        
        // Detect if text looks like a menu
        let isLikelyMenu = isLikelyMenuText(text)
        
        // Extract potential dish names
        let potentialDishes = extractPotentialDishes(text)
        
        // Extract potential prices
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
        // Simple pattern matching for dish names
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
        // Simple confidence calculation based on text characteristics
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

struct TranslationRequest: Codable {
    let text: String
    let targetLanguage: String
    let sourceLanguage: String?
}

struct TranslationResponse: Codable {
    let translatedText: String
    let sourceLanguage: String
    let targetLanguage: String
    let confidence: Float?
}

// MARK: - Async Extension for Arrays

extension Array {
    func asyncMap<T>(_ transform: (Element) async throws -> T) async throws -> [T] {
        var results = [T]()
        for element in self {
            let result = try await transform(element)
            results.append(result)
        }
        return results
    }
}