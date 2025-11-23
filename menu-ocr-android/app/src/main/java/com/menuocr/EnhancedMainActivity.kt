package com.menuocr

import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.os.Bundle
import android.util.Base64
import android.widget.Button
import android.widget.ImageView
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.github.dhaval2404.imagepicker.ImagePicker
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.io.ByteArrayOutputStream

class EnhancedMainActivity : AppCompatActivity() {

    private lateinit var statusText: TextView
    private lateinit var apiText: TextView
    private lateinit var resultText: TextView
    private lateinit var imageView: ImageView
    private lateinit var btnCaptureImage: Button
    private lateinit var btnSelectImage: Button
    private lateinit var btnProcessOcr: Button
    private lateinit var btnTestEnhanced: Button
    private lateinit var enhancementLevelText: TextView

    private var selectedBitmap: Bitmap? = null
    private var apiService: ApiService? = null
    private var enhancedOcrProcessor: EnhancedOcrProcessor? = null
    private val uiScope = CoroutineScope(Dispatchers.Main)
    private var enhancementLevel: String = "high" // fast, balanced, high

    private val imagePickerLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == RESULT_OK) {
            result.data?.data?.let { uri ->
                selectedBitmap = BitmapFactory.decodeStream(contentResolver.openInputStream(uri))
                imageView.setImageBitmap(selectedBitmap)
                statusText.text = "Image selected! Ready for enhanced OCR processing"
                btnProcessOcr.isEnabled = true
                btnTestEnhanced.isEnabled = true
                Toast.makeText(this, "Image selected successfully", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val allGranted = permissions.values.all { it }
        if (allGranted) {
            statusText.text = "Permissions granted! Ready to capture images"
        } else {
            statusText.text = "Permissions required for camera and gallery access"
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        setupApiService()
        
        // Create enhanced layout programmatically
        val layout = android.widget.LinearLayout(this)
        layout.orientation = android.widget.LinearLayout.VERTICAL
        layout.setPadding(16, 16, 16, 16)
        
        // Title
        val titleText = TextView(this)
        titleText.text = "Menu OCR - Enhanced with OpenRouter/Qwen"
        titleText.textSize = 24f
        titleText.setPadding(0, 0, 0, 16)
        layout.addView(titleText)
        
        // API status
        apiText = TextView(this)
        apiText.text = "FastAPI Backend: http://10.0.2.2:8000\nStatus: Initializing..."
        apiText.setPadding(0, 0, 0, 16)
        layout.addView(apiText)
        
        // Enhancement level selector
        enhancementLevelText = TextView(this)
        enhancementLevelText.text = "Enhancement Level: $enhancementLevel (high=OpenRouter, balanced=hybrid, fast=tesseract)"
        enhancementLevelText.setPadding(0, 0, 0, 16)
        layout.addView(enhancementLevelText)
        
        // Status text
        statusText = TextView(this)
        statusText.text = "Ready to test enhanced OCR functionality with OpenRouter/Qwen integration"
        statusText.setPadding(0, 0, 0, 16)
        layout.addView(statusText)
        
        // Buttons row 1
        val buttonRow1 = android.widget.LinearLayout(this)
        buttonRow1.orientation = android.widget.LinearLayout.HORIZONTAL
        buttonRow1.setPadding(0, 0, 0, 16)
        
        btnCaptureImage = Button(this)
        btnCaptureImage.text = "Capture Image"
        btnCaptureImage.setOnClickListener {
            checkPermissionsAndPickImage(true)
        }
        buttonRow1.addView(btnCaptureImage)
        
        btnSelectImage = Button(this)
        btnSelectImage.text = "Select Gallery"
        btnSelectImage.setOnClickListener {
            checkPermissionsAndPickImage(false)
        }
        buttonRow1.addView(btnSelectImage)
        
        layout.addView(buttonRow1)
        
        // Buttons row 2
        val buttonRow2 = android.widget.LinearLayout(this)
        buttonRow2.orientation = android.widget.LinearLayout.HORIZONTAL
        buttonRow2.setPadding(0, 0, 0, 16)
        
        btnProcessOcr = Button(this)
        btnProcessOcr.text = "Enhanced OCR"
        btnProcessOcr.isEnabled = false
        btnProcessOcr.setOnClickListener {
            processImageWithEnhancedOCR()
        }
        buttonRow2.addView(btnProcessOcr)
        
        btnTestEnhanced = Button(this)
        btnTestEnhanced.text = "Test OpenRouter"
        btnTestEnhanced.isEnabled = false
        btnTestEnhanced.setOnClickListener {
            testOpenRouterConnection()
        }
        buttonRow2.addView(btnTestEnhanced)
        
        layout.addView(buttonRow2)
        
        // Test API button
        val testApiButton = Button(this)
        testApiButton.text = "Test API Connection"
        testApiButton.setOnClickListener {
            testApiConnection()
        }
        layout.addView(testApiButton)
        
        // Image view
        imageView = ImageView(this)
        imageView.layoutParams = android.widget.LinearLayout.LayoutParams(
            android.widget.LinearLayout.LayoutParams.MATCH_PARENT,
            400
        )
        imageView.setBackgroundColor(ContextCompat.getColor(this, android.R.color.darker_gray))
        imageView.setOnClickListener {
            checkPermissionsAndPickImage(true)
        }
        layout.addView(imageView)
        
        // Result text
        resultText = TextView(this)
        resultText.setPadding(0, 16, 0, 0)
        resultText.text = "Enhanced OCR Results will appear here...\nUses OpenRouter + Qwen for better accuracy!"
        layout.addView(resultText)
        
        setContentView(layout)
        checkPermissions()
        testApiConnection()
    }

    private fun setupApiService() {
        val retrofit = Retrofit.Builder()
            .baseUrl("http://10.0.2.2:8000/")
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        
        apiService = retrofit.create(ApiService::class.java)
        enhancedOcrProcessor = EnhancedOcrProcessor(apiService!!)
    }

    private fun checkPermissions() {
        val permissions = arrayOf(
            android.Manifest.permission.CAMERA,
            android.Manifest.permission.READ_EXTERNAL_STORAGE
        )

        val notGranted = permissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }

        if (notGranted.isNotEmpty()) {
            requestPermissionLauncher.launch(notGranted.toTypedArray())
        } else {
            statusText.text = "Permissions granted! Ready to capture images with enhanced OCR"
        }
    }

    private fun checkPermissionsAndPickImage(fromCamera: Boolean) {
        if (fromCamera) {
            ImagePicker.with(this)
                .cameraOnly()
                .crop()
                .compress(1024)
                .maxResultSize(1080, 1080)
                .createIntent { intent ->
                    imagePickerLauncher.launch(intent)
                }
        } else {
            ImagePicker.with(this)
                .galleryOnly()
                .crop()
                .compress(1024)
                .maxResultSize(1080, 1080)
                .createIntent { intent ->
                    imagePickerLauncher.launch(intent)
                }
        }
    }

    private fun testApiConnection() {
        apiText.text = "FastAPI Backend: http://10.0.2.2:8000\nStatus: Testing Connection..."
        
        uiScope.launch {
            try {
                val response = apiService?.checkHealth()
                if (response?.isSuccessful == true) {
                    val healthData = response.body()
                    apiText.text = "FastAPI Backend: http://10.0.2.2:8000\nStatus: ✅ Connected Successfully\nVersion: ${healthData?.get("version") ?: "1.0.0"}"
                    statusText.text = "✅ API connection successful!\n✅ Enhanced OCR service ready!\n✅ OpenRouter/Qwen integration active!"
                    Toast.makeText(this@EnhancedMainActivity, "Enhanced OCR system ready!", Toast.LENGTH_LONG).show()
                } else {
                    apiText.text = "FastAPI Backend: http://10.0.2.2:8000\nStatus: ⚠️ Connection Failed (${response?.code()})"
                    statusText.text = "⚠️ API connection failed. Enhanced OCR unavailable."
                }
            } catch (e: Exception) {
                apiText.text = "FastAPI Backend: http://10.0.2.2:8000\nStatus: ❌ Error - ${e.message}"
                statusText.text = "❌ Connection error: ${e.message}"
            }
        }
    }

    private fun testOpenRouterConnection() {
        uiScope.launch {
            try {
                val response = apiService?.checkHealth()
                if (response?.isSuccessful == true) {
                    statusText.text = "✅ OpenRouter/Qwen integration working!\nReady for enhanced OCR processing"
                    Toast.makeText(this@EnhancedMainActivity, "OpenRouter test successful!", Toast.LENGTH_SHORT).show()
                } else {
                    statusText.text = "⚠️ OpenRouter connection failed. Will use fallback OCR."
                    Toast.makeText(this@EnhancedMainActivity, "OpenRouter unavailable, using fallback", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                statusText.text = "⚠️ OpenRouter test error: ${e.message}"
            }
        }
    }

    private fun processImageWithEnhancedOCR() {
        selectedBitmap?.let { bitmap ->
            statusText.text = "Processing with enhanced OCR (OpenRouter + Qwen)..."
            btnProcessOcr.isEnabled = false
            
            uiScope.launch {
                try {
                    val result = enhancedOcrProcessor?.processImageWithFallback(bitmap, enhancementLevel)
                    
                    val resultTextBuilder = StringBuilder()
                    resultTextBuilder.append("Enhanced OCR Results:\n\n")
                    
                    if (result?.success == true) {
                        // Processing info
                        resultTextBuilder.append("Processing Method: ${result.enhancementLevel}\n")
                        val openRouterText = if (result.openrouterUsed) "✅ Yes" else "❌ No (fallback)"
                        resultTextBuilder.append("OpenRouter Used: $openRouterText\n")
                        resultTextBuilder.append("Confidence Score: ${String.format("%.2f", result.confidenceScore * 100)}%\n")
                        resultTextBuilder.append("Processing Time: ${result.processingTimeMs}ms\n\n")
                        
                        // Raw text
                        resultTextBuilder.append("Raw Extracted Text:\n${result.rawText}\n\n")
                        
                        // Menu items
                        resultTextBuilder.append("Menu Items (${result.menuItems.size}):\n")
                        result.menuItems.forEachIndexed { index, item ->
                            resultTextBuilder.append("${index + 1}. ${item.name}")
                            if (item.price != null) {
                                resultTextBuilder.append(" - ${item.price}")
                            }
                            resultTextBuilder.append("\n")
                            if (item.description != null) {
                                resultTextBuilder.append("   ${item.description}\n")
                            }
                            if (item.category != null) {
                                resultTextBuilder.append("   Category: ${item.category}\n")
                            }
                        }
                        
                        statusText.text = "✅ Enhanced OCR completed successfully!\n${result.menuItems.size} items found in ${result.processingTimeMs}ms"
                        
                    } else {
                        resultTextBuilder.append("Enhanced OCR Error:\n${result?.errorMessage ?: "Unknown error"}")
                        statusText.text = "❌ Enhanced OCR failed: ${result?.errorMessage ?: "Unknown error"}"
                    }
                    
                    resultText.text = resultTextBuilder.toString()
                    
                    if (result?.success == true) {
                        Toast.makeText(this@EnhancedMainActivity, "Enhanced OCR completed!", Toast.LENGTH_SHORT).show()
                    } else {
                        Toast.makeText(this@EnhancedMainActivity, "Enhanced OCR failed", Toast.LENGTH_SHORT).show()
                    }
                    
                } catch (e: Exception) {
                    resultText.text = "Enhanced OCR Error: ${e.message}"
                    statusText.text = "❌ Enhanced OCR processing error: ${e.message}"
                    Toast.makeText(this@EnhancedMainActivity, "Error: ${e.message}", Toast.LENGTH_LONG).show()
                } finally {
                    btnProcessOcr.isEnabled = true
                }
            }
        } ?: run {
            Toast.makeText(this, "Please select an image first", Toast.LENGTH_SHORT).show()
        }
    }

    private fun bitmapToBase64(bitmap: android.graphics.Bitmap): String {
        val byteArrayOutputStream = ByteArrayOutputStream()
        bitmap.compress(android.graphics.Bitmap.CompressFormat.JPEG, 80, byteArrayOutputStream)
        val byteArray = byteArrayOutputStream.toByteArray()
        return Base64.encodeToString(byteArray, Base64.NO_WRAP)
    }
}