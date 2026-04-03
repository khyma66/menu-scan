package com.menuocr

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.text.InputType
import android.view.View
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.browser.customtabs.CustomTabColorSchemeParams
import androidx.browser.customtabs.CustomTabsIntent
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
        // Handle OAuth deep-link if this Activity was opened by an auth callback.
        // Session routing (login vs main) is handled exclusively by SplashActivity
        // to avoid double-checks and stale in-memory session races.
        handleOAuthCallback(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleOAuthCallback(intent)
    }

    private fun handleOAuthCallback(intent: Intent?) {
        val data = intent?.data ?: return

        // Handle subscription result deep-link (menuocr://subscription-result?status=...)
        // This fires after user returns from web checkout — just navigate to main
        // and let the Profile tab refresh subscription status on resume.
        if (data.scheme == "fooder" && data.host == "subscription-result") {
            val status = data.getQueryParameter("status") ?: "unknown"
            Log.i(TAG, "Subscription result deep-link received: status=$status")
            val msg = if (status == "success") "Subscription activated!" else "Checkout cancelled"
            Toast.makeText(this, msg, Toast.LENGTH_SHORT).show()
            navigateToMain()
            return
        }

        if (data.scheme != "com.menuocr" || data.host != "auth-callback") return

        // SupabaseClient.handleOAuthCallback handles both token formats:
        //   fragment:  com.menuocr://auth-callback#access_token=...
        //   query:     com.menuocr://auth-callback?access_token=...
        // Do NOT guard on encodedFragment here — fall through to SupabaseClient.
        val hasData = !data.encodedFragment.isNullOrBlank() || !data.encodedQuery.isNullOrBlank()
        if (!hasData) {
            Log.w(TAG, "OAuth callback received but no token data in URI")
            return
        }

        showLoading(true)
        lifecycleScope.launch {
            try {
                val result = SupabaseClient.handleOAuthCallback(data)
                showLoading(false)
                result.fold(
                    onSuccess = {
                        Toast.makeText(this@LoginActivity, "Authentication successful!", Toast.LENGTH_SHORT).show()
                        // Persist OAuth session tokens
                        val prefs = getSharedPreferences("fooder_auth", Context.MODE_PRIVATE)
                        SupabaseClient.saveSession(prefs)
                        navigateToMain()
                    },
                    onFailure = { error ->
                        showError(getErrorMessage(error))
                    }
                )
            } catch (e: Exception) {
                showLoading(false)
                Log.w(TAG, "OAuth callback failed: ${e.message}")
                showError(getErrorMessage(e))
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
        loginTab.setTextColor(android.graphics.Color.parseColor("#222222"))
        loginTab.setBackgroundColor(android.graphics.Color.WHITE)
        signupTab.setTextColor(android.graphics.Color.parseColor("#999999"))
        signupTab.setBackgroundColor(android.graphics.Color.parseColor("#F3F4F6"))
        confirmPasswordLayout.visibility = View.GONE
        forgotPasswordText.visibility = View.VISIBLE
        submitButton.text = "Login"
        hideError()
    }

    private fun switchToSignupMode() {
        isLoginMode = false
        signupTab.setTextColor(android.graphics.Color.parseColor("#222222"))
        signupTab.setBackgroundColor(android.graphics.Color.WHITE)
        loginTab.setTextColor(android.graphics.Color.parseColor("#999999"))
        loginTab.setBackgroundColor(android.graphics.Color.parseColor("#F3F4F6"))
        confirmPasswordLayout.visibility = View.VISIBLE
        forgotPasswordText.visibility = View.GONE
        submitButton.text = "Sign Up"
        hideError()
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
                        // Persist session so the user stays logged-in after restart
                        val prefs = getSharedPreferences("fooder_auth", Context.MODE_PRIVATE)
                        SupabaseClient.saveSession(prefs)
                        ApiClient.updateAuthToken()
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
                        // Signup succeeded — Supabase sends the 6-digit OTP to
                        // the user's email using the Fooder confirmation template.
                        showOtpVerificationDialog(email)
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

    /**
     * Shows a dialog asking the user to enter the 6-digit OTP sent to their
     * email by Fooder after sign-up. On success the user is taken straight
     * into the app without needing to click any browser link.
     */
    private fun showOtpVerificationDialog(email: String) {
        val otpInput = EditText(this).apply {
            inputType = android.text.InputType.TYPE_CLASS_NUMBER
            hint = "6-digit code"
            maxLines = 1
            filters = arrayOf(android.text.InputFilter.LengthFilter(6))
            setPadding(48, 32, 48, 32)
        }

        android.app.AlertDialog.Builder(this)
            .setTitle("Verify your email")
            .setMessage("We sent a 6-digit code to\n$email\n\nEnter it below to activate your Fooder account.")
            .setView(otpInput)
            .setPositiveButton("Verify") { _, _ ->
                val code = otpInput.text?.toString()?.trim().orEmpty()
                if (code.length != 6) {
                    showError("Please enter the full 6-digit code")
                    showOtpVerificationDialog(email)
                    return@setPositiveButton
                }
                showLoading(true)
                hideError()
                lifecycleScope.launch {
                    try {
                        val result = SupabaseClient.verifyEmailOtp(email, code)
                        showLoading(false)
                        result.fold(
                            onSuccess = {
                                Toast.makeText(
                                    this@LoginActivity,
                                    "Email verified! Welcome to Fooder.",
                                    Toast.LENGTH_SHORT
                                ).show()
                                // Persist session after OTP verification
                                val prefs = getSharedPreferences("fooder_auth", Context.MODE_PRIVATE)
                                SupabaseClient.saveSession(prefs)
                                navigateToMain()
                            },
                            onFailure = { error ->
                                showError(getErrorMessage(error))
                                showOtpVerificationDialog(email)
                            }
                        )
                    } catch (e: Exception) {
                        showLoading(false)
                        showError(getErrorMessage(e))
                        showOtpVerificationDialog(email)
                    }
                }
            }
            .setNeutralButton("Resend code") { _, _ ->
                lifecycleScope.launch {
                    SupabaseClient.signUp(email, passwordInput.text.toString())
                    Toast.makeText(
                        this@LoginActivity,
                        "New code sent to $email",
                        Toast.LENGTH_SHORT
                    ).show()
                    showOtpVerificationDialog(email)
                }
            }
            .setCancelable(false)
            .show()
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
                "Check your email for the 6-digit code, then tap Sign Up to verify"
            message.contains("Token has expired", ignoreCase = true) ||
            message.contains("OTP has expired", ignoreCase = true) ->
                "The code has expired — tap Resend code to get a new one"
            message.contains("Invalid OTP", ignoreCase = true) ||
            message.contains("otp_expired", ignoreCase = true) ->
                "Incorrect or expired code. Check the email or tap Resend code"
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
        // FLAG_ACTIVITY_CLEAR_TASK already destroys all activities in the task
        // and finishes this one — calling finish() explicitly would cause a
        // duplicate-finish and corrupt the back stack.
        intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        startActivity(intent)
    }
    
    private fun handleGoogleSignIn() {
        hideError()
        try {
            val url = SupabaseClient.getGoogleOAuthUrl()
            launchBrandedTab(url)
        } catch (e: Exception) {
            showError(getErrorMessage(e))
        }
    }

    private fun handleAppleSignIn() {
        hideError()
        try {
            val url = SupabaseClient.getAppleOAuthUrl()
            launchBrandedTab(url)
        } catch (e: Exception) {
            showError(getErrorMessage(e))
        }
    }

    private fun launchBrandedTab(url: String) {
        val toolbarColor = android.graphics.Color.parseColor("#222222")
        val colorParams = CustomTabColorSchemeParams.Builder()
            .setToolbarColor(toolbarColor)
            .setNavigationBarColor(toolbarColor)
            .build()
        val customTabsIntent = CustomTabsIntent.Builder()
            .setDefaultColorSchemeParams(colorParams)
            .setShowTitle(true)
            .setUrlBarHidingEnabled(true)
            .build()
        customTabsIntent.launchUrl(this, Uri.parse(url))
    }
}
