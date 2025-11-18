// Google Drive Integration for MainActivity.kt
// Add these methods to your MainActivity class

// 1. Add these properties to the MainActivity class:
private var googleDriveService: GoogleDriveService? = null
private val googleSignInLauncher = registerForActivityResult(
    ActivityResultContracts.StartActivityForResult()
) { result ->
    if (result.resultCode == RESULT_OK) {
        initializeGoogleDrive()
    } else {
        Toast.makeText(this, "Google Drive sign-in failed", Toast.LENGTH_SHORT).show()
    }
}

// 2. Add these buttons to your onCreate method (around line 123):
// Test API button
val testApiButton = Button(this)
testApiButton.text = "Test API Connection"
testApiButton.setOnClickListener {
    testApiConnection()
}
layout.addView(testApiButton)

// Add these new buttons:
val connectDriveButton = Button(this)
connectDriveButton.text = "Connect Google Drive"
connectDriveButton.setOnClickListener {
    connectGoogleDrive()
}
layout.addView(connectDriveButton)

val loadFromDriveButton = Button(this)
loadFromDriveButton.text = "Load from Google Drive"
loadFromDriveButton.setOnClickListener {
    loadGoogleDriveFiles()
}
layout.addView(loadFromDriveButton)

val saveToDriveButton = Button(this)
saveToDriveButton.text = "Save to Google Drive"
saveToDriveButton.setOnClickListener {
    saveToGoogleDrive()
}
layout.addView(saveToDriveButton)

// 3. Add these methods to MainActivity class:

private fun initializeGoogleDrive() {
    googleDriveService = GoogleDriveService(this)
    uiScope.launch {
        val isInitialized = googleDriveService?.signInAndInitializeDrive() ?: false
        if (isInitialized) {
            statusText.text = "✅ Google Drive initialized successfully!\nReady to access files from Drive"
            loadGoogleDriveFiles()
        } else {
            statusText.text = "⚠️ Google Drive requires sign-in\nClick 'Connect Google Drive' to authorize"
        }
    }
}

private fun loadGoogleDriveFiles() {
    uiScope.launch {
        try {
            val files = googleDriveService?.getDriveFiles() ?: emptyList()
            if (files.isNotEmpty()) {
                statusText.text = "✅ Found ${files.size} files in Google Drive\nYou can now select images from Drive"
                // Auto-load first image file
                files.firstOrNull()?.let { file ->
                    val bitmap = googleDriveService?.downloadAndProcessFile(file)
                    bitmap?.let {
                        selectedBitmap = it
                        imageView.setImageBitmap(it)
                        statusText.text = "✅ Loaded image from Google Drive!\nReady for OCR processing"
                        btnProcessOcr.isEnabled = true
                    }
                }
            } else {
                statusText.text = "📁 No image files found in Google Drive"
            }
        } catch (e: Exception) {
            statusText.text = "❌ Error loading Google Drive files: ${e.message}"
        }
    }
}

private fun connectGoogleDrive() {
    if (googleDriveService?.isSignedIn() == true) {
        initializeGoogleDrive()
    } else {
        googleDriveService?.getSignInIntent()?.let { intent ->
            googleSignInLauncher.launch(intent)
        }
    }
}

private fun saveToGoogleDrive() {
    selectedBitmap?.let { bitmap ->
        uiScope.launch {
            val timestamp = System.currentTimeMillis()
            val fileName = "menu_ocr_${timestamp}.jpg"
            val success = googleDriveService?.uploadImageToDrive(bitmap, fileName) ?: false
            
            if (success) {
                Toast.makeText(this@MainActivity, "Image saved to Google Drive: $fileName", Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(this@MainActivity, "Failed to save image to Google Drive", Toast.LENGTH_SHORT).show()
            }
        }
    } ?: run {
        Toast.makeText(this, "No image to save", Toast.LENGTH_SHORT).show()
    }
}