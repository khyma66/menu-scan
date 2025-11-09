package com.menuocr

import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.BitmapFactory
import android.os.Bundle
import android.view.View
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.github.dhaval2404.imagepicker.ImagePicker
import com.menuocr.databinding.ActivityMainBinding
import com.menuocr.viewmodel.AuthViewModel
import com.menuocr.viewmodel.MenuViewModel
import com.google.android.material.snackbar.Snackbar
import com.menuocr.viewmodel.AuthState
import com.menuocr.viewmodel.Menu
import com.menuocr.viewmodel.MenuState
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch

@AndroidEntryPoint
class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private val menuViewModel: MenuViewModel by viewModels()
    private val authViewModel: AuthViewModel by viewModels()
    private lateinit var dishAdapter: DishAdapter

    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val allGranted = permissions.values.all { it }
        if (allGranted) {
            // Permissions granted, can proceed with camera/gallery
        }
    }

    private val imagePickerLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == RESULT_OK) {
            result.data?.data?.let { uri ->
                val bitmap = BitmapFactory.decodeStream(contentResolver.openInputStream(uri))
                binding.imageView.setImageBitmap(bitmap)
                menuViewModel.processImage(bitmap)
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        checkAuthentication()
        setupRecyclerView()
        checkPermissions()
        setupUI()
        observeViewModels()
    }

    private fun checkAuthentication() {
        if (authViewModel.authState.value !is AuthState.Authenticated) {
            navigateToLogin()
            return
        }
    }

    private fun setupRecyclerView() {
        dishAdapter = DishAdapter()
        binding.recyclerView.apply {
            layoutManager = LinearLayoutManager(this@MainActivity)
            adapter = dishAdapter
        }
    }

    private fun checkPermissions() {
        val permissions = arrayOf(
            android.Manifest.permission.CAMERA,
            android.Manifest.permission.READ_EXTERNAL_STORAGE
        )

        val notGranted = permissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }

        if (notGranted.isNotEmpty()) {
            requestPermissionLauncher.launch(notGranted.toTypedArray())
        }
    }

    private fun setupUI() {
        binding.btnCaptureImage.setOnClickListener {
            ImagePicker.with(this)
                .cameraOnly()
                .crop()
                .compress(1024)
                .maxResultSize(1080, 1080)
                .createIntent { intent ->
                    imagePickerLauncher.launch(intent)
                }
        }

        binding.btnSelectImage.setOnClickListener {
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

    private fun observeViewModels() {
        lifecycleScope.launch {
            menuViewModel.menuState.collect { state ->
                when (state) {
                    is MenuState.Loading -> showLoading()
                    is MenuState.Success -> showMenu(state.menu)
                    is MenuState.Error -> showError(state.message)
                    is MenuState.Idle -> hideLoading()
                }
            }
        }

        lifecycleScope.launch {
            authViewModel.authState.collect { state ->
                if (state is AuthState.Unauthenticated) {
                    navigateToLogin()
                }
            }
        }
    }

    private fun showLoading() {
        binding.progressBar.visibility = View.VISIBLE
        binding.recyclerView.visibility = View.GONE
    }

    private fun hideLoading() {
        binding.progressBar.visibility = View.GONE
        binding.recyclerView.visibility = View.VISIBLE
    }

    private fun showMenu(menu: Menu) {
        dishAdapter.submitList(menu.dishes)
        hideLoading()
    }

    private fun showError(message: String) {
        hideLoading()
        Snackbar.make(binding.root, message, Snackbar.LENGTH_LONG).show()
    }

    private fun navigateToLogin() {
        val intent = Intent(this, LoginActivity::class.java)
        intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        startActivity(intent)
        finish()
    }

    override fun onCreateOptionsMenu(menu: android.view.Menu?): Boolean {
        menuInflater.inflate(R.menu.main_menu, menu)
        return true
    }

    override fun onOptionsItemSelected(item: android.view.MenuItem): Boolean {
        return when (item.itemId) {
            R.id.action_sign_out -> {
                authViewModel.signOut()
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }
}