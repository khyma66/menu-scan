package com.menuocr

import android.os.Bundle
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.fragment.app.Fragment
import com.google.android.material.bottomnavigation.BottomNavigationView

class DoorDashMainActivity : AppCompatActivity() {

    private lateinit var bottomNavigation: BottomNavigationView
    private lateinit var titleText: TextView
    private var selectedTabId: Int = R.id.nav_discover

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_doordash_main)

        // Initialize views
        bottomNavigation = findViewById(R.id.bottom_navigation)
        titleText = findViewById(R.id.title_text)

        setupBottomNavigation()
        if (savedInstanceState == null) {
            openFragment(RestaurantDiscoveryFragment())
            bottomNavigation.selectedItemId = R.id.nav_discover
            titleText.text = "Discover"
        }

    }

    private fun setupBottomNavigation() {
        bottomNavigation.setOnItemSelectedListener { item ->
            when (item.itemId) {
                R.id.nav_discover -> {
                    selectedTabId = item.itemId
                    openFragment(RestaurantDiscoveryFragment())
                    titleText.text = "Discover"
                    true
                }
                R.id.nav_health -> {
                    selectedTabId = item.itemId
                    openFragment(HealthConditionsFragment())
                    titleText.text = "Health+"
                    true
                }
                R.id.nav_scan -> {
                    selectedTabId = item.itemId
                    openFragment(MenuOcrFragment())
                    titleText.text = "Scan"
                    true
                }
                R.id.nav_profile -> {
                    selectedTabId = item.itemId
                    titleText.text = "Profile"
                    openFragment(ProfileFragment())
                    true
                }
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
