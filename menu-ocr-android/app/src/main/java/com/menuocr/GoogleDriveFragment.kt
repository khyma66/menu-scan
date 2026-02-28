package com.menuocr

import android.animation.Animator
import android.animation.AnimatorListenerAdapter
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.view.animation.AccelerateDecelerateInterpolator
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.cardview.widget.CardView
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment

data class DriveFile(
    val name: String,
    val size: String,
    val modifiedDate: String,
    val type: String
)

class GoogleDriveFragment : Fragment() {

    private lateinit var driveStatus: TextView
    private lateinit var btnSignInDrive: Button
    private lateinit var btnRefreshFiles: Button
    private lateinit var btnSyncDrive: Button
    private lateinit var btnDriveSettings: Button
    private lateinit var filesContainer: LinearLayout
    private lateinit var emptyState: LinearLayout

    private val driveFiles = listOf(
        DriveFile("Menu_Scan_001.jpg", "2.4 MB", "2025-02-07", "Image"),
        DriveFile("Restaurant_Menu.pdf", "1.8 MB", "2025-02-06", "PDF"),
        DriveFile("Menu_Scan_002.jpg", "3.1 MB", "2025-02-05", "Image"),
        DriveFile("Breakfast_Menu.txt", "45 KB", "2025-02-04", "Text"),
        DriveFile("Menu_Scan_003.jpg", "2.9 MB", "2025-02-03", "Image")
    )

    private var isSignedIn = false

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_google_drive, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        // Initialize views
        driveStatus = view.findViewById(R.id.drive_status)
        btnSignInDrive = view.findViewById(R.id.btn_sign_in_drive)
        btnRefreshFiles = view.findViewById(R.id.btn_refresh_files)
        btnSyncDrive = view.findViewById(R.id.btn_sync_drive)
        btnDriveSettings = view.findViewById(R.id.btn_drive_settings)
        filesContainer = view.findViewById(R.id.files_container)
        emptyState = view.findViewById(R.id.empty_state)

        setupClickListeners()
        updateDriveStatus("☁️ Google Drive integration ready (demo mode)")

        // Display files
        displayFiles()

