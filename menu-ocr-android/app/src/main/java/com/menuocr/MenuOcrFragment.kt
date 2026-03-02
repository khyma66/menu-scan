package com.menuocr

import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Bundle
import android.provider.MediaStore
import android.util.Log
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.AdapterView
import android.widget.ArrayAdapter
import android.widget.*
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import com.github.dhaval2404.imagepicker.ImagePicker
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.tasks.await
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.ByteArrayOutputStream

class MenuOcrFragment : Fragment() {
    companion object {
        private const val MENU_TABLE_PROMPT = "Get menu details in a table format extracting the dish, its price and any other info (if ingredients) and for each dish get - taste (overall sweet/tangy/hot etc.) in English"
        private const val HEALTH_PREFS = "health_profile_cache"
        private const val KEY_HEALTH_CONDITIONS = "health_conditions"
        private const val KEY_ALLERGIES = "allergies"
        private const val KEY_DIETARY_PREFERENCES = "dietary_preferences"
        private const val KEY_TASTE_PREFERENCES = "taste_preferences"
    }

    private lateinit var btnCaptureImage: Button
    private lateinit var btnSelectGallery: Button
    private lateinit var imagesPreviewCard: androidx.cardview.widget.CardView
    private lateinit var selectedImagesContainer: LinearLayout
    private lateinit var btnAddMoreImages: Button
    private lateinit var btnProcessOcr: Button
    private lateinit var loadingProgress: LinearLayout
    private lateinit var resultsCard: LinearLayout
    private lateinit var ocrResults: TextView
    private lateinit var geminiDishLinksContainer: LinearLayout
    private lateinit var qwenDetailCard: LinearLayout
    private lateinit var btnBackToDishes: Button
    private lateinit var detailDishName: TextView
    private lateinit var detailPrice: TextView
    private lateinit var detailDescription: TextView
    private lateinit var detailIngredients: TextView
    private lateinit var detailTaste: TextView
    private lateinit var detailSimilar: TextView
    private lateinit var detailRecommendation: TextView
    private lateinit var detailAllergens: TextView
    private lateinit var detailSpiciness: TextView
    private lateinit var detailPreparation: TextView
    private lateinit var actionButtons: LinearLayout
    private lateinit var scanLimitText: TextView
    private lateinit var switchTranslate: Switch
    private lateinit var spinnerTranslateLanguage: Spinner
    private lateinit var btnResetResults: Button
    private lateinit var btnAddMoreResults: Button

    private var selectedBitmaps: MutableList<Bitmap> = mutableListOf()
    private var apiService: ApiService? = null
    private val uiScope = CoroutineScope(Dispatchers.Main)
    
    // Accumulated menu items for the current processing batch
    private var accumulatedMenuItems: MutableList<MenuItem> = mutableListOf()
    private var originalEnglishMenuItems: MutableList<MenuItem> = mutableListOf()
    private var accumulatedGeminiItems: MutableList<MenuItem> = mutableListOf()
    private val translatedItemsCache: MutableMap<String, List<MenuItem>> = mutableMapOf()
    private var showRecommendationColumn: Boolean = false
    private var qwenEnhancementRunning: Boolean = false
    private var processingCancelled: Boolean = false

    private val languageCodeByLabel = linkedMapOf(
        "Spanish" to "es",
        "French" to "fr",
        "German" to "de",
        "Italian" to "it",
        "Hindi" to "hi",
        "Telugu" to "te",
        "Tamil" to "ta",
        "Japanese" to "ja",
        "Chinese" to "zh"
    )

    private val emptyLikeTokens = setOf("null", "none", "n/a", "na", "unknown", "-", "--", "nil")
    
