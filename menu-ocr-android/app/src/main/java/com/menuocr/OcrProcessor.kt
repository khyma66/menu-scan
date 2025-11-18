package com.menuocr

import android.graphics.Bitmap
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
// import javax.inject.Inject  // Hilt disabled for build compatibility
// import javax.inject.Singleton  // Hilt disabled for build compatibility
import kotlinx.coroutines.tasks.await

// @Singleton  // Hilt disabled
// @Inject constructor()  // Hilt disabled
class OcrProcessor {

    private val recognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)

    suspend fun processImage(bitmap: Bitmap): String {
        return try {
            val image = InputImage.fromBitmap(bitmap, 0)
            val result = recognizer.process(image).await()
            result.text
        } catch (e: Exception) {
            throw Exception("OCR processing failed: ${e.message}")
        }
    }

    fun close() {
        recognizer.close()
    }
}