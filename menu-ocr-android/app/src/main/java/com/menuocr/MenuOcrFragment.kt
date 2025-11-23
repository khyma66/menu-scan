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
    private lateinit var imagePreviewCard: androidx.cardview.widget.CardView
    private lateinit var imagePreview: ImageView
    private lateinit var imageStatus: TextView
    private lateinit var btnProcessOcr: Button
    private lateinit var loadingProgress: LinearLayout
    private lateinit var resultsCard: androidx.cardview.widget.CardView
    private lateinit var ocrResults: TextView
    private lateinit var actionButtons: LinearLayout

    private var selectedBitmap: Bitmap? = null
    private var apiService: ApiService? = null
    private var enhancedOcrProcessor: EnhancedOcrProcessor? = null
    private val uiScope = CoroutineScope(Dispatchers.Main)
    private var enhancementLevel: String = "high"

    private val imagePickerLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == android.app.Activity.RESULT_OK) {
            result.data?.data?.let { uri ->
                selectedBitmap = BitmapFactory.decodeStream(requireContext().contentResolver.openInputStream(uri))
                showImagePreview()
                btnProcessOcr.visibility = View.VISIBLE
                Toast.makeText(requireContext(), "Image selected successfully", Toast.LENGTH_SHORT).show()
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
        imagePreviewCard = view.findViewById(R.id.image_preview_card)
        imagePreview = view.findViewById(R.id.image_preview)
        imageStatus = view.findViewById(R.id.image_status)
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
        val retrofit = Retrofit.Builder()
            .baseUrl("http://10.0.2.2:8000/")
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

        btnProcessOcr.setOnClickListener {
            processImageWithEnhancedOCR()
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

    private fun showImagePreview() {
        selectedBitmap?.let { bitmap ->
            imagePreview.setImageBitmap(bitmap)
            imagePreviewCard.visibility = View.VISIBLE
            imageStatus.text = "Image selected! Ready for OCR processing"
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
                    updateConnectionStatus("❌ Backend connection failed")
                }
            } catch (e: Exception) {
                updateConnectionStatus("❌ Connection error: ${e.message}")
            }
        }
    }

    private fun updateConnectionStatus(message: String) {
        connectionStatus.text = message
    }

    private fun processImageWithEnhancedOCR() {
        selectedBitmap?.let { bitmap ->
            // Show loading
            loadingProgress.visibility = View.VISIBLE
            btnProcessOcr.isEnabled = false
            resultsCard.visibility = View.GONE
            actionButtons.visibility = View.GONE

            uiScope.launch {
                try {
                    val result = enhancedOcrProcessor?.processImageWithFallback(bitmap, enhancementLevel)

                    val resultTextBuilder = StringBuilder()

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

                        // Show results
                        ocrResults.text = resultTextBuilder.toString()
                        resultsCard.visibility = View.VISIBLE
                        actionButtons.visibility = View.VISIBLE

                        Toast.makeText(requireContext(), "OCR completed successfully!", Toast.LENGTH_SHORT).show()
                    } else {
                        ocrResults.text = "OCR Error:\n${result?.errorMessage ?: "Unknown error"}"
                        resultsCard.visibility = View.VISIBLE
                        Toast.makeText(requireContext(), "OCR failed", Toast.LENGTH_SHORT).show()
                    }

                } catch (e: Exception) {
                    ocrResults.text = "OCR Error: ${e.message}"
                    resultsCard.visibility = View.VISIBLE
                    Toast.makeText(requireContext(), "Error: ${e.message}", Toast.LENGTH_LONG).show()
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