    private val imagePickerLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == android.app.Activity.RESULT_OK) {
            result.data?.data?.let { uri ->
                val bitmap = BitmapFactory.decodeStream(requireContext().contentResolver.openInputStream(uri))
                selectedBitmaps.add(bitmap)
                showImagesPreview()
                btnProcessOcr.visibility = View.VISIBLE
                animateProcessButton()
                Toast.makeText(requireContext(), "Image added successfully", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val allGranted = permissions.values.all { it }
        if (!allGranted) {
            Toast.makeText(requireContext(), "Permissions required for camera and gallery access", Toast.LENGTH_LONG).show()
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
        btnCaptureImage = view.findViewById(R.id.btn_capture_image)
        btnSelectGallery = view.findViewById(R.id.btn_select_gallery)
        imagesPreviewCard = view.findViewById(R.id.images_preview_card)
        selectedImagesContainer = view.findViewById(R.id.selected_images_container)
        btnAddMoreImages = view.findViewById(R.id.btn_add_more_images)
        btnProcessOcr = view.findViewById(R.id.btn_process_ocr)
        loadingProgress = view.findViewById(R.id.loading_progress)
        resultsCard = view.findViewById(R.id.results_card)
        ocrResults = view.findViewById(R.id.ocr_results)
        geminiDishLinksContainer = view.findViewById(R.id.gemini_dish_links_container)
        qwenDetailCard = view.findViewById(R.id.qwen_detail_card)
        btnBackToDishes = view.findViewById(R.id.btn_back_to_dishes)
        detailDishName = view.findViewById(R.id.detail_dish_name)
        detailPrice = view.findViewById(R.id.detail_price)
        detailDescription = view.findViewById(R.id.detail_description)
        detailIngredients = view.findViewById(R.id.detail_ingredients)
        detailTaste = view.findViewById(R.id.detail_taste)
        detailSimilar = view.findViewById(R.id.detail_similar)
        detailRecommendation = view.findViewById(R.id.detail_recommendation)
        detailAllergens = view.findViewById(R.id.detail_allergens)
        detailSpiciness = view.findViewById(R.id.detail_spiciness)
        detailPreparation = view.findViewById(R.id.detail_preparation)
        actionButtons = view.findViewById(R.id.action_buttons)
        switchTranslate = view.findViewById(R.id.switch_translate)
        spinnerTranslateLanguage = view.findViewById(R.id.spinner_translate_language)
        btnResetResults = view.findViewById(R.id.btn_reset_results)
        btnAddMoreResults = view.findViewById(R.id.btn_add_more_results)

        setupApiService()
        setupTranslationControls()
        setupClickListeners()
        checkPermissions()
        syncPlanTierFromBackend()

        // Animate content on load
        animateContent()
        
    }

    private fun setupApiService() {
        apiService = ApiClient.getApiService()
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
            processImagesWithMLKitAndAPI()
        }

        btnResetResults.setOnClickListener {
            clearResultsTable()
            Toast.makeText(requireContext(), "Output table reset", Toast.LENGTH_SHORT).show()
        }

        btnAddMoreResults.setOnClickListener {
            checkPermissionsAndPickImage(false)
        }

        btnBackToDishes.setOnClickListener {
            qwenDetailCard.visibility = View.GONE
            geminiDishLinksContainer.visibility = View.VISIBLE
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
        }
    }

    private fun checkPermissionsAndPickImage(fromCamera: Boolean) {
        if (fromCamera) {
            ImagePicker.with(this)
                .cameraOnly()
                .compress(4096)
                .maxResultSize(2160, 2160)
                .createIntent { intent ->
                    imagePickerLauncher.launch(intent)
                }
        } else {
            ImagePicker.with(this)
                .galleryOnly()
                .compress(4096)
                .maxResultSize(2160, 2160)
                .createIntent { intent ->
                    imagePickerLauncher.launch(intent)
                }
        }
    }

    private fun showImagesPreview() {
        if (selectedBitmaps.isNotEmpty()) {
            selectedImagesContainer.removeAllViews()
            val density = resources.displayMetrics.density
            val thumbSizePx = (100 * density).toInt()
            val marginPx = (8 * density).toInt()

            selectedBitmaps.forEachIndexed { index, bitmap ->
                val frame = FrameLayout(requireContext()).apply {
                    layoutParams = LinearLayout.LayoutParams(thumbSizePx, thumbSizePx).apply {
                        marginEnd = marginPx
                    }
                }

                val imageView = ImageView(requireContext()).apply {
                    layoutParams = FrameLayout.LayoutParams(
                        FrameLayout.LayoutParams.MATCH_PARENT,
                        FrameLayout.LayoutParams.MATCH_PARENT
                    )
                    setImageBitmap(bitmap)
                    scaleType = android.widget.ImageView.ScaleType.CENTER_CROP
                    background = android.graphics.drawable.ColorDrawable(android.graphics.Color.LTGRAY)
                    setPadding(4, 4, 4, 4)
                }

                val removeButton = TextView(requireContext()).apply {
                    val btnSize = (28 * resources.displayMetrics.density).toInt()
                    layoutParams = FrameLayout.LayoutParams(btnSize, btnSize,
                        Gravity.END or Gravity.TOP
                    ).apply {
                        topMargin = (-4 * resources.displayMetrics.density).toInt()
                        rightMargin = (-4 * resources.displayMetrics.density).toInt()
                    }
                    text = "✕"
                    textSize = 16f
                    gravity = Gravity.CENTER
                    setTextColor(android.graphics.Color.WHITE)
                    val shape = android.graphics.drawable.GradientDrawable()
                    shape.shape = android.graphics.drawable.GradientDrawable.OVAL
                    shape.setColor(android.graphics.Color.parseColor("#EF4444"))
                    shape.setStroke((2 * resources.displayMetrics.density).toInt(), android.graphics.Color.WHITE)
                    background = shape
                    elevation = 4f
                    setOnClickListener {
                        if (index in selectedBitmaps.indices) {
                            selectedBitmaps.removeAt(index)
                            showImagesPreview()
                            if (selectedBitmaps.isEmpty()) {
                                imagesPreviewCard.visibility = View.GONE
                                btnProcessOcr.visibility = View.GONE
                                btnAddMoreImages.visibility = View.GONE
                            }
                        }
                    }
                }

                frame.addView(imageView)
                frame.addView(removeButton)
                selectedImagesContainer.addView(frame)

            }

            imagesPreviewCard.visibility = View.VISIBLE
            btnAddMoreImages.visibility = View.VISIBLE
        }
    }

    private fun animateProcessButton() {
        btnProcessOcr.alpha = 1f
        btnProcessOcr.translationY = 0f
    }

    /**
     * Process selected images and ask backend Gemini flow to return menu details in table-friendly format.
     */
    private fun processImagesWithMLKitAndAPI() {
        if (selectedBitmaps.isEmpty()) {
            Toast.makeText(requireContext(), "Please select at least one image first", Toast.LENGTH_SHORT).show()
            return
        }

        // Check scan limits before processing
        uiScope.launch {
            val canScan = try {
                ScanLimitManager.canScan(requireContext())
            } catch (e: Exception) {
                true // Default to allowing scan if check fails
            }
            
            if (!canScan) {
                showUpgradeRequiredDialog()
                return@launch
            }
            
            // Increment scan count
            ScanLimitManager.incrementScanCount(requireContext())
            
            // Proceed with processing
            processImagesInternal()
        }
    }
    
    /**
     * Show dialog prompting user to login when scan limit is reached
     */
    private fun showLoginRequiredDialog() {
        android.app.AlertDialog.Builder(requireContext())
            .setTitle("Free Scan Limit Reached")
            .setMessage("You've used all ${ScanLimitManager.getFreeScansUsed(requireContext())} free scans. Please login to continue scanning menus.")
            .setPositiveButton("Login") { _, _ ->
                val intent = Intent(requireContext(), LoginActivity::class.java)
                startActivity(intent)
            }
            .setNegativeButton("Cancel") { dialog, _ ->
                dialog.dismiss()
            }
            .show()
    }

    private fun showUpgradeRequiredDialog() {
        android.app.AlertDialog.Builder(requireContext())
            .setTitle("Upgrade Required")
            .setMessage("Your 3 free scans are used.\n\nPro: Unlimited scans + Translation + Similar dishes + Ingredients\nMax: Unlimited scans + Ingredients + Recommendations")
            .setPositiveButton("Get Pro") { _, _ ->
                upgradePlan("PRO", ScanLimitManager.PlanTier.PRO)
            }
            .setNeutralButton("Get Max") { _, _ ->
                upgradePlan("MAX", ScanLimitManager.PlanTier.MAX)
            }
            .setNegativeButton("Cancel") { dialog, _ ->
                dialog.dismiss()
            }
            .show()
    }

    private fun syncPlanTierFromBackend() {
        uiScope.launch {
            try {
                val response = apiService?.getSubscriptionInfo()
                if (response?.isSuccessful == true && response.body() != null) {
                    val planName = response.body()!!.plan_name.uppercase()
                    val tier = when (planName) {
                        "PRO" -> ScanLimitManager.PlanTier.PRO
                        "MAX" -> ScanLimitManager.PlanTier.MAX
                        else -> ScanLimitManager.PlanTier.FREE
                    }
                    ScanLimitManager.setPlanTier(requireContext(), tier)
                }
            } catch (_: Exception) {
            }
        }
    }

    private fun upgradePlan(planName: String, tier: ScanLimitManager.PlanTier) {
        uiScope.launch {
            try {
                val response = apiService?.selectSubscriptionPlan(SelectSubscriptionPlanRequest(plan_name = planName))
                if (response?.isSuccessful == true) {
                    ScanLimitManager.setPlanTier(requireContext(), tier)
                    Toast.makeText(requireContext(), "$planName activated", Toast.LENGTH_SHORT).show()
                } else {
                    Toast.makeText(requireContext(), "Failed to activate $planName", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(requireContext(), "Upgrade failed: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }
    }
    
    /**
     * Internal method to process images after scan limit check
     */
    private fun processImagesInternal() {
        if (selectedBitmaps.isEmpty()) {
            Toast.makeText(requireContext(), "Please select at least one image first", Toast.LENGTH_SHORT).show()
            return
        }

        accumulatedMenuItems.clear()
        originalEnglishMenuItems.clear()
        accumulatedGeminiItems.clear()
        translatedItemsCache.clear()
        showRecommendationColumn = false
        qwenEnhancementRunning = false
        processingCancelled = false
        switchTranslate.isChecked = false
        spinnerTranslateLanguage.visibility = View.GONE

        loadingProgress.visibility = View.VISIBLE
        loadingProgress.alpha = 1f

        btnProcessOcr.isEnabled = false
        btnProcessOcr.text = "Cancel"
        btnProcessOcr.isEnabled = true
        btnProcessOcr.setOnClickListener {
            processingCancelled = true
            btnProcessOcr.isEnabled = false
            updateLoadingStatus("Cancelling...")
        }
        resultsCard.visibility = View.GONE
        actionButtons.visibility = View.GONE

        uiScope.launch {
            try {
                val imageBytesList = selectedBitmaps.map { bitmapToJpegBytes(it) }

                imageBytesList.forEachIndexed { index, imageBytes ->
                    if (processingCancelled) return@forEachIndexed
                    updateLoadingStatus("Reading dishes (image ${index + 1}/${imageBytesList.size})...")
                    val imagePart = bytesToMultipart(imageBytes, "menu_${index + 1}.jpg")
                    val useLlmEnhancement = "false".toRequestBody("text/plain".toMediaType())
                    val useQwenVision = "false".toRequestBody("text/plain".toMediaType())
                    val language = "auto".toRequestBody("text/plain".toMediaType())
                    val outputLanguage = "en".toRequestBody("text/plain".toMediaType())

                    val response = apiService?.processEnhancedOcrUpload(
                        image = imagePart,
                        useLlmEnhancement = useLlmEnhancement,
                        useQwenVision = useQwenVision,
                        language = language,
                        outputLanguage = outputLanguage
                    )

                    if (response?.isSuccessful == true && response.body() != null) {
                        val body = response.body()!!
                        val rawText = body.raw_text.orEmpty()

                        if (rawText.contains("Sample Menu", ignoreCase = true) || rawText.contains("Fallback text", ignoreCase = true)) {
                            throw IllegalStateException(
                                "Server returned fallback placeholder text. Please retry after backend restart."
                            )
                        }

                        val geminiItems = (body.gemini_menu_items ?: body.menu_items)
                            .orEmpty()
                            .map { sanitizeMenuItem(it) }
                            .filter { !it.name.isNullOrBlank() }
                        if (geminiItems.isNotEmpty()) {
                            accumulatedGeminiItems.addAll(geminiItems)
                        }
                    } else {
                        throw IllegalStateException("OCR processing failed on image ${index + 1}: ${response?.message() ?: "no response"}")
                    }
                }

                if (accumulatedGeminiItems.isEmpty()) {
                    throw IllegalStateException("No dishes found in response. Try a clearer image or different lighting.")
                }

                accumulatedMenuItems.clear()
                accumulatedMenuItems.addAll(accumulatedGeminiItems)
                originalEnglishMenuItems.clear()
                originalEnglishMenuItems.addAll(accumulatedGeminiItems)

                refreshResultsDisplay()
                Toast.makeText(requireContext(), "Dishes ready", Toast.LENGTH_SHORT).show()

                if (ScanLimitManager.canUseAdditionalDetails(requireContext())) {
                    startBackgroundQwenEnhancement(imageBytesList)
                } else {
                    Toast.makeText(requireContext(), "Free plan includes translation only. Upgrade for ingredients, similar dishes, and recommendations.", Toast.LENGTH_LONG).show()
                }

            } catch (e: Exception) {
                Log.e("MenuOcrFragment", "OCR processing failed", e)
                ocrResults.text = "OCR Error: ${e.localizedMessage ?: e.message ?: "Unknown error"}"
                resultsCard.visibility = View.VISIBLE
                Toast.makeText(requireContext(), "Processing failed: ${e.localizedMessage ?: "Check connection"}", Toast.LENGTH_LONG).show()
            } finally {
                loadingProgress.visibility = View.GONE

                btnProcessOcr.text = "Start Analysis"
                btnProcessOcr.isEnabled = true
                btnProcessOcr.setOnClickListener { processImagesWithMLKitAndAPI() }
                
                // Keep images visible above results for reference (user can add/remove)
                if (selectedBitmaps.isNotEmpty()) {
                    imagesPreviewCard.visibility = View.VISIBLE
                    btnAddMoreImages.visibility = View.VISIBLE
                    btnProcessOcr.visibility = View.VISIBLE
                    btnProcessOcr.text = "⚡ Re-analyze"
                } else {
                    imagesPreviewCard.visibility = View.GONE
                    btnProcessOcr.visibility = View.GONE
                }
            }
        }
    }

    private fun startBackgroundQwenEnhancement(imageBytesList: List<ByteArray>) {
        if (imageBytesList.isEmpty()) return
        if (qwenEnhancementRunning) return
        qwenEnhancementRunning = true

        uiScope.launch {
            val qwenMap = mutableMapOf<String, MenuItem>()
            try {
                loadingProgress.visibility = View.VISIBLE
                loadingProgress.alpha = 1f

                imageBytesList.forEachIndexed { index, imageBytes ->
                    updateLoadingStatus("Loading additional details (image ${index + 1}/${imageBytesList.size})...")
                    val imagePart = bytesToMultipart(imageBytes, "enhance_${index + 1}.jpg")
                    val useLlmEnhancement = "true".toRequestBody("text/plain".toMediaType())
                    val useQwenVision = "false".toRequestBody("text/plain".toMediaType())
                    val language = "auto".toRequestBody("text/plain".toMediaType())
                    val outputLanguage = "en".toRequestBody("text/plain".toMediaType())

                    val response = apiService?.processEnhancedOcrUpload(
                        image = imagePart,
                        useLlmEnhancement = useLlmEnhancement,
                        useQwenVision = useQwenVision,
                        language = language,
                        outputLanguage = outputLanguage
                    )

                    if (response?.isSuccessful == true && response.body() != null) {
                        val body = response.body()!!
                        val qwenItems = (body.qwen_menu_items ?: body.menu_items)
                            .orEmpty()
                            .map { sanitizeMenuItem(it) }
                            .filter { !it.name.isNullOrBlank() }

                        val healthProfile = body.metadata?.get("health_profile") as? Map<*, *>
                        val healthConditions = healthProfile?.get("health_conditions") as? List<*>
                        if (!healthConditions.isNullOrEmpty()) {
                            showRecommendationColumn = true
                        }

                        qwenItems.forEach { enhancedItem ->
                            qwenMap[itemKey(enhancedItem)] = enhancedItem
                        }

                        val merged = accumulatedGeminiItems.mapIndexed { itemIndex, geminiItem ->
                            val matchedEnhanced = qwenMap[itemKey(geminiItem)]
                                ?: qwenItems.firstOrNull {
                                    it.name?.trim()?.equals(geminiItem.name?.trim(), ignoreCase = true) == true
                                }
                                ?: qwenItems.getOrNull(itemIndex)

                            mergeGeminiAndEnhanced(geminiItem, matchedEnhanced)
                        }

                        accumulatedMenuItems.clear()
                        accumulatedMenuItems.addAll(merged)
                        originalEnglishMenuItems.clear()
                        originalEnglishMenuItems.addAll(merged)
                        if (switchTranslate.isChecked) {
                            val selectedLabel = spinnerTranslateLanguage.selectedItem?.toString()
                            val targetLanguage = languageCodeByLabel[selectedLabel] ?: "es"
                            requestTranslation(targetLanguage)
                        } else {
                            refreshResultsDisplay()
                        }
                    }
                }

                Toast.makeText(requireContext(), "Additional details ready", Toast.LENGTH_SHORT).show()

            } catch (e: Exception) {
                Log.w("MenuOcrFragment", "Qwen enhancement background processing failed", e)
                Toast.makeText(requireContext(), "Additional details delayed: ${e.localizedMessage ?: "retry later"}", Toast.LENGTH_SHORT).show()
            } finally {
                loadingProgress.visibility = View.GONE
                qwenEnhancementRunning = false
            }
        }
    }

    private fun bytesToMultipart(imageBytes: ByteArray, fileName: String): MultipartBody.Part {
        val requestBody = imageBytes.toRequestBody("image/jpeg".toMediaType())
        return MultipartBody.Part.createFormData("image", fileName, requestBody)
    }

    private fun itemKey(item: MenuItem): String {
        val namePart = item.name?.trim()?.lowercase().orEmpty()
        val pricePart = item.price?.trim().orEmpty()
        return "$namePart|$pricePart"
    }

    private fun cleanText(value: String?): String? {
        val text = value?.trim() ?: return null
        if (text.isEmpty()) return null
        if (text.lowercase() in emptyLikeTokens) return null
        return text
    }

    private fun cleanList(values: List<String>?): List<String> {
        return values.orEmpty().mapNotNull { cleanText(it) }.distinct()
    }

    private fun pickText(vararg values: String?): String? {
        for (value in values) {
            val cleaned = cleanText(value)
            if (cleaned != null) return cleaned
        }
        return null
    }

    private fun sanitizeMenuItem(item: MenuItem): MenuItem {
        return MenuItem(
            name = cleanText(item.name),
            price = cleanText(item.price),
            description = cleanText(item.description),
            category = pickText(item.category, "Other Dishes"),
            ingredients = cleanList(item.ingredients),
            taste = cleanText(item.taste),
            similarDish1 = cleanText(item.similarDish1),
            similarDish2 = cleanText(item.similarDish2),
            recommendation = cleanText(item.recommendation),
            recommendation_reason = cleanText(item.recommendation_reason),
            allergens = cleanList(item.allergens),
            spiciness_level = cleanText(item.spiciness_level),
            preparation_method = cleanText(item.preparation_method)
        )
    }

    private fun inferIngredients(name: String, description: String): List<String> {
        val text = "${name.lowercase()} ${description.lowercase()}"
        return when {
            "pizza" in text -> listOf("dough", "tomato", "cheese")
            "pasta" in text || "noodle" in text -> listOf("pasta", "olive oil", "herbs")
            "burger" in text || "sandwich" in text -> listOf("bread", "protein", "vegetables")
            "salad" in text -> listOf("greens", "olive oil", "seasoning")
            "curry" in text -> listOf("spices", "onion", "oil")
            "soup" in text -> listOf("broth", "herbs", "vegetables")
            "dessert" in text || "cake" in text -> listOf("flour", "sugar", "butter")
            else -> listOf("chef-special ingredients")
        }
    }

    private fun inferTaste(name: String, description: String): String {
        val text = "${name.lowercase()} ${description.lowercase()}"
        return when {
            listOf("spicy", "chili", "hot", "pepper").any { it in text } -> "spicy"
            listOf("sweet", "dessert", "honey", "sugar").any { it in text } -> "sweet"
            listOf("lemon", "citrus", "vinegar", "tangy").any { it in text } -> "tangy"
            else -> "savory"
        }
    }

    private fun inferSimilar(name: String, description: String): Pair<String, String> {
        val text = "${name.lowercase()} ${description.lowercase()}"
        return when {
            "pizza" in text -> "Lahmacun" to "Manakish"
            "pasta" in text || "noodle" in text -> "Yakisoba" to "Dan Dan Noodles"
            "curry" in text -> "Thai Green Curry" to "Japanese Katsu Curry"
            "burger" in text -> "Banh Mi" to "Arepa"
            "soup" in text -> "Tom Yum" to "Miso Soup"
            else -> "Paella" to "Bibimbap"
        }
    }

    private fun inferPreparation(name: String, description: String): String {
        val text = "${name.lowercase()} ${description.lowercase()}"
        return when {
            "fried" in text -> "fried"
            "grill" in text -> "grilled"
            "baked" in text -> "baked"
            "steam" in text -> "steamed"
            "roast" in text -> "roasted"
            "boil" in text -> "boiled"
            else -> "chef method"
        }
    }

    private fun inferSpiciness(name: String, description: String): String {
        val text = "${name.lowercase()} ${description.lowercase()}"
        return when {
            "extra hot" in text -> "extra hot"
            listOf("spicy", "chili", "hot").any { it in text } -> "medium"
            listOf("pepper", "masala").any { it in text } -> "mild"
            else -> "none"
        }
    }

    private fun inferRecommendation(name: String, description: String): Pair<String, String> {
        val text = "${name.lowercase()} ${description.lowercase()}"
        return when {
            listOf("fried", "sugar", "cream", "bacon").any { it in text } ->
                "Recommended" to "Consume in moderation based on richness."
            else -> "Recommended" to "Balanced choice based on dish profile."
        }
    }

    private fun buildDisplayDetails(geminiItem: MenuItem, qwenItem: MenuItem): MenuItem {
        val merged = mergeGeminiAndEnhanced(geminiItem, qwenItem)
        val name = pickText(merged.name, geminiItem.name, "Unknown dish") ?: "Unknown dish"
        val description = pickText(merged.description, geminiItem.description, "Description unavailable") ?: "Description unavailable"
        val inferredIngredients = inferIngredients(name, description)
        val ingredients = cleanList(merged.ingredients).ifEmpty { inferredIngredients }
        val inferredTaste = inferTaste(name, description)
        val taste = pickText(merged.taste, inferredTaste) ?: inferredTaste
        val inferredSimilar = inferSimilar(name, description)
        val similarDish1 = pickText(merged.similarDish1, inferredSimilar.first) ?: inferredSimilar.first
        val similarDish2 = pickText(merged.similarDish2, inferredSimilar.second) ?: inferredSimilar.second
        val inferredRecommendation = inferRecommendation(name, description)
        val recommendation = pickText(merged.recommendation, inferredRecommendation.first) ?: inferredRecommendation.first
        val recommendationReason = pickText(merged.recommendation_reason, inferredRecommendation.second) ?: inferredRecommendation.second
        val allergens = cleanList(merged.allergens).ifEmpty { listOf("Not specified") }
        val spiciness = pickText(merged.spiciness_level, inferSpiciness(name, description)) ?: inferSpiciness(name, description)
        val preparation = pickText(merged.preparation_method, inferPreparation(name, description)) ?: inferPreparation(name, description)

        return MenuItem(
            name = name,
            price = pickText(merged.price, geminiItem.price, "-") ?: "-",
            description = description,
            category = pickText(merged.category, geminiItem.category, "Other Dishes") ?: "Other Dishes",
            ingredients = ingredients,
            taste = taste,
            similarDish1 = similarDish1,
            similarDish2 = similarDish2,
            recommendation = recommendation,
            recommendation_reason = recommendationReason,
            allergens = allergens,
            spiciness_level = spiciness,
            preparation_method = preparation
        )
    }

    private fun mergeGeminiAndEnhanced(geminiItem: MenuItem, enhancedItem: MenuItem?): MenuItem {
        val sanitizedGemini = sanitizeMenuItem(geminiItem)
        val sanitizedEnhanced = enhancedItem?.let { sanitizeMenuItem(it) }
        if (sanitizedEnhanced == null) return sanitizedGemini

        val mergedIngredients = if (sanitizedEnhanced.ingredients.isNullOrEmpty()) {
            sanitizedGemini.ingredients
        } else {
            sanitizedEnhanced.ingredients
        }

        val mergedAllergens = if (sanitizedEnhanced.allergens.isNullOrEmpty()) {
            sanitizedGemini.allergens
        } else {
            sanitizedEnhanced.allergens
        }

        return MenuItem(
            name = pickText(sanitizedEnhanced.name, sanitizedGemini.name, "Unknown dish"),
            price = pickText(sanitizedEnhanced.price, sanitizedGemini.price),
            description = pickText(sanitizedEnhanced.description, sanitizedGemini.description),
            category = pickText(sanitizedEnhanced.category, sanitizedGemini.category, "Other Dishes"),
            ingredients = mergedIngredients,
            taste = pickText(sanitizedEnhanced.taste, sanitizedGemini.taste),
            similarDish1 = pickText(sanitizedEnhanced.similarDish1, sanitizedGemini.similarDish1),
            similarDish2 = pickText(sanitizedEnhanced.similarDish2, sanitizedGemini.similarDish2),
            recommendation = pickText(sanitizedEnhanced.recommendation, sanitizedGemini.recommendation),
            recommendation_reason = pickText(sanitizedEnhanced.recommendation_reason, sanitizedGemini.recommendation_reason),
            allergens = mergedAllergens,
            spiciness_level = pickText(sanitizedEnhanced.spiciness_level, sanitizedGemini.spiciness_level),
            preparation_method = pickText(sanitizedEnhanced.preparation_method, sanitizedGemini.preparation_method)
        )
    }

    private suspend fun extractDishesFallback(rawText: String?): List<MenuItem> {
        if (rawText.isNullOrBlank()) return emptyList()

        return try {
            val dishResponse = apiService?.extractDishes(DishRequest(text = rawText, language = "en"))
            if (dishResponse?.isSuccessful != true || dishResponse.body() == null) {
                emptyList()
            } else {
                dishResponse.body()!!.dishes.orEmpty()
                    .filter { !it.name.isNullOrBlank() }
                    .map {
                        MenuItem(
                            name = it.name,
                            price = it.price?.toString(),
                            description = it.description,
                            category = "-",
                            ingredients = emptyList(),
                            taste = "-"
                        )
                    }
            }
        } catch (e: Exception) {
            Log.w("MenuOcrFragment", "Fallback dish extraction failed: ${e.message}")
            emptyList()
        }
    }

    /**
     * Convert bitmap to multipart image for upload endpoint.
     */
    private fun bitmapToMultipart(bitmap: Bitmap, fileName: String): MultipartBody.Part {
        val byteArrayOutputStream = ByteArrayOutputStream()
        bitmap.compress(Bitmap.CompressFormat.JPEG, 100, byteArrayOutputStream)
        val imageBytes = byteArrayOutputStream.toByteArray()
        val requestBody = imageBytes.toRequestBody("image/jpeg".toMediaType())
        return MultipartBody.Part.createFormData("image", fileName, requestBody)
    }

    private fun bitmapToJpegBytes(bitmap: Bitmap): ByteArray {
        val byteArrayOutputStream = ByteArrayOutputStream()
        bitmap.compress(Bitmap.CompressFormat.JPEG, 100, byteArrayOutputStream)
        return byteArrayOutputStream.toByteArray()
    }

    private fun String.toTextPart() = this.toRequestBody("text/plain".toMediaType())

    /**
     * Update loading status text
     */
    private fun updateLoadingStatus(status: String) {
        val statusTextView = loadingProgress.findViewById<TextView>(R.id.loading_status_text)
        statusTextView?.text = status
    }

    /**
     * Refresh the results display with all accumulated items
     */
    private fun refreshResultsDisplay() {
        val resultBuilder = StringBuilder()
        val currentTier = ScanLimitManager.getPlanTier(requireContext())
        if (qwenEnhancementRunning) {
            resultBuilder.append("Loading additional details...\n")
        }
        val baseItems = if (accumulatedMenuItems.isNotEmpty()) {
            accumulatedMenuItems.toList()
        } else {
            accumulatedGeminiItems.toList()
        }
        val filteredItems = applyHealthAndTasteFilter(baseItems)
        resultBuilder.append("${filteredItems.size} dishes found")

        geminiDishLinksContainer.removeAllViews()
        qwenDetailCard.visibility = View.GONE
        geminiDishLinksContainer.visibility = View.VISIBLE

        if (filteredItems.isEmpty()) {
            val emptyView = TextView(requireContext()).apply {
                text = "No dishes matched your Health + Taste preferences."
                setTextColor(ContextCompat.getColor(requireContext(), R.color.gray_600))
                setPadding(16, 16, 16, 16)
                textSize = 15f
                setLineSpacing(0f, 1.4f)
            }
            geminiDishLinksContainer.addView(emptyView)
        }

        val density = resources.displayMetrics.density
        filteredItems.withIndex().groupBy { it.value.category?.takeIf { c -> c.isNotBlank() } ?: "Other Dishes" }
            .forEach { (section, indexedItemsInSection) ->
                val sectionView = TextView(requireContext()).apply {
                    text = section.uppercase()
                    setTextColor(ContextCompat.getColor(requireContext(), R.color.gray_900))
                    textSize = 13f
                    setTypeface(typeface, android.graphics.Typeface.BOLD)
                    letterSpacing = 0.08f
                    setPadding(16, (20 * density).toInt(), 16, (8 * density).toInt())
                }
                geminiDishLinksContainer.addView(sectionView)

                indexedItemsInSection.forEach { indexedItem ->
                    val item = indexedItem.value
                    val dishName = pickText(item.name, "Unknown dish") ?: "Unknown dish"
                    val dishPrice = pickText(item.price, "") ?: ""
                    val dishDesc = pickText(item.description, "") ?: ""

                    // Card-like container for each dish
                    val dishCard = LinearLayout(requireContext()).apply {
                        orientation = LinearLayout.VERTICAL
                        val params = LinearLayout.LayoutParams(
                            LinearLayout.LayoutParams.MATCH_PARENT,
                            LinearLayout.LayoutParams.WRAP_CONTENT
                        )
                        params.setMargins(
                            (8 * density).toInt(),
                            (4 * density).toInt(),
                            (8 * density).toInt(),
                            (4 * density).toInt()
                        )
                        layoutParams = params
                        setPadding(
                            (16 * density).toInt(),
                            (12 * density).toInt(),
                            (16 * density).toInt(),
                            (12 * density).toInt()
                        )
                        background = ContextCompat.getDrawable(requireContext(), R.drawable.bg_card)
                        isClickable = true
                        isFocusable = true
                        setOnClickListener { showQwenDishDetails(resolveDetailIndex(item), item) }
                    }

                    // Top row: name + price
                    val topRow = LinearLayout(requireContext()).apply {
                        orientation = LinearLayout.HORIZONTAL
                        gravity = Gravity.CENTER_VERTICAL
                    }
                    val nameView = TextView(requireContext()).apply {
                        text = dishName
                        setTextColor(ContextCompat.getColor(requireContext(), R.color.gray_900))
                        textSize = 16f
                        setTypeface(typeface, android.graphics.Typeface.BOLD)
                        layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
                    }
                    topRow.addView(nameView)
                    if (dishPrice.isNotBlank()) {
                        val priceView = TextView(requireContext()).apply {
                            text = dishPrice
                            setTextColor(ContextCompat.getColor(requireContext(), R.color.brand_primary))
                            textSize = 15f
                            setTypeface(typeface, android.graphics.Typeface.BOLD)
                        }
                        topRow.addView(priceView)
                    }
                    dishCard.addView(topRow)

                    // Description (truncated)
                    if (dishDesc.isNotBlank()) {
                        val descView = TextView(requireContext()).apply {
                            text = dishDesc
                            setTextColor(ContextCompat.getColor(requireContext(), R.color.gray_600))
                            textSize = 14f
                            maxLines = 2
                            ellipsize = android.text.TextUtils.TruncateAt.END
                            setLineSpacing(0f, 1.3f)
                            setPadding(0, (4 * density).toInt(), 0, 0)
                        }
                        dishCard.addView(descView)
                    }

                    // Enhancement badge (ingredients/taste preview)
                    val hasEnhancement = !item.ingredients.isNullOrEmpty() || !item.taste.isNullOrBlank()
                    if (hasEnhancement) {
                        val badgeRow = LinearLayout(requireContext()).apply {
                            orientation = LinearLayout.HORIZONTAL
                            setPadding(0, (6 * density).toInt(), 0, 0)
                            gravity = Gravity.CENTER_VERTICAL
                        }
                        if (!item.taste.isNullOrBlank() && item.taste !in emptyLikeTokens) {
                            val tasteChip = TextView(requireContext()).apply {
                                text = "\uD83D\uDE0B ${item.taste}"
                                textSize = 12f
                                setTextColor(ContextCompat.getColor(requireContext(), R.color.gray_700))
                                setPadding((8 * density).toInt(), (2 * density).toInt(), (8 * density).toInt(), (2 * density).toInt())
                            }
                            badgeRow.addView(tasteChip)
                        }
                        val tapHint = TextView(requireContext()).apply {
                            text = "Tap for details →"
                            textSize = 12f
                            setTextColor(ContextCompat.getColor(requireContext(), R.color.gray_500))
                            layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f).apply {
                                gravity = Gravity.END
                            }
                            gravity = Gravity.END
                        }
                        badgeRow.addView(tapHint)
                        dishCard.addView(badgeRow)
                    }

                    geminiDishLinksContainer.addView(dishCard)
                }
            }

        ocrResults.text = resultBuilder.toString()
        resultsCard.visibility = View.VISIBLE
        actionButtons.visibility = View.VISIBLE
    }

    private fun showQwenDishDetails(index: Int, selectedItem: MenuItem) {
        if (!ScanLimitManager.canUseAdditionalDetails(requireContext())) {
            detailDishName.text = pickText(selectedItem.name, "Unknown dish") ?: "Unknown dish"
            detailPrice.text = "Price: ${pickText(selectedItem.price, "-") ?: "-"}"
            detailDescription.text = "Description: ${pickText(selectedItem.description, "Description unavailable") ?: "Description unavailable"}"
            detailIngredients.text = "Ingredients:\nUpgrade to Pro or Max to view"
            detailTaste.text = "Taste: ${pickText(selectedItem.taste, "-") ?: "-"}"
            detailSimilar.text = "Similar Dishes:\nUpgrade to Pro to view"
            detailRecommendation.text = "Health Recommendation: Upgrade to Max to view"
            detailAllergens.text = "Allergens: Upgrade to Pro or Max to view"
            detailSpiciness.text = "Spiciness: Upgrade to Pro or Max to view"
            detailPreparation.text = "Preparation: Upgrade to Pro or Max to view"

            geminiDishLinksContainer.visibility = View.GONE
            qwenDetailCard.visibility = View.VISIBLE
            return
        }

        val geminiItem = sanitizeMenuItem(accumulatedGeminiItems.getOrNull(index) ?: selectedItem)
        val qwenItem = sanitizeMenuItem(findQwenItemForGemini(index, geminiItem) ?: geminiItem)
        val detailItem = buildDisplayDetails(geminiItem, qwenItem)

        detailDishName.text = detailItem.name ?: "Unknown dish"
        detailPrice.text = detailItem.price ?: "-"
        detailDescription.text = detailItem.description ?: "Description unavailable"

        val canUseIngredients = ScanLimitManager.canUseIngredients(requireContext())
        val canUseSimilar = ScanLimitManager.canUseSimilarDishes(requireContext())
        val canUseRecommendations = ScanLimitManager.canUseRecommendations(requireContext())

        val ingredientsText = if (!cleanList(detailItem.ingredients).isNullOrEmpty()) {
            cleanList(detailItem.ingredients).joinToString("\n") { "  • $it" }
        } else {
            "  Not available"
        }
        detailIngredients.text = if (canUseIngredients) {
            "🧾 Ingredients\n$ingredientsText"
        } else {
            "🧾 Ingredients\n  Upgrade to Pro or Max to view"
        }
        detailTaste.text = "😋 Taste: ${pickText(detailItem.taste, "Not available") ?: "Not available"}"
        detailSimilar.text = if (canUseSimilar) {
            "🌍 Similar Dishes\n  • ${pickText(detailItem.similarDish1, "Not available") ?: "Not available"}\n  • ${pickText(detailItem.similarDish2, "Not available") ?: "Not available"}"
        } else {
            "🌍 Similar Dishes\n  Upgrade to Pro to view"
        }

        val recommendationValue = if (showRecommendationColumn) {
            "${pickText(detailItem.recommendation, "Recommended") ?: "Recommended"}${if (!detailItem.recommendation_reason.isNullOrBlank()) "\n  ${detailItem.recommendation_reason}" else ""}"
        } else {
            pickText(detailItem.recommendation, "Recommended") ?: "Recommended"
        }
        detailRecommendation.text = if (canUseRecommendations) {
            "💊 Recommendation\n  ${pickText(recommendationValue, "Not available") ?: "Not available"}"
        } else {
            "💊 Recommendation\n  Upgrade to Max to view"
        }
        val allergensText = if (!cleanList(detailItem.allergens).isNullOrEmpty()) cleanList(detailItem.allergens).joinToString(", ") else "Not specified"
        detailAllergens.text = if (canUseIngredients) "⚠️ Allergens: $allergensText" else "⚠️ Allergens: Upgrade to Pro or Max"
        detailSpiciness.text = if (canUseIngredients) "🌶️ Spiciness: ${pickText(detailItem.spiciness_level, "Not available") ?: "Not available"}" else "🌶️ Spiciness: Upgrade to Pro or Max"
        detailPreparation.text = if (canUseIngredients) "👨‍🍳 Preparation: ${pickText(detailItem.preparation_method, "Not available") ?: "Not available"}" else "👨‍🍳 Preparation: Upgrade to Pro or Max"

        geminiDishLinksContainer.visibility = View.GONE
        qwenDetailCard.visibility = View.VISIBLE
    }

    private fun findQwenItemForGemini(index: Int, geminiItem: MenuItem): MenuItem? {
        val indexed = accumulatedMenuItems.getOrNull(index)
        if (indexed != null) {
            val indexedName = indexed.name?.trim()?.lowercase().orEmpty()
            val geminiName = geminiItem.name?.trim()?.lowercase().orEmpty()
            if (indexedName == geminiName || geminiName.isBlank()) {
                return indexed
            }
        }

        val targetName = geminiItem.name?.trim()?.lowercase().orEmpty()
        val targetPrice = geminiItem.price?.trim().orEmpty()
        if (targetName.isNotBlank()) {
            accumulatedMenuItems.firstOrNull {
                (it.name?.trim()?.lowercase().orEmpty() == targetName) &&
                    (targetPrice.isBlank() || it.price?.trim().orEmpty() == targetPrice)
            }?.let { return it }

            accumulatedMenuItems.firstOrNull {
                it.name?.trim()?.lowercase().orEmpty() == targetName
            }?.let { return it }
        }

        return accumulatedMenuItems.getOrNull(index)
    }

    private fun resolveDetailIndex(item: MenuItem): Int {
        val key = itemKey(item)
        val fromEnhanced = accumulatedMenuItems.indexOfFirst { itemKey(it) == key }
        if (fromEnhanced >= 0) return fromEnhanced

        val fromGemini = accumulatedGeminiItems.indexOfFirst { itemKey(it) == key }
        if (fromGemini >= 0) return fromGemini

        return accumulatedMenuItems.indexOfFirst {
            it.name?.trim()?.equals(item.name?.trim(), ignoreCase = true) == true
        }
    }

    private fun readCachedTokens(key: String): Set<String> {
        val prefs = requireContext().getSharedPreferences(HEALTH_PREFS, android.content.Context.MODE_PRIVATE)
        return prefs.getString(key, "")
            .orEmpty()
            .split('|')
            .map { it.trim().lowercase() }
            .filter { it.isNotBlank() }
            .toSet()
    }

    private fun applyHealthAndTasteFilter(items: List<MenuItem>): List<MenuItem> {
        if (items.isEmpty()) return items

        val healthConditions = readCachedTokens(KEY_HEALTH_CONDITIONS)
        val allergies = readCachedTokens(KEY_ALLERGIES)
        val dietary = readCachedTokens(KEY_DIETARY_PREFERENCES)
        val tastePreferences = readCachedTokens(KEY_TASTE_PREFERENCES)

        if (healthConditions.isEmpty() && allergies.isEmpty() && dietary.isEmpty() && tastePreferences.isEmpty()) {
            return items
        }

        val sweetRiskTokens = listOf("dessert", "cake", "sweet", "sugar", "syrup")
        val saltyRiskTokens = listOf("salt", "salty", "smoked", "cured", "processed")
        val friedRiskTokens = listOf("fried", "butter", "cream", "fatty", "bacon")
        val nonVegTokens = listOf("chicken", "beef", "pork", "fish", "mutton", "seafood", "meat")
        val nonVeganTokens = nonVegTokens + listOf("egg", "milk", "cheese", "butter", "cream", "yogurt", "honey")

        return items.filter { item ->
            val text = buildString {
                append(item.name.orEmpty())
                append(' ')
                append(item.description.orEmpty())
                append(' ')
                append(item.taste.orEmpty())
                append(' ')
                append(item.ingredients.orEmpty().joinToString(" "))
                append(' ')
                append(item.allergens.orEmpty().joinToString(" "))
            }.lowercase()

            val blockedByAllergy = allergies.any { allergy -> allergy in text }
            if (blockedByAllergy) return@filter false

            if (("diabetes" in healthConditions || "prediabetes" in healthConditions) && sweetRiskTokens.any { it in text }) {
                return@filter false
            }

            if (("hypertension" in healthConditions || "high blood pressure" in healthConditions) && saltyRiskTokens.any { it in text }) {
                return@filter false
            }

            if (("heart disease" in healthConditions || "high cholesterol" in healthConditions || "cholesterol" in healthConditions) && friedRiskTokens.any { it in text }) {
                return@filter false
            }

            if (("vegetarian" in dietary) && nonVegTokens.any { it in text }) {
                return@filter false
            }

            if (("vegan" in dietary) && nonVeganTokens.any { it in text }) {
                return@filter false
            }

            if (tastePreferences.isNotEmpty()) {
                val tasteText = "${item.taste.orEmpty()} ${item.description.orEmpty()} ${item.name.orEmpty()}".lowercase()
                if (!tastePreferences.any { pref -> pref in tasteText }) {
                    return@filter false
                }
            }

            true
        }
    }

    private fun setupTranslationControls() {
        val labels = languageCodeByLabel.keys.toList()
        spinnerTranslateLanguage.adapter = ArrayAdapter(
            requireContext(),
            android.R.layout.simple_spinner_dropdown_item,
            labels
        )

        val translationAllowed = ScanLimitManager.canUseTranslation(requireContext())
        switchTranslate.isEnabled = translationAllowed
        switchTranslate.text = if (translationAllowed) "Translate Output" else "Translate Output (Unavailable on Max)"

        switchTranslate.setOnCheckedChangeListener { _, isChecked ->
            if (isChecked && !ScanLimitManager.canUseTranslation(requireContext())) {
                switchTranslate.isChecked = false
                Toast.makeText(requireContext(), "Translation is available on Free and Pro plans.", Toast.LENGTH_SHORT).show()
                return@setOnCheckedChangeListener
            }
            spinnerTranslateLanguage.visibility = if (isChecked) View.VISIBLE else View.GONE
            if (!isChecked) {
                accumulatedMenuItems.clear()
                accumulatedMenuItems.addAll(originalEnglishMenuItems)
                refreshResultsDisplay()
            } else {
                val selectedLabel = spinnerTranslateLanguage.selectedItem?.toString()
                val targetLanguage = languageCodeByLabel[selectedLabel] ?: "es"
                requestTranslation(targetLanguage)
            }
        }

        spinnerTranslateLanguage.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(parent: AdapterView<*>, view: View?, position: Int, id: Long) {
                if (!switchTranslate.isChecked) return
                val selectedLabel = parent.getItemAtPosition(position)?.toString()
                val targetLanguage = languageCodeByLabel[selectedLabel] ?: return
                requestTranslation(targetLanguage)
            }

            override fun onNothingSelected(parent: AdapterView<*>?) = Unit
        }
    }

    private fun clearResultsTable() {
        accumulatedMenuItems.clear()
        originalEnglishMenuItems.clear()
        accumulatedGeminiItems.clear()
        translatedItemsCache.clear()
        showRecommendationColumn = false
        qwenEnhancementRunning = false
        switchTranslate.isChecked = false
        spinnerTranslateLanguage.visibility = View.GONE
        geminiDishLinksContainer.removeAllViews()
        qwenDetailCard.visibility = View.GONE
        ocrResults.text = ""
        resultsCard.visibility = View.GONE
        actionButtons.visibility = View.GONE
        // Also clear images and hide preview
        selectedBitmaps.clear()
        imagesPreviewCard.visibility = View.GONE
        btnProcessOcr.visibility = View.GONE
    }

    private fun requestTranslation(targetLanguage: String) {
        if (originalEnglishMenuItems.isEmpty()) return

        val cached = translatedItemsCache[targetLanguage]
        if (cached != null) {
            accumulatedMenuItems.clear()
            accumulatedMenuItems.addAll(cached)
            refreshResultsDisplay()
            return
        }

        uiScope.launch {
            try {
                updateLoadingStatus("Translating menu...")
                loadingProgress.visibility = View.VISIBLE
                val response = apiService?.translateMenuItems(
                    MenuItemsTranslationRequest(
                        menu_items = originalEnglishMenuItems,
                        target_language = targetLanguage,
                    )
                )

                if (response?.isSuccessful == true && response.body() != null) {
                    val translated = response.body()!!.menu_items.map { sanitizeMenuItem(it) }
                    translatedItemsCache[targetLanguage] = translated
                    accumulatedMenuItems.clear()
                    accumulatedMenuItems.addAll(translated)
                    refreshResultsDisplay()
                } else {
                    Toast.makeText(requireContext(), "Translation failed: ${response?.message()}", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(requireContext(), "Translation error: ${e.localizedMessage}", Toast.LENGTH_SHORT).show()
            } finally {
                loadingProgress.visibility = View.GONE
            }
        }
    }

    private fun animateContent() {
        val uploadCard = view?.findViewById<LinearLayout>(R.id.upload_card)
        uploadCard?.alpha = 1f
        uploadCard?.translationY = 0f
    }

    override fun onDestroy() {
        super.onDestroy()
    }
}
