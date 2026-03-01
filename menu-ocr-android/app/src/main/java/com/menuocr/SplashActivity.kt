package com.menuocr

import android.animation.AnimatorSet
import android.animation.ObjectAnimator
import android.content.Intent
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.animation.OvershootInterpolator
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsControllerCompat

class SplashActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        WindowCompat.setDecorFitsSystemWindows(window, false)
        window.statusBarColor = android.graphics.Color.parseColor("#FA3D2E")
        window.navigationBarColor = android.graphics.Color.parseColor("#FA3D2E")
        WindowInsetsControllerCompat(window, window.decorView).apply {
            isAppearanceLightStatusBars = false
            isAppearanceLightNavigationBars = false
        }

        // Build layout programmatically
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            val gradient = GradientDrawable(
                GradientDrawable.Orientation.TOP_BOTTOM,
                intArrayOf(
                    android.graphics.Color.parseColor("#FA3D2E"),
                    android.graphics.Color.parseColor("#E02E1F")
                )
            )
            background = gradient
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.MATCH_PARENT
            )
        }

        // Fork/knife icon
        val iconView = ImageView(this).apply {
            setImageResource(R.drawable.ic_splash_fork)
            val size = (80 * resources.displayMetrics.density).toInt()
            layoutParams = LinearLayout.LayoutParams(size, size).apply {
                gravity = Gravity.CENTER_HORIZONTAL
                bottomMargin = (16 * resources.displayMetrics.density).toInt()
            }
            setColorFilter(android.graphics.Color.WHITE)
            scaleX = 0f
            scaleY = 0f
            alpha = 0f
        }

        // App name
        val nameText = TextView(this).apply {
            text = "Foodit"
            setTextColor(android.graphics.Color.WHITE)
            textSize = 36f
            typeface = android.graphics.Typeface.create("sans-serif-medium", android.graphics.Typeface.BOLD)
            gravity = Gravity.CENTER
            alpha = 0f
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply { gravity = Gravity.CENTER_HORIZONTAL }
        }

        // Tagline
        val taglineText = TextView(this).apply {
            text = "Scan · Discover · Eat Healthy"
            setTextColor(android.graphics.Color.argb(220, 255, 255, 255))
            textSize = 16f
            gravity = Gravity.CENTER
            alpha = 0f
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                gravity = Gravity.CENTER_HORIZONTAL
                topMargin = (8 * resources.displayMetrics.density).toInt()
            }
        }

        root.addView(iconView)
        root.addView(nameText)
        root.addView(taglineText)
        setContentView(root)

        // Animate
        startBreathAnimation(iconView, nameText, taglineText, root)
    }

    private fun startBreathAnimation(icon: ImageView, name: TextView, tagline: TextView, root: View) {
        // Phase 1: Icon springs in (0-600ms)
        val iconScaleX = ObjectAnimator.ofFloat(icon, "scaleX", 0f, 1.15f).apply { duration = 500 }
        val iconScaleY = ObjectAnimator.ofFloat(icon, "scaleY", 0f, 1.15f).apply { duration = 500 }
        val iconAlpha = ObjectAnimator.ofFloat(icon, "alpha", 0f, 1f).apply { duration = 300 }
        val phase1 = AnimatorSet().apply {
            playTogether(iconScaleX, iconScaleY, iconAlpha)
            interpolator = OvershootInterpolator(2.0f)
        }

        // Phase 2: Icon settles (600-800ms)
        val settleX = ObjectAnimator.ofFloat(icon, "scaleX", 1.15f, 1.0f).apply { duration = 200 }
        val settleY = ObjectAnimator.ofFloat(icon, "scaleY", 1.15f, 1.0f).apply { duration = 200 }
        val phase2 = AnimatorSet().apply { playTogether(settleX, settleY) }

        // Phase 3: Name fades in (800-1200ms)
        val nameAlpha = ObjectAnimator.ofFloat(name, "alpha", 0f, 1f).apply { duration = 400 }
        val nameTransY = ObjectAnimator.ofFloat(name, "translationY", 20f, 0f).apply { duration = 400 }
        val phase3 = AnimatorSet().apply { playTogether(nameAlpha, nameTransY) }

        // Phase 4: Tagline fades in (1200-1600ms)
        val tagAlpha = ObjectAnimator.ofFloat(tagline, "alpha", 0f, 1f).apply { duration = 400 }
        val tagTransY = ObjectAnimator.ofFloat(tagline, "translationY", 15f, 0f).apply { duration = 400 }
        val phase4 = AnimatorSet().apply { playTogether(tagAlpha, tagTransY) }

        // Phase 5: Gentle pulse (1600-2200ms)
        val pulseUpX = ObjectAnimator.ofFloat(icon, "scaleX", 1.0f, 1.08f).apply { duration = 300 }
        val pulseUpY = ObjectAnimator.ofFloat(icon, "scaleY", 1.0f, 1.08f).apply { duration = 300 }
        val pulseDownX = ObjectAnimator.ofFloat(icon, "scaleX", 1.08f, 1.0f).apply { duration = 300 }
        val pulseDownY = ObjectAnimator.ofFloat(icon, "scaleY", 1.08f, 1.0f).apply { duration = 300 }
        val phase5 = AnimatorSet().apply {
            play(pulseUpX).with(pulseUpY)
            play(pulseDownX).with(pulseDownY).after(pulseUpX)
        }

        // Phase 6: Fade out everything (2200-2700ms)
        val fadeAll = ObjectAnimator.ofFloat(root, "alpha", 1f, 0f).apply { duration = 400 }

        // Chain all phases
        val fullAnimation = AnimatorSet().apply {
            playSequentially(phase1, phase2, phase3, phase4, phase5, fadeAll)
            startDelay = 200
        }

        fullAnimation.addListener(object : android.animation.AnimatorListenerAdapter() {
            override fun onAnimationEnd(animation: android.animation.Animator) {
                navigateToMain()
            }
        })

        fullAnimation.start()
    }

    private fun navigateToMain() {
        startActivity(Intent(this, DoorDashMainActivity::class.java))
        overridePendingTransition(android.R.anim.fade_in, android.R.anim.fade_out)
        finish()
    }
}
