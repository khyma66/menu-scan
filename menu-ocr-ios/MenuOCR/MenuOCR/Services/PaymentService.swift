//
//  PaymentService.swift
//  MenuOCR
//
//  Created by MenuOCR on 2025-01-07.
//

import Foundation
import Stripe

class PaymentService: NSObject, STPApplePayContextDelegate {
    static let shared = PaymentService()

    private var paymentSheet: PaymentSheet?

    func initialize(stripePublishableKey: String) {
        STPAPIClient.shared.publishableKey = stripePublishableKey
    }

    func presentPaymentSheet(
        paymentIntentClientSecret: String,
        from viewController: UIViewController,
        completion: @escaping (PaymentSheetResult) -> Void
    ) {
        var configuration = PaymentSheet.Configuration()
        configuration.merchantDisplayName = "Menu OCR"
        configuration.allowsDelayedPaymentMethods = true

        PaymentSheet.create(
            paymentIntentClientSecret: paymentIntentClientSecret,
            configuration: configuration
        ) { [weak self] result in
            switch result {
            case .success(let paymentSheet):
                self?.paymentSheet = paymentSheet
                paymentSheet.present(from: viewController) { result in
                    completion(result)
                }
            case .failure(let error):
                print("Failed to create PaymentSheet: \(error)")
                completion(.failed(error: error))
            }
        }
    }

    // MARK: - STPApplePayContextDelegate

    func applePayContext(_ context: STPApplePayContext, didCreatePaymentMethod paymentMethod: STPPaymentMethod, paymentInformation: PKPayment, completion: @escaping STPIntentClientSecretCompletionBlock) {
        // Handle Apple Pay payment method creation
        // This would typically call your backend to create a payment intent
    }

    func applePayContext(_ context: STPApplePayContext, didCompleteWith status: STPPaymentStatus, error: Error?) {
        // Handle Apple Pay completion
    }
}