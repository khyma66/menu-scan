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
class UserPreferencesViewModel @Inject constructor(
    private val apiService: ApiService
) : ViewModel() {

    private val _preferencesState = MutableStateFlow<PreferencesState>(PreferencesState.Idle)
    val preferencesState: StateFlow<PreferencesState> = _preferencesState

    private val _foodPreferencesState = MutableStateFlow<FoodPreferencesState>(FoodPreferencesState.Idle)
    val foodPreferencesState: StateFlow<FoodPreferencesState> = _foodPreferencesState

    fun loadUserPreferences() {
        viewModelScope.launch {
            _preferencesState.value = PreferencesState.Loading
            try {
                val response = apiService.getUserProfile()
                if (response.isSuccessful) {
                    response.body()?.let { preferences ->
                        _preferencesState.value = PreferencesState.Success(preferences)
                    } ?: run {
                        _preferencesState.value = PreferencesState.Error("Failed to load preferences")
                    }
                } else {
                    _preferencesState.value = PreferencesState.Error("Failed to load preferences: ${response.message()}")
                }
            } catch (e: Exception) {
                _preferencesState.value = PreferencesState.Error(e.message ?: "Unknown error")
            }
        }
    }

    fun loadFoodPreferences() {
        viewModelScope.launch {
            _foodPreferencesState.value = FoodPreferencesState.Loading
            try {
                val response = apiService.getFoodPreferences()
                if (response.isSuccessful) {
                    response.body()?.let { preferences ->
                        _foodPreferencesState.value = FoodPreferencesState.Success(preferences)
                    } ?: run {
                        _foodPreferencesState.value = FoodPreferencesState.Error("Failed to load food preferences")
                    }
                } else {
                    _foodPreferencesState.value = FoodPreferencesState.Error("Failed to load food preferences: ${response.message()}")
                }
            } catch (e: Exception) {
                _foodPreferencesState.value = FoodPreferencesState.Error(e.message ?: "Unknown error")
            }
        }
    }

    fun addFoodPreference(preference: FoodPreferenceRequest) {
        viewModelScope.launch {
            _foodPreferencesState.value = FoodPreferencesState.Loading
            try {
                val response = apiService.addFoodPreference(preference)
                if (response.isSuccessful) {
                    // Reload food preferences after adding
                    loadFoodPreferences()
                } else {
                    _foodPreferencesState.value = FoodPreferencesState.Error("Failed to add food preference: ${response.message()}")
                }
            } catch (e: Exception) {
                _foodPreferencesState.value = FoodPreferencesState.Error(e.message ?: "Unknown error")
            }
        }
    }

    fun updateUserProfile(request: UserProfileUpdateRequest) {
        viewModelScope.launch {
            _preferencesState.value = PreferencesState.Loading
            try {
                val response = apiService.updateUserProfile(request)
                if (response.isSuccessful) {
                    // Reload preferences after updating
                    loadUserPreferences()
                } else {
                    _preferencesState.value = PreferencesState.Error("Failed to update profile: ${response.message()}")
                }
            } catch (e: Exception) {
                _preferencesState.value = PreferencesState.Error(e.message ?: "Unknown error")
            }
        }
    }

    fun removeFoodPreference(preferenceId: String) {
        viewModelScope.launch {
            _foodPreferencesState.value = FoodPreferencesState.Loading
            try {
                val response = apiService.removeFoodPreference(preferenceId)
                if (response.isSuccessful) {
                    // Reload food preferences after removing
                    loadFoodPreferences()
                } else {
                    _foodPreferencesState.value = FoodPreferencesState.Error("Failed to remove food preference: ${response.message()}")
                }
            } catch (e: Exception) {
                _foodPreferencesState.value = FoodPreferencesState.Error(e.message ?: "Unknown error")
            }
        }
    }
}

sealed class PreferencesState {
    object Idle : PreferencesState()
    object Loading : PreferencesState()
    data class Success(val preferences: UserPreferences) : PreferencesState()
    data class Error(val message: String) : PreferencesState()
}

sealed class FoodPreferencesState {
    object Idle : PreferencesState()
    object Loading : PreferencesState()
    data class Success(val preferences: List<FoodPreference>) : PreferencesState()
    data class Error(val message: String) : PreferencesState()
}