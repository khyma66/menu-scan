package com.menuocr

import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.os.Bundle
import android.util.Base64
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.*
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import com.github.dhaval2404.imagepicker.ImagePicker
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.io.ByteArrayOutputStream

class MenuOcrFragment : Fragment() {

    private lateinit var connectionStatus: TextView
    private lateinit var btnCaptureImage: Button
    private lateinit var btnSelectGallery: Button
    private lateinit var imagesPreviewCard: androidx.cardview.widget.CardView
    private lateinit var selectedImagesContainer: LinearLayout
    private lateinit var btnAddMoreImages: Button
    private lateinit var btnProcessOcr: Button
    private lateinit var loadingProgress: LinearLayout
    private lateinit var resultsCard: androidx.cardview.widget.CardView
    private lateinit var ocrResults: TextView
    private lateinit var actionButtons: LinearLayout

    private var selectedBitmaps: MutableList<Bitmap> = mutableListOf()
    private var apiService: ApiService? = null
    private var enhancedOcrProcessor: EnhancedOcrProcessor? = null
    private val uiScope = CoroutineScope(Dispatchers.Main)
    private var enhancementLevel: String = "high"

    private val imagePickerLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == android.app.Activity.RESULT_OK) {
            result.data?.data?.let { uri ->
                val bitmap = BitmapFactory.decodeStream(requireContext().contentResolver.openInputStream(uri))
                selectedBitmaps.add(bitmap)
                showImagesPreview()
                btnProcessOcr.visibility = View.VISIBLE
                Toast.makeText(requireContext(), "Image added successfully", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val allGranted = permissions.values.all { it }
        if (allGranted) {
            updateConnectionStatus("Permissions granted! Ready to capture images")
        } else {
            updateConnectionStatus("Permissions required for camera and gallery access")
        }
    }

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_menu_ocr, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        // Initialize views
        connectionStatus = view.findViewById(R.id.connection_status)
        btnCaptureImage = view.findViewById(R.id.btn_capture_image)
        btnSelectGallery = view.findViewById(R.id.btn_select_gallery)
        imagesPreviewCard = view.findViewById(R.id.images_preview_card)
        selectedImagesContainer = view.findViewById(R.id.selected_images_container)
        btnAddMoreImages = view.findViewById(R.id.btn_add_more_images)
        btnProcessOcr = view.findViewById(R.id.btn_process_ocr)
        loadingProgress = view.findViewById(R.id.loading_progress)
        resultsCard = view.findViewById(R.id.results_card)
        ocrResults = view.findViewById(R.id.ocr_results)
        actionButtons = view.findViewById(R.id.action_buttons)

        setupApiService()
        setupClickListeners()
        checkPermissions()
        testApiConnection()
    }

    private fun setupApiService() {
        // Always use local backend for testing - change to production URL when deploying
        val baseUrl = "http://10.0.2.2:8000/"  // Emulator localhost

        val okHttpClient = okhttp3.OkHttpClient.Builder()
            .connectTimeout(10, java.util.concurrent.TimeUnit.SECONDS)
            .readTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
            .writeTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
            .build()

        val retrofit = Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()

        apiService = retrofit.create(ApiService::class.java)
        enhancedOcrProcessor = EnhancedOcrProcessor(apiService!!)
    }

    private fun setupClickListeners() {
        btnCaptureImage.setOnClickListener {
            checkPermissionsAndPickImage(true)
        }

        btnSelectGallery.setOnClickListener {
            checkPermissionsAndPickImage(false)
        }

        btnAddMoreImages.setOnClickListener {
            checkPermissionsAndPickImage(false) // Default to gallery for adding more
        }

        btnProcessOcr.setOnClickListener {
            processImagesWithEnhancedOCR()
        }
    }

    private fun checkPermissions() {
        val permissions = arrayOf(
            android.Manifest.permission.CAMERA,
            android.Manifest.permission.READ_EXTERNAL_STORAGE
        )

        val notGranted = permissions.filter {
            ContextCompat.checkSelfPermission(requireContext(), it) != PackageManager.PERMISSION_GRANTED
        }

        if (notGranted.isNotEmpty()) {
            requestPermissionLauncher.launch(notGranted.toTypedArray())
        } else {
            updateConnectionStatus("✅ Permissions granted! Ready to capture images")
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

    private fun showImagesPreview() {
        if (selectedBitmaps.isNotEmpty()) {
            selectedImagesContainer.removeAllViews()

            selectedBitmaps.forEachIndexed { index, bitmap ->
                val imageView = ImageView(requireContext()).apply {
                    layoutParams = LinearLayout.LayoutParams(100, 100).apply {
                        marginEnd = 8
                    }
                    setImageBitmap(bitmap)
                    scaleType = android.widget.ImageView.ScaleType.CENTER_CROP
                    background = android.graphics.drawable.ColorDrawable(android.graphics.Color.LTGRAY)
                    setPadding(4, 4, 4, 4)
                }
                selectedImagesContainer.addView(imageView)
            }

            imagesPreviewCard.visibility = View.VISIBLE
            btnAddMoreImages.visibility = View.VISIBLE
        }
    }

    private fun testApiConnection() {
        updateConnectionStatus("🔄 Testing backend connection...")

        uiScope.launch {
            try {
                val response = apiService?.checkHealth()
                if (response?.isSuccessful == true) {
                    val healthData = response.body()
                    updateConnectionStatus("✅ Backend connected - Ready to process")
                } else {
                    updateConnectionStatus("⚠️ Backend not available - Check connection")
                }
            } catch (e: Exception) {
                updateConnectionStatus("⚠️ Connection error - Will retry when processing")
                // Don't crash the app, just show warning
                android.util.Log.w("MenuOcrFragment", "Backend connection failed: ${e.message}")
            }
        }
    }

    private fun updateConnectionStatus(message: String) {
        connectionStatus.text = message
    }

    private fun processImagesWithEnhancedOCR() {
        if (selectedBitmaps.isEmpty()) {
            Toast.makeText(requireContext(), "Please select at least one image first", Toast.LENGTH_SHORT).show()
            return
        }

        // Show loading
        loadingProgress.visibility = View.VISIBLE
        btnProcessOcr.isEnabled = false
        resultsCard.visibility = View.GONE
        actionButtons.visibility = View.GONE

        uiScope.launch {
            try {
                val allMenuItems = mutableListOf<MenuItem>()
                val allRawText = StringBuilder()
                var totalProcessingTime = 0L

                // Process each image
                selectedBitmaps.forEachIndexed { index, bitmap ->
                    try {
                        // Convert bitmap to base64
                        val byteArrayOutputStream = ByteArrayOutputStream()
                        bitmap.compress(android.graphics.Bitmap.CompressFormat.JPEG, 90, byteArrayOutputStream)
                        val imageBytes = byteArrayOutputStream.toByteArray()

                        // Create multipart request
                        val requestBody = okhttp3.RequestBody.create("image/jpeg".toMediaType(), imageBytes)
                        val imagePart = okhttp3.MultipartBody.Part.createFormData("image", "menu_image_$index.jpg", requestBody)
                        val enhancementLevelBody = okhttp3.RequestBody.create("text/plain".toMediaType(), "high")

                        val response = apiService?.processEnhancedOcrUpload(imagePart, enhancementLevelBody)

                        if (response?.isSuccessful == true) {
                            response.body()?.let { menuResponse ->
                                if (menuResponse.success) {
                                    // Add image separator
                                    if (index > 0) allRawText.append("\n\n--- Image ${index + 1} ---\n\n")
                                    allRawText.append(menuResponse.raw_text)

                                    // Add menu items with image reference
                                    menuResponse.menu_items.forEach { item ->
                                        allMenuItems.add(item.copy(
                                            name = "${item.name} (Image ${index + 1})"
                                        ))
                                    }

                                    totalProcessingTime += menuResponse.processing_time_ms
                                }
                            }
                        } else {
                            android.util.Log.w("MenuOcrFragment", "Failed to process image $index: ${response?.message()}")
                        }
                    } catch (e: Exception) {
                        android.util.Log.e("MenuOcrFragment", "Error processing image $index", e)
                    }
                }

                // Build results
                val resultTextBuilder = StringBuilder()
                resultTextBuilder.append("Processing Method: Enhanced OCR with Qwen (${selectedBitmaps.size} images)\n")
                resultTextBuilder.append("Total Processing Time: ${totalProcessingTime}ms\n\n")

                // Raw text from all images
                resultTextBuilder.append("Raw Extracted Text:\n${allRawText.toString()}\n\n")

                // Combined menu items
                resultTextBuilder.append("Combined Menu Items (${allMenuItems.size}):\n")
                allMenuItems.forEachIndexed { index, item ->
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

                // Show results
                ocrResults.text = resultTextBuilder.toString()
                resultsCard.visibility = View.VISIBLE
                actionButtons.visibility = View.VISIBLE

                Toast.makeText(requireContext(), "OCR completed for ${selectedBitmaps.size} images!", Toast.LENGTH_SHORT).show()

            } catch (e: Exception) {
                android.util.Log.e("MenuOcrFragment", "OCR processing failed", e)
                ocrResults.text = "OCR Error: ${e.localizedMessage ?: e.message ?: "Unknown error"}"
                resultsCard.visibility = View.VISIBLE
                Toast.makeText(requireContext(), "Processing failed: ${e.localizedMessage ?: "Check connection"}", Toast.LENGTH_LONG).show()
            } finally {
                // Hide loading
                loadingProgress.visibility = View.GONE
                btnProcessOcr.isEnabled = true
            }
        }
    }
            // Show loading
            loadingProgress.visibility = View.VISIBLE
            btnProcessOcr.isEnabled = false
            resultsCard.visibility = View.GONE
            actionButtons.visibility = View.GONE

            uiScope.launch {
                try {
                    // Convert bitmap to base64
                    val byteArrayOutputStream = ByteArrayOutputStream()
                    bitmap.compress(android.graphics.Bitmap.CompressFormat.JPEG, 90, byteArrayOutputStream)
                    val imageBase64 = android.util.Base64.encodeToString(byteArrayOutputStream.toByteArray(), android.util.Base64.DEFAULT)

                    // Create OCR request
                    val ocrRequest = OcrRequest(
                        image_base64 = imageBase64,
                        language = "auto"
                    )

                    // Call enhanced OCR endpoint using multipart upload
                    val imageBytes = android.util.Base64.decode(ocrRequest.image_base64, android.util.Base64.DEFAULT)
                    val requestBody = okhttp3.RequestBody.create("image/jpeg".toMediaType(), imageBytes)
                    val imagePart = okhttp3.MultipartBody.Part.createFormData("image", "menu_image.jpg", requestBody)
                    val enhancementLevelBody = okhttp3.RequestBody.create("text/plain".toMediaType(), "high")

                    val response = apiService?.processEnhancedOcrUpload(imagePart, enhancementLevelBody)

                    val resultTextBuilder = StringBuilder()

                    if (response?.isSuccessful == true) {
                        response.body()?.let { menuResponse ->
                            if (menuResponse.success) {
                                // Processing info
                                resultTextBuilder.append("Processing Method: Regular OCR\n")
                                resultTextBuilder.append("Language: ${menuResponse.metadata?.get("detected_language") ?: "auto"}\n")
                                resultTextBuilder.append("Processing Time: ${menuResponse.processing_time_ms}ms\n\n")

                                // Raw text
                                resultTextBuilder.append("Raw Extracted Text:\n${menuResponse.raw_text}\n\n")

                                // Menu items
                                resultTextBuilder.append("Menu Items (${menuResponse.menu_items.size}):\n")
                                menuResponse.menu_items.forEachIndexed { index, item ->
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

                                // Show results
                                ocrResults.text = resultTextBuilder.toString()
                                resultsCard.visibility = View.VISIBLE
                                actionButtons.visibility = View.VISIBLE

                                Toast.makeText(requireContext(), "OCR completed successfully!", Toast.LENGTH_SHORT).show()
                            } else {
                                ocrResults.text = "OCR Error: Processing failed"
                                resultsCard.visibility = View.VISIBLE
                                Toast.makeText(requireContext(), "OCR failed", Toast.LENGTH_SHORT).show()
                            }
                        } ?: run {
                            ocrResults.text = "OCR Error: Empty response"
                            resultsCard.visibility = View.VISIBLE
                        }
                    } else {
                        ocrResults.text = "OCR Error: HTTP ${response?.code()} - ${response?.message()}"
                        resultsCard.visibility = View.VISIBLE
                        Toast.makeText(requireContext(), "OCR failed: ${response?.message()}", Toast.LENGTH_SHORT).show()
                    }

                } catch (e: Exception) {
                    android.util.Log.e("MenuOcrFragment", "OCR processing failed", e)
                    ocrResults.text = "OCR Error: ${e.localizedMessage ?: e.message ?: "Unknown error"}"
                    resultsCard.visibility = View.VISIBLE
                    Toast.makeText(requireContext(), "Processing failed: ${e.localizedMessage ?: "Check connection"}", Toast.LENGTH_LONG).show()
                } finally {
                    // Hide loading
                    loadingProgress.visibility = View.GONE
                    btnProcessOcr.isEnabled = true
                }
            }
        } ?: run {
            Toast.makeText(requireContext(), "Please select an image first", Toast.LENGTH_SHORT).show()
        }
    }
}