package com.menuocr

import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

class ProfileActivity : AppCompatActivity() {

    private lateinit var backButton: Button
    private lateinit var titleText: TextView
    private lateinit var profileText: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Create simple layout programmatically
        val layout = android.widget.LinearLayout(this)
        layout.orientation = android.widget.LinearLayout.VERTICAL
        layout.setPadding(16, 16, 16, 16)
        
        // Title
        titleText = TextView(this)
        titleText.text = "User Profile"
        titleText.textSize = 24f
        titleText.setPadding(0, 0, 0, 16)
        layout.addView(titleText)
        
        // Profile info
        profileText = TextView(this)
        profileText.text = "Test Profile Screen\n\nFor testing purposes, this is a simplified version without Supabase authentication.\n\nUser information will be displayed here in the full version."
        profileText.setPadding(0, 0, 0, 32)
        layout.addView(profileText)
        
        // Back button
        backButton = Button(this)
        backButton.text = "Back to Main"
        backButton.setOnClickListener {
            finish()
        }
        layout.addView(backButton)
        
        setContentView(layout)
    }
}