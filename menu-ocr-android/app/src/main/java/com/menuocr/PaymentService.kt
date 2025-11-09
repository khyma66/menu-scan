package com.menuocr

import androidx.activity.ComponentActivity
import com.stripe.android.PaymentConfiguration
import com.stripe.android.paymentsheet.PaymentSheet
import com.stripe.android.paymentsheet.PaymentSheetResult
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class PaymentService @Inject constructor() {

    private lateinit var paymentSheet: PaymentSheet

    fun initialize(activity: ComponentActivity, stripePublishableKey: String) {
        PaymentConfiguration.init(activity.applicationContext, stripePublishableKey)
        paymentSheet = PaymentSheet(activity, ::onPaymentSheetResult)
    }

    fun presentPaymentSheet(
        paymentIntentClientSecret: String,
        configuration: PaymentSheet.Configuration
    ) {
        paymentSheet.presentWithPaymentIntent(
            paymentIntentClientSecret,
            configuration
        )
    }

    private fun onPaymentSheetResult(paymentSheetResult: PaymentSheetResult) {
        when (paymentSheetResult) {
            is PaymentSheetResult.Completed -> {
                // Payment completed successfully
                handlePaymentSuccess()
            }
            is PaymentSheetResult.Canceled -> {
                // Payment canceled by user
                handlePaymentCanceled()
            }
            is PaymentSheetResult.Failed -> {
                // Payment failed
                handlePaymentFailed(paymentSheetResult.error)
            }
        }
    }

    private fun handlePaymentSuccess() {
        // Handle successful payment
        // Update UI, show success message, unlock premium features, etc.
    }

    private fun handlePaymentCanceled() {
        // Handle payment cancellation
        // Show appropriate message to user
    }

    private fun handlePaymentFailed(error: Throwable) {
        // Handle payment failure
        // Show error message, log error, etc.
    }
}