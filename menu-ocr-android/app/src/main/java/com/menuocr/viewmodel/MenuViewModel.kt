package com.menuocr.viewmodel

import android.graphics.Bitmap
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.menuocr.*
import com.menuocr.cache.CacheManager
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import com.google.gson.Gson
import java.io.ByteArrayOutputStream
import java.util.*
import javax.inject.Inject

@HiltViewModel
class MenuViewModel @Inject constructor(
    private val ocrProcessor: OcrProcessor,
    private val apiService: ApiService,
    private val cacheManager: CacheManager
) : ViewModel() {

    private val gson = Gson()

    private val _menuState = MutableStateFlow<MenuState>(MenuState.Idle)
    val menuState: StateFlow<MenuState> = _menuState

    fun processImage(bitmap: Bitmap) {
        viewModelScope.launch {
            _menuState.value = MenuState.Loading

            try {
                // First, try local OCR
                val extractedText = ocrProcessor.processImage(bitmap)

                // Then send to backend for menu processing
                val base64Image = bitmapToBase64(bitmap)
                val ocrRequest = OcrRequest(image_base64 = base64Image)
                val ocrResponse = apiService.processOcr(ocrRequest)

                if (ocrResponse.isSuccessful) {
                    val menuResponse = ocrResponse.body()
                    if (menuResponse != null) {
                        // Extract dishes from the processed text
                        val dishRequest = DishRequest(text = menuResponse.text)
                        val dishResponse = apiService.extractDishes(dishRequest)

                        if (dishResponse.isSuccessful) {
                            val dishes = dishResponse.body()?.dishes ?: emptyList()
                            val menu = Menu(dishes = dishes)
                            _menuState.value = MenuState.Success(menu)
                        } else {
                            _menuState.value = MenuState.Error("Failed to extract dishes")
                        }
                    } else {
                        _menuState.value = MenuState.Error("Failed to process OCR")
                    }
                } else {
                    // Fallback to local OCR result
                    val fallbackDishes = parseDishesFromText(extractedText)
                    val menu = Menu(dishes = fallbackDishes)
                    _menuState.value = MenuState.Success(menu)
                }
            } catch (e: Exception) {
                _menuState.value = MenuState.Error(e.message ?: "Unknown error")
            }
        }
    }

    private fun bitmapToBase64(bitmap: Bitmap): String {
        val outputStream = ByteArrayOutputStream()
        bitmap.compress(Bitmap.CompressFormat.JPEG, 80, outputStream)
        val byteArray = outputStream.toByteArray()
        return Base64.getEncoder().encodeToString(byteArray)
    }

    private fun parseDishesFromText(text: String): List<Dish> {
        // Simple fallback parsing - in a real app, you'd want more sophisticated parsing
        val lines = text.lines().filter { it.isNotBlank() }
        return lines.mapNotNull { line ->
            // Very basic parsing - look for lines that might contain dish names and prices
            val trimmed = line.trim()
            if (trimmed.length > 3) {
                Dish(name = trimmed, price = null, description = null)
            } else null
        }
    }
}

sealed class MenuState {
    object Idle : MenuState()
    object Loading : MenuState()
    data class Success(val menu: Menu) : MenuState()
    data class Error(val message: String) : MenuState()
}

data class Menu(
    val dishes: List<Dish>
)