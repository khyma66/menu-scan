package com.menuocr.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.menuocr.*
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class PaymentViewModel @Inject constructor(
    private val apiService: ApiService,
    private val paymentService: PaymentService
) : ViewModel() {

    private val _paymentState = MutableStateFlow<PaymentState>(PaymentState.Idle)
    val paymentState: StateFlow<PaymentState> = _paymentState

    private val _paymentHistoryState = MutableStateFlow<PaymentHistoryState>(PaymentHistoryState.Idle)
    val paymentHistoryState: StateFlow<PaymentHistoryState> = _paymentHistoryState

    fun createPaymentIntent(amount: Int, description: String? = null) {
        viewModelScope.launch {
            _paymentState.value = PaymentState.Loading
            try {
                val request = PaymentIntentRequest(
                    amount = amount,
                    description = description
                )
                val response = apiService.createPaymentIntent(request)

                if (response.isSuccessful) {
                    response.body()?.let { paymentIntent ->
                        _paymentState.value = PaymentState.PaymentIntentCreated(paymentIntent)
                    } ?: run {
                        _paymentState.value = PaymentState.Error("Failed to create payment intent")
                    }
                } else {
                    _paymentState.value = PaymentState.Error("Failed to create payment intent: ${response.message()}")
                }
            } catch (e: Exception) {
                _paymentState.value = PaymentState.Error(e.message ?: "Unknown error")
            }
        }
    }

    fun loadPaymentHistory() {
        viewModelScope.launch {
            _paymentHistoryState.value = PaymentHistoryState.Loading
            try {
                val response = apiService.getPaymentHistory()

                if (response.isSuccessful) {
                    response.body()?.let { history ->
                        _paymentHistoryState.value = PaymentHistoryState.Success(history)
                    } ?: run {
                        _paymentHistoryState.value = PaymentHistoryState.Error("Failed to load payment history")
                    }
                } else {
                    _paymentHistoryState.value = PaymentHistoryState.Error("Failed to load payment history: ${response.message()}")
                }
            } catch (e: Exception) {
                _paymentHistoryState.value = PaymentHistoryState.Error(e.message ?: "Unknown error")
            }
        }
    }

    fun presentPaymentSheet(paymentIntent: PaymentIntentResponse) {
        // This would be called from the Activity/Fragment to present the PaymentSheet
        // Implementation depends on how you structure the UI
    }
}

sealed class PaymentState {
    object Idle : PaymentState()
    object Loading : PaymentState()
    data class PaymentIntentCreated(val paymentIntent: PaymentIntentResponse) : PaymentState()
    data class Error(val message: String) : PaymentState()
}

sealed class PaymentHistoryState {
    object Idle : PaymentState()
    object Loading : PaymentState()
    data class Success(val history: PaymentHistoryResponse) : PaymentState()
    data class Error(val message: String) : PaymentState()
}