package com.menuocr

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity

class LoginActivity : AppCompatActivity() {

    private lateinit var loginButton: Button
    private lateinit var titleText: TextView
    private lateinit var infoText: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Create simple layout programmatically
        val layout = android.widget.LinearLayout(this)
        layout.orientation = android.widget.LinearLayout.VERTICAL
        layout.setPadding(16, 16, 16, 16)
        
        // Title
        titleText = TextView(this)
        titleText.text = "Menu OCR - Login"
        titleText.textSize = 24f
        titleText.setPadding(0, 0, 0, 16)
        layout.addView(titleText)
        
        // Info
        infoText = TextView(this)
        infoText.text = "Test login screen\n\nFor testing purposes, this is a simplified version without Supabase authentication.\n\nClick below to go to main screen."
        infoText.setPadding(0, 0, 0, 32)
        layout.addView(infoText)
        
        // Login button (go to main)
        loginButton = Button(this)
        loginButton.text = "Enter Main Screen"
        loginButton.setOnClickListener {
            val intent = Intent(this, MainActivity::class.java)
            intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
            startActivity(intent)
            finish()
        }
        layout.addView(loginButton)
        
        setContentView(layout)
    }
}