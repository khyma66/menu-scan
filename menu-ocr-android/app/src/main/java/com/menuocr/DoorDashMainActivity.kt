package com.menuocr

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.fragment.app.Fragment
import androidx.fragment.app.FragmentManager
import androidx.fragment.app.FragmentPagerAdapter
import androidx.viewpager.widget.ViewPager
import com.google.android.material.tabs.TabLayout

class DoorDashMainActivity : AppCompatActivity() {

    private lateinit var viewPager: ViewPager
    private lateinit var tabLayout: TabLayout

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_doordash_main)

        // Initialize views
        viewPager = findViewById(R.id.view_pager)
        tabLayout = findViewById(R.id.tab_layout)

        // Setup ViewPager with adapter
        val adapter = ViewPagerAdapter(supportFragmentManager)
        viewPager.adapter = adapter

        // Connect TabLayout with ViewPager
        tabLayout.setupWithViewPager(viewPager)
    }

    private inner class ViewPagerAdapter(fm: FragmentManager) : FragmentPagerAdapter(fm, BEHAVIOR_RESUME_ONLY_CURRENT_FRAGMENT) {

        override fun getCount(): Int = 3

        override fun getItem(position: Int): Fragment {
            return when (position) {
                0 -> RestaurantDiscoveryFragment()
                1 -> MenuOcrFragment()
                2 -> GoogleDriveFragment()
                else -> RestaurantDiscoveryFragment()
            }
        }

        override fun getPageTitle(position: Int): CharSequence? {
            return when (position) {
                0 -> "🍽️ Restaurant Discovery"
                1 -> "📱 Menu OCR"
                2 -> "☁️ Google Drive"
                else -> ""
            }
        }
    }
}