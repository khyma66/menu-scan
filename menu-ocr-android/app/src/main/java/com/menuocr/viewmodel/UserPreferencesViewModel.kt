package com.menuocr.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.menuocr.FoodPreferenceRequest
import com.menuocr.UserPreferences
import com.menuocr.data.UserPreferencesRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class UserPreferencesViewModel @Inject constructor(
    private val repository: UserPreferencesRepository
) : ViewModel() {

    private val _foodPreferencesState = MutableStateFlow<FoodPreferencesState>(FoodPreferencesState.Idle)
    val foodPreferencesState: StateFlow<FoodPreferencesState> = _foodPreferencesState

    fun getFoodPreferences() {
        viewModelScope.launch {
            _foodPreferencesState.value = FoodPreferencesState.Loading
            val result = repository.getFoodPreferences()
            result.onSuccess {
                _foodPreferencesState.value = FoodPreferencesState.Success(it)
            }.onFailure {
                _foodPreferencesState.value = FoodPreferencesState.Error(it.message ?: "Failed to get food preferences")
            }
        }
    }

    fun addFoodPreference(preference: FoodPreferenceRequest) {
        viewModelScope.launch {
            _foodPreferencesState.value = FoodPreferencesState.Loading
            val result = repository.addFoodPreference(preference)
            result.onSuccess {
                getFoodPreferences() // Refresh the list
            }.onFailure {
                _foodPreferencesState.value = FoodPreferencesState.Error(it.message ?: "Failed to add food preference")
            }
        }
    }
}

sealed class FoodPreferencesState {
    object Idle : FoodPreferencesState()
    object Loading : FoodPreferencesState()
    data class Success(val preferences: UserPreferences) : FoodPreferencesState()
    data class Error(val message: String) : FoodPreferencesState()
}