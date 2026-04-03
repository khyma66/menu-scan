package com.menuocr

import android.content.Context
import android.os.Bundle
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import com.google.android.material.bottomnavigation.BottomNavigationView
import kotlinx.coroutines.launch

class DoorDashMainActivity : AppCompatActivity() {

    private lateinit var bottomNavigation: BottomNavigationView
    private lateinit var titleText: TextView
    private lateinit var userGreetingText: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_doordash_main)

        bottomNavigation = findViewById(R.id.bottom_navigation)
        titleText        = findViewById(R.id.title_text)
        userGreetingText = findViewById(R.id.user_greeting_text)

        setupBottomNavigation()

        if (savedInstanceState == null) {
            openFragment(MenuOcrFragment())
            bottomNavigation.selectedItemId = R.id.nav_scan
            titleText.text = "Scan"
        }
    }

    override fun onResume() {
        super.onResume()
        restoreSessionIfNeeded()
    }

    private fun restoreSessionIfNeeded() {
        lifecycleScope.launch {
            try {
                if (!SupabaseClient.isAuthenticated()) {
                    val prefs = getSharedPreferences("fooder_auth", Context.MODE_PRIVATE)
                    SupabaseClient.restoreSession(prefs)
                }
                ApiClient.updateAuthToken()
            } catch (_: Exception) { }
        }
    }

    private fun setupBottomNavigation() {
        bottomNavigation.setOnItemSelectedListener { item ->
            when (item.itemId) {
                R.id.nav_health   -> { titleText.text = "Health+";  openFragment(HealthConditionsFragment());    true }
                R.id.nav_scan     -> { titleText.text = "Scan";     openFragment(MenuOcrFragment());             true }
                R.id.nav_profile  -> { titleText.text = "Profile";  openFragment(ProfileFragment());             true }
                else -> false
            }
        }
    }

    private fun openFragment(fragment: Fragment) {
        supportFragmentManager.beginTransaction()
            .replace(R.id.content_container, fragment)
            .commit()
    }
}
