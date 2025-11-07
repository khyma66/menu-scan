//
//  PaymentViewModel.swift
//  MenuOCR
//
//  Created by MenuOCR on 2025-01-07.
//

import Foundation
import Combine

class PaymentViewModel: ObservableObject {
    @Published var paymentState: PaymentState = .idle
    @Published var paymentHistoryState: PaymentHistoryState = .idle

    private let apiService = ApiService()
    private var cancellables = Set<AnyCancellable>()

    func createPaymentIntent(amount: Int, description: String? = nil) {
        paymentState = .loading

        let request = PaymentIntentRequest(
            amount: amount,
            description: description
        )

        Task {
            do {
                let response = try await apiService.createPaymentIntent(request: request)
                await MainActor.run {
                    self.paymentState = .paymentIntentCreated(response)
                }
            } catch {
                await MainActor.run {
                    self.paymentState = .error(error.localizedDescription)
                }
            }
        }
    }

    func loadPaymentHistory() {
        paymentHistoryState = .loading

        Task {
            do {
                let response = try await apiService.getPaymentHistory()
                await MainActor.run {
                    self.paymentHistoryState = .success(response)
                }
            } catch {
                await MainActor.run {
                    self.paymentHistoryState = .error(error.localizedDescription)
                }
            }
        }
    }

    func presentPaymentSheet(paymentIntent: PaymentIntentResponse, from viewController: UIViewController) {
        PaymentService.shared.presentPaymentSheet(
            paymentIntentClientSecret: paymentIntent.client_secret,
            from: viewController
        ) { [weak self] result in
            guard let self = self else { return }

            Task { @MainActor in
                switch result {
                case .completed:
                    self.paymentState = .paymentCompleted
                case .canceled:
                    self.paymentState = .paymentCanceled
                case .failed(let error):
                    self.paymentState = .error(error.localizedDescription)
                }
            }
        }
    }
}

enum PaymentState {
    case idle
    case loading
    case paymentIntentCreated(PaymentIntentResponse)
    case paymentCompleted
    case paymentCanceled
    case error(String)
}

enum PaymentHistoryState {
    case idle
    case loading
    case success(PaymentHistoryResponse)
    case error(String)
}