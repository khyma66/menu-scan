package com.menuocr

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.text.InputType
import android.view.View
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.google.android.material.button.MaterialButton
import com.google.android.material.textfield.TextInputEditText
import com.google.android.material.textfield.TextInputLayout
import kotlinx.coroutines.launch
import android.util.Log

class LoginActivity : AppCompatActivity() {

    private lateinit var emailInput: TextInputEditText
    private lateinit var passwordInput: TextInputEditText
    private lateinit var confirmPasswordInput: TextInputEditText
    private lateinit var confirmPasswordLayout: TextInputLayout
    private lateinit var submitButton: MaterialButton
    private lateinit var loadingProgress: android.widget.ProgressBar
    private lateinit var errorText: TextView
    private lateinit var loginTab: TextView
    private lateinit var signupTab: TextView
    private lateinit var forgotPasswordText: TextView
    private lateinit var skipLoginText: TextView
    private lateinit var googleSignInButton: MaterialButton
    private lateinit var appleSignInButton: MaterialButton

    private var isLoginMode = true

    companion object {
        private const val TAG = "LoginActivity"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_login)

        initViews()
        setupListeners()
        handleOAuthCallback(intent)
        checkExistingSession()
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleOAuthCallback(intent)
    }

    private fun handleOAuthCallback(intent: Intent?) {
        val data = intent?.data ?: return
        if (data.scheme != "com.menuocr" || data.host != "auth-callback") return

        lifecycleScope.launch {
            try {
                val session = SupabaseClient.getCurrentSession()
                if (session != null) {
                    Toast.makeText(this@LoginActivity, "Authentication successful!", Toast.LENGTH_SHORT).show()
                    navigateToMain()
                }
            } catch (e: Exception) {
                Log.w(TAG, "OAuth callback received but session unavailable: ${e.message}")
            }
        }
    }

    private fun initViews() {
        emailInput = findViewById(R.id.emailInput)
        passwordInput = findViewById(R.id.passwordInput)
        confirmPasswordInput = findViewById(R.id.confirmPasswordInput)
        confirmPasswordLayout = findViewById(R.id.confirmPasswordLayout)
        submitButton = findViewById(R.id.submitButton)
        loadingProgress = findViewById(R.id.loadingProgress)
        errorText = findViewById(R.id.errorText)
        loginTab = findViewById(R.id.loginTab)
        signupTab = findViewById(R.id.signupTab)
        forgotPasswordText = findViewById(R.id.forgotPasswordText)
        skipLoginText = findViewById(R.id.skipLoginText)
        googleSignInButton = findViewById(R.id.googleSignInButton)
        appleSignInButton = findViewById(R.id.appleSignInButton)
    }

    private fun setupListeners() {
        loginTab.setOnClickListener {
            switchToLoginMode()
        }

        signupTab.setOnClickListener {
            switchToSignupMode()
        }

        submitButton.setOnClickListener {
            if (isLoginMode) {
                handleLogin()
            } else {
                handleSignup()
            }
        }

        forgotPasswordText.setOnClickListener {
            handleForgotPassword()
        }

        skipLoginText.setOnClickListener {
            navigateToMain()
        }
        
        googleSignInButton.setOnClickListener {
            handleGoogleSignIn()
        }

        appleSignInButton.setOnClickListener {
            handleAppleSignIn()
        }
    }

    private fun switchToLoginMode() {
        isLoginMode = true
        loginTab.setTextColor(getColor(R.color.green_700))
        signupTab.setTextColor(getColor(R.color.gray_text))
        confirmPasswordLayout.visibility = View.GONE
        forgotPasswordText.visibility = View.VISIBLE
        submitButton.text = "Login"
        hideError()
    }

    private fun switchToSignupMode() {
        isLoginMode = false
        signupTab.setTextColor(getColor(R.color.green_700))
        loginTab.setTextColor(getColor(R.color.gray_text))
        confirmPasswordLayout.visibility = View.VISIBLE
        forgotPasswordText.visibility = View.GONE
        submitButton.text = "Sign Up"
        hideError()
    }

    private fun checkExistingSession() {
        lifecycleScope.launch {
            try {
                val session = SupabaseClient.getCurrentSession()
                if (session != null) {
                    // User already logged in, go to main
                    navigateToMain()
                }
            } catch (e: Exception) {
                // No existing session, stay on login
            }
        }
    }

    private fun handleLogin() {
        val email = emailInput.text.toString().trim()
        val password = passwordInput.text.toString()

        if (!validateInputs(email, password)) return

        showLoading(true)
        hideError()

        lifecycleScope.launch {
            try {
                val result = SupabaseClient.signIn(email, password)
                showLoading(false)

                result.fold(
                    onSuccess = {
                        Toast.makeText(this@LoginActivity, "Login successful!", Toast.LENGTH_SHORT).show()
                        navigateToMain()
                    },
                    onFailure = { error ->
                        showError(getErrorMessage(error))
                    }
                )
            } catch (e: Exception) {
                showLoading(false)
                showError(getErrorMessage(e))
            }
        }
    }

    private fun handleSignup() {
        val email = emailInput.text.toString().trim()
        val password = passwordInput.text.toString()
        val confirmPassword = confirmPasswordInput.text.toString()

        if (!validateInputs(email, password, confirmPassword)) return

        showLoading(true)
        hideError()

        lifecycleScope.launch {
            try {
                val result = SupabaseClient.signUp(email, password)
                showLoading(false)

                result.fold(
                    onSuccess = {
                        Toast.makeText(this@LoginActivity, "Account created! Please check your email to verify.", Toast.LENGTH_LONG).show()
                        // Switch to login mode after signup
                        switchToLoginMode()
                    },
                    onFailure = { error ->
                        showError(getErrorMessage(error))
                    }
                )
            } catch (e: Exception) {
                showLoading(false)
                showError(getErrorMessage(e))
            }
        }
    }

    private fun handleForgotPassword() {
        val prefilledEmail = emailInput.text?.toString()?.trim().orEmpty()
        val emailField = EditText(this).apply {
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS
            hint = "Enter your account email"
            setText(prefilledEmail)
            setSelection(text?.length ?: 0)
        }

        android.app.AlertDialog.Builder(this)
            .setTitle("Reset Password")
            .setMessage("Enter your email to receive a password reset link.")
            .setView(emailField)
            .setPositiveButton("Send") { _, _ ->
                val email = emailField.text?.toString()?.trim().orEmpty()
                if (email.isEmpty()) {
                    showError("Please enter your email address")
                    return@setPositiveButton
                }
                if (!android.util.Patterns.EMAIL_ADDRESS.matcher(email).matches()) {
                    showError("Please enter a valid email")
                    return@setPositiveButton
                }

                showLoading(true)
                hideError()
                lifecycleScope.launch {
                    try {
                        val result = SupabaseClient.resetPassword(email)
                        showLoading(false)
                        result.fold(
                            onSuccess = {
                                Toast.makeText(this@LoginActivity, "Password reset email sent to $email", Toast.LENGTH_LONG).show()
                            },
                            onFailure = { error ->
                                showError(getErrorMessage(error))
                            }
                        )
                    } catch (e: Exception) {
                        showLoading(false)
                        showError(getErrorMessage(e))
                    }
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    private fun validateInputs(email: String, password: String, confirmPassword: String? = null): Boolean {
        if (email.isEmpty()) {
            showError("Please enter your email")
            return false
        }

        if (!android.util.Patterns.EMAIL_ADDRESS.matcher(email).matches()) {
            showError("Please enter a valid email")
            return false
        }

        if (password.isEmpty()) {
            showError("Please enter your password")
            return false
        }

        if (password.length < 6) {
            showError("Password must be at least 6 characters")
            return false
        }

        if (confirmPassword != null && password != confirmPassword) {
            showError("Passwords do not match")
            return false
        }

        return true
    }

    private fun getErrorMessage(error: Throwable): String {
        val message = error.message ?: "An error occurred"
        
        return when {
            message.contains("Invalid login credentials", ignoreCase = true) -> 
                "Invalid email or password"
            message.contains("User already registered", ignoreCase = true) -> 
                "An account with this email already exists"
            message.contains("Email not confirmed", ignoreCase = true) -> 
                "Please check your email and verify your account"
            message.contains("Password should be", ignoreCase = true) -> 
                "Password must be at least 6 characters"
            message.contains("Unable to resolve host", ignoreCase = true) ||
            message.contains("network", ignoreCase = true) -> 
                "Network error. Please check your connection"
            message.contains("Chain validation failed", ignoreCase = true) ||
            message.contains("SSL", ignoreCase = true) ->
                "Secure connection failed. Check device date/time and update Google Play services."
            else -> message
        }
    }

    private fun showLoading(show: Boolean) {
        loadingProgress.visibility = if (show) View.VISIBLE else View.GONE
        submitButton.isEnabled = !show
        submitButton.text = if (show) "" else if (isLoginMode) "Login" else "Sign Up"
    }

    private fun showError(message: String) {
        errorText.text = message
        errorText.visibility = View.VISIBLE
    }

    private fun hideError() {
        errorText.visibility = View.GONE
    }

    private fun navigateToMain() {
        val intent = Intent(this, DoorDashMainActivity::class.java)
        intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        startActivity(intent)
        finish()
    }
    
    private fun handleGoogleSignIn() {
        showLoading(true)
        hideError()

        lifecycleScope.launch {
            try {
                val result = SupabaseClient.signInWithGoogle()
                showLoading(false)

                result.fold(
                    onSuccess = {
                        Toast.makeText(this@LoginActivity, "Google sign-in successful!", Toast.LENGTH_SHORT).show()
                        navigateToMain()
                    },
                    onFailure = { error ->
                        showError(getErrorMessage(error))
                    }
                )
            } catch (e: Exception) {
                showLoading(false)
                showError(getErrorMessage(e))
            }
        }
    }

    private fun handleAppleSignIn() {
        hideError()
        try {
            val url = SupabaseClient.getAppleOAuthUrl()
            startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
            Toast.makeText(this, "Continue Apple sign-in in browser", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            showError(getErrorMessage(e))
        }
    }
}
