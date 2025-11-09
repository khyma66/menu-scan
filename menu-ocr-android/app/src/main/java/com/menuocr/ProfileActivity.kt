package com.menuocr

import android.content.Intent
import android.os.Bundle
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.menuocr.databinding.ActivityProfileBinding
import com.menuocr.viewmodel.AuthViewModel
import com.menuocr.viewmodel.AuthState
import com.google.android.material.snackbar.Snackbar
import dagger.hilt.android.AndroidEntryPoint
import io.github.jan.supabase.gotrue.user.UserInfo
import kotlinx.coroutines.launch

@AndroidEntryPoint
class ProfileActivity : AppCompatActivity() {

    private lateinit var binding: ActivityProfileBinding
    private val authViewModel: AuthViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityProfileBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupUI()
        observeAuthState()
        loadUserProfile()
    }

    private fun setupUI() {
        binding.btnSignOut.setOnClickListener {
            authViewModel.signOut()
        }

        binding.btnBack.setOnClickListener {
            finish()
        }
    }

    private fun observeAuthState() {
        lifecycleScope.launch {
            authViewModel.authState.collect { state ->
                when (state) {
                    is AuthState.Authenticated -> {
                        // User is still authenticated, no action needed
                    }
                    is AuthState.Unauthenticated -> {
                        // User signed out, go back to login
                        navigateToLogin()
                    }
                    is AuthState.Error -> {
                        showError(state.message)
                    }
                    else -> {
                        // Loading or other states
                    }
                }
            }
        }
    }

    private fun loadUserProfile() {
        val user = authViewModel.authState.value
        if (user is AuthState.Authenticated) {
            displayUserInfo(user.user)
        }
    }

    private fun displayUserInfo(user: UserInfo) {
        binding.tvUserName.text = user.userMetadata?.get("name") as? String
            ?: user.userMetadata?.get("full_name") as? String
            ?: "User"

        binding.tvUserEmail.text = user.email ?: "No email"

        binding.tvUserId.text = user.id

        binding.tvCreatedAt.text = user.createdAt?.let {
            java.text.SimpleDateFormat("MMM dd, yyyy", java.util.Locale.getDefault()).format(java.util.Date(it))
        } ?: "Unknown"

        binding.tvLastSignIn.text = user.lastSignInAt?.let {
            java.text.SimpleDateFormat("MMM dd, yyyy HH:mm", java.util.Locale.getDefault()).format(java.util.Date(it))
        } ?: "Never"
    }

    private fun navigateToLogin() {
        val intent = Intent(this, LoginActivity::class.java)
        intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        startActivity(intent)
        finish()
    }

    private fun showError(message: String) {
        Snackbar.make(binding.root, message, Snackbar.LENGTH_LONG).show()
    }
}