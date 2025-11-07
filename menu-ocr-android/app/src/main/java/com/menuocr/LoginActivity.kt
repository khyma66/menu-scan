package com.menuocr

import android.content.Intent
import android.os.Bundle
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.menuocr.databinding.ActivityLoginBinding
import com.menuocr.viewmodel.AuthViewModel
import com.google.android.material.snackbar.Snackbar
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch

@AndroidEntryPoint
class LoginActivity : AppCompatActivity() {

    private lateinit var binding: ActivityLoginBinding
    private val authViewModel: AuthViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityLoginBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupUI()
        observeAuthState()
    }

    private fun setupUI() {
        binding.btnSignIn.setOnClickListener {
            val email = binding.etEmail.text.toString().trim()
            val password = binding.etPassword.text.toString().trim()

            if (validateInput(email, password)) {
                authViewModel.signInWithEmail(email, password)
            }
        }

        binding.btnSignUp.setOnClickListener {
            val email = binding.etEmail.text.toString().trim()
            val password = binding.etPassword.text.toString().trim()

            if (validateInput(email, password)) {
                authViewModel.signUpWithEmail(email, password)
            }
        }

        binding.btnGoogleSignIn.setOnClickListener {
            authViewModel.signInWithGoogle()
        }
    }

    private fun validateInput(email: String, password: String): Boolean {
        return when {
            email.isEmpty() -> {
                binding.tilEmail.error = "Email is required"
                false
            }
            password.isEmpty() -> {
                binding.tilPassword.error = "Password is required"
                false
            }
            password.length < 6 -> {
                binding.tilPassword.error = "Password must be at least 6 characters"
                false
            }
            else -> {
                binding.tilEmail.error = null
                binding.tilPassword.error = null
                true
            }
        }
    }

    private fun observeAuthState() {
        lifecycleScope.launch {
            authViewModel.authState.collect { state ->
                when (state) {
                    is AuthState.Loading -> showLoading()
                    is AuthState.Authenticated -> navigateToMain()
                    is AuthState.Error -> showError(state.message)
                    is AuthState.PasswordResetSent -> showPasswordResetSent()
                    else -> hideLoading()
                }
            }
        }
    }

    private fun showLoading() {
        binding.progressBar.visibility = android.view.View.VISIBLE
        binding.btnSignIn.isEnabled = false
        binding.btnSignUp.isEnabled = false
        binding.btnGoogleSignIn.isEnabled = false
    }

    private fun hideLoading() {
        binding.progressBar.visibility = android.view.View.GONE
        binding.btnSignIn.isEnabled = true
        binding.btnSignUp.isEnabled = true
        binding.btnGoogleSignIn.isEnabled = true
    }

    private fun navigateToMain() {
        val intent = Intent(this, MainActivity::class.java)
        intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        startActivity(intent)
        finish()
    }

    private fun showError(message: String) {
        hideLoading()
        Snackbar.make(binding.root, message, Snackbar.LENGTH_LONG).show()
    }

    private fun showPasswordResetSent() {
        hideLoading()
        Snackbar.make(binding.root, "Password reset email sent", Snackbar.LENGTH_LONG).show()
    }
}