        // Animate content on load
        animateContent()
    }

    private fun setupClickListeners() {
        btnSignInDrive.setOnClickListener {
            isSignedIn = !isSignedIn
            if (isSignedIn) {
                btnSignInDrive.text = "🔓 Sign Out"
                updateDriveStatus("✅ Signed in to Google Drive")
                displayFiles()
                Toast.makeText(requireContext(), "Signed in to Google Drive", Toast.LENGTH_SHORT).show()
            } else {
                btnSignInDrive.text = "🔐 Sign In with Google"
                updateDriveStatus("☁️ Google Drive integration ready (demo mode)")
                filesContainer.removeAllViews()
                emptyState.visibility = View.VISIBLE
                Toast.makeText(requireContext(), "Signed out from Google Drive", Toast.LENGTH_SHORT).show()
            }
        }

        btnRefreshFiles.setOnClickListener {
            animateRefresh()
            Toast.makeText(requireContext(), "Refreshing files from Google Drive...", Toast.LENGTH_SHORT).show()
            Handler(Looper.getMainLooper()).postDelayed({
                displayFiles()
                Toast.makeText(requireContext(), "Files refreshed successfully", Toast.LENGTH_SHORT).show()
            }, 1000)
        }

        btnSyncDrive.setOnClickListener {
            animateSync()
            Toast.makeText(requireContext(), "Syncing with Google Drive...", Toast.LENGTH_SHORT).show()
            Handler(Looper.getMainLooper()).postDelayed({
                Toast.makeText(requireContext(), "Sync completed successfully", Toast.LENGTH_SHORT).show()
            }, 1500)
        }

        btnDriveSettings.setOnClickListener {
            Toast.makeText(requireContext(), "Google Drive settings", Toast.LENGTH_SHORT).show()
        }
    }

    private fun displayFiles() {
        filesContainer.removeAllViews()

        if (!isSignedIn) {
            emptyState.visibility = View.VISIBLE
            return
        }

        emptyState.visibility = View.GONE

        driveFiles.forEachIndexed { index, file ->
            val card = createFileCard(file)
            filesContainer.addView(card)

            // Animate card with staggered delay
            card.alpha = 0f
            card.translationX = -50f
            Handler(Looper.getMainLooper()).postDelayed({
                card.animate()
                    .alpha(1f)
                    .translationX(0f)
                    .setDuration(300)
                    .setInterpolator(AccelerateDecelerateInterpolator())
                    .start()
            }, (index * 80).toLong())
        }
    }

    private fun createFileCard(file: DriveFile): CardView {
        val card = CardView(requireContext()).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                bottomMargin = 12
            }
            radius = 12f
            cardElevation = 4f
            setCardBackgroundColor(ContextCompat.getColor(requireContext(), android.R.color.white))
        }

        val cardLayout = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(16, 16, 16, 16)
        }

        // File icon
        val iconView = androidx.appcompat.widget.AppCompatImageView(requireContext()).apply {
            layoutParams = LinearLayout.LayoutParams(48, 48).apply {
                gravity = android.view.Gravity.CENTER_VERTICAL
            }
            setImageResource(getFileIcon(file.type))
            setBackgroundResource(R.drawable.stats_card_background)
            setPadding(12, 12, 12, 12)
        }

        // Content
        val contentLayout = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
            layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f).apply {
                marginStart = 16
            }
        }

        val nameText = TextView(requireContext()).apply {
            text = file.name
            textSize = 14f
            setTypeface(null, android.graphics.Typeface.BOLD)
            setTextColor(ContextCompat.getColor(requireContext(), R.color.gray_900))
        }

        val detailsText = TextView(requireContext()).apply {
            text = "${file.type} • ${file.size} • ${file.modifiedDate}"
            textSize = 12f
            setTextColor(ContextCompat.getColor(requireContext(), R.color.gray_600))
        }

        contentLayout.addView(nameText)
        contentLayout.addView(detailsText)

        // Action button
        val actionButton = Button(requireContext()).apply {
            text = "View"
            textSize = 12f
            setBackgroundResource(R.drawable.button_secondary)
            setTextColor(ContextCompat.getColor(requireContext(), R.color.blue_500))
            setPadding(16, 8, 16, 8)
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                gravity = android.view.Gravity.CENTER_VERTICAL
            }

            setOnClickListener {
                Toast.makeText(requireContext(), "Opening ${file.name}", Toast.LENGTH_SHORT).show()
            }
        }

        cardLayout.addView(iconView)
        cardLayout.addView(contentLayout)
        cardLayout.addView(actionButton)

        card.addView(cardLayout)

        // Add click listener
        card.setOnClickListener {
            Toast.makeText(requireContext(), "Selected: ${file.name}", Toast.LENGTH_SHORT).show()
        }

        return card
    }

    private fun getFileIcon(type: String): Int {
        return when (type.lowercase()) {
            "image", "jpg", "png" -> R.drawable.ic_camera
            "pdf" -> R.drawable.ic_folder_open
            "text", "txt" -> R.drawable.ic_search
            else -> R.drawable.ic_folder_open
        }
    }

    private fun updateDriveStatus(message: String) {
        driveStatus.text = message
    }

    private fun animateRefresh() {
        btnRefreshFiles.animate()
            .rotationBy(360f)
            .setDuration(500)
            .setInterpolator(AccelerateDecelerateInterpolator())
            .start()
    }

    private fun animateSync() {
        btnSyncDrive.animate()
            .scaleX(0.9f)
            .scaleY(0.9f)
            .setDuration(100)
            .setListener(object : AnimatorListenerAdapter() {
                override fun onAnimationEnd(animation: Animator) {
                    btnSyncDrive.animate()
                        .scaleX(1f)
                        .scaleY(1f)
                        .setDuration(100)
                        .start()
                }
            })
            .start()
    }

    private fun animateContent() {
        val statusCard = view?.findViewById<CardView>(R.id.status_card)
        statusCard?.alpha = 0f
        statusCard?.translationY = -20f

        statusCard?.animate()
            ?.alpha(1f)
            ?.translationY(0f)
            ?.setDuration(400)
            ?.setStartDelay(100)
            ?.start()

        val actionButtonsLayout = view?.findViewById<LinearLayout>(R.id.action_buttons_layout)
        actionButtonsLayout?.alpha = 0f
        actionButtonsLayout?.translationY = 20f

        actionButtonsLayout?.animate()
            ?.alpha(1f)
            ?.translationY(0f)
            ?.setDuration(400)
            ?.setStartDelay(200)
            ?.start()
    }
}