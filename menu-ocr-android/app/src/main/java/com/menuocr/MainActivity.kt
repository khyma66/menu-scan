package com.menuocr

import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.BitmapFactory
import android.os.Bundle
import android.util.Base64
import android.view.View
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
import kotlinx.coroutines.withContext
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.io.ByteArrayOutputStream

class MainActivity : AppCompatActivity() {

    private lateinit var btnCaptureImage: Button
    private lateinit var btnSelectImage: Button
    private lateinit var btnProcessOcr: Button
    private lateinit var imageView: ImageView
    private lateinit var statusText: TextView
    private lateinit var apiText: TextView
    private lateinit var resultText: TextView
    
    private var selectedBitmap: android.graphics.Bitmap? = null
    private var apiService: ApiService? = null
    private val uiScope = CoroutineScope(Dispatchers.Main)

    private val imagePickerLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == RESULT_OK) {
            result.data?.data?.let { uri ->
                selectedBitmap = BitmapFactory.decodeStream(contentResolver.openInputStream(uri))
                imageView.setImageBitmap(selectedBitmap)
                statusText.text = "Image selected! Ready for OCR processing"
                btnProcessOcr.isEnabled = true
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
        
        // Create simple layout programmatically
        val layout = android.widget.LinearLayout(this)
        layout.orientation = android.widget.LinearLayout.VERTICAL
        layout.setPadding(16, 16, 16, 16)
        
        // Title
        val titleText = TextView(this)
        titleText.text = "Menu OCR - Enhanced Version"
        titleText.textSize = 24f
        titleText.setPadding(0, 0, 0, 16)
        layout.addView(titleText)
        
        // API status
        apiText = TextView(this)
        apiText.text = "FastAPI Backend: http://10.0.2.2:8000\nStatus: Initializing..."
        apiText.setPadding(0, 0, 0, 16)
        layout.addView(apiText)
        
        // Status text
        statusText = TextView(this)
        statusText.text = "Ready to test OCR functionality"
        statusText.setPadding(0, 0, 0, 16)
        layout.addView(statusText)
        
        // Buttons
        btnCaptureImage = Button(this)
        btnCaptureImage.text = "Capture Image"
        btnCaptureImage.setOnClickListener {
            checkPermissionsAndPickImage(true)
        }
        layout.addView(btnCaptureImage)
        
        btnSelectImage = Button(this)
        btnSelectImage.text = "Select from Gallery"
        btnSelectImage.setOnClickListener {
            checkPermissionsAndPickImage(false)
        }
        layout.addView(btnSelectImage)
        
        btnProcessOcr = Button(this)
        btnProcessOcr.text = "Process with OCR"
        btnProcessOcr.isEnabled = false
        btnProcessOcr.setOnClickListener {
            processImageWithOCR()
        }
        layout.addView(btnProcessOcr)
        
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
        resultText.text = "OCR Results will appear here..."
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
            statusText.text = "Permissions already granted! Ready to capture images"
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
                    statusText.text = "✅ API connection test successful!\n✅ Backend is healthy!\n✅ Android app integration ready!"
                    Toast.makeText(this@MainActivity, "API test completed successfully!", Toast.LENGTH_LONG).show()
                } else {
                    apiText.text = "FastAPI Backend: http://10.0.2.2:8000\nStatus: ⚠️ Connection Failed (${response?.code()})"
                    statusText.text = "⚠️ API connection failed with code: ${response?.code()}\nMake sure backend is running on port 8000"
                }
            } catch (e: Exception) {
                apiText.text = "FastAPI Backend: http://10.0.2.2:8000\nStatus: ❌ Error - ${e.message}"
                statusText.text = "❌ Connection error: ${e.message}\n\nPlease ensure:\n1. Backend is running on localhost:8000\n2. Emulator can access host via 10.0.2.2:8000"
                Toast.makeText(this@MainActivity, "Connection error: ${e.message}", Toast.LENGTH_LONG).show()
            }
        }
    }

    private fun processImageWithOCR() {
        selectedBitmap?.let { bitmap ->
            statusText.text = "Processing image with OCR..."
            btnProcessOcr.isEnabled = false
            
            uiScope.launch {
                try {
                    // Convert bitmap to base64
                    val base64Image = bitmapToBase64(bitmap)
                    
                    // Create OCR request
                    val ocrRequest = OcrRequest(
                        image_base64 = base64Image,
                        language = "en"
                    )
                    
                    // Send to FastAPI backend
                    val response = apiService?.processOcr(ocrRequest)
                    
                    if (response?.isSuccessful == true) {
                        val menuResponse = response.body()
                        val resultTextBuilder = StringBuilder()
                        resultTextBuilder.append("OCR Results:\n\n")
                        resultTextBuilder.append("Raw Text:\n${menuResponse?.raw_text ?: "No text detected"}\n\n")
                        resultTextBuilder.append("Menu Items (${menuResponse?.menu_items?.size ?: 0}):\n")
                        menuResponse?.menu_items?.forEachIndexed { index, item ->
                            resultTextBuilder.append("${index + 1}. ${item.name}")
                            if (item.price != null) {
                                resultTextBuilder.append(" - ${item.price}")
                            }
                            resultTextBuilder.append("\n")
                            if (item.description != null) {
                                resultTextBuilder.append("   ${item.description}\n")
                            }
                        }
                        resultText.text = resultTextBuilder.toString()
                        statusText.text = "✅ OCR processing completed successfully! (${menuResponse?.processing_time_ms ?: 0}ms)"
                        Toast.makeText(this@MainActivity, "OCR processed successfully!", Toast.LENGTH_SHORT).show()
                    } else {
                        resultText.text = "OCR Error: Failed to process image (${response?.code()})"
                        statusText.text = "❌ OCR processing failed with code: ${response?.code()}"
                        Toast.makeText(this@MainActivity, "OCR processing failed", Toast.LENGTH_SHORT).show()
                    }
                } catch (e: Exception) {
                    resultText.text = "OCR Error: ${e.message}"
                    statusText.text = "❌ OCR processing error: ${e.message}"
                    Toast.makeText(this@MainActivity, "Error: ${e.message}", Toast.LENGTH_LONG).show()
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