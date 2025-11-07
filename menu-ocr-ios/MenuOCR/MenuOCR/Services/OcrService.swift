//
//  OcrService.swift
//  MenuOCR
//
//  Created by MenuOCR on 2025-01-07.
//

import UIKit
import Vision

class OcrService {
    private let textRecognitionRequest = VNRecognizeTextRequest()

    init() {
        textRecognitionRequest.recognitionLevel = .accurate
        textRecognitionRequest.usesLanguageCorrection = true
    }

    func processImage(_ image: UIImage) async throws -> String {
        guard let cgImage = image.cgImage else {
            throw OCRError.invalidImage
        }

        let requestHandler = VNImageRequestHandler(cgImage: cgImage, options: [:])

        return try await withCheckedThrowingContinuation { continuation in
            do {
                try requestHandler.perform([textRecognitionRequest])

                guard let observations = textRecognitionRequest.results else {
                    continuation.resume(throwing: OCRError.noTextFound)
                    return
                }

                let recognizedText = observations.compactMap { observation in
                    observation.topCandidates(1).first?.string
                }.joined(separator: "\n")

                continuation.resume(returning: recognizedText)
            } catch {
                continuation.resume(throwing: error)
            }
        }
    }

    enum OCRError: Error {
        case invalidImage
        case noTextFound
        case processingFailed(String)
    }
}