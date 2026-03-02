#!/usr/bin/env python3
"""Rewrite Android SplashActivity.kt: logo-only, deep purple gradient, no text."""

TARGET = "/Users/mohanakrishnanarsupalli/menu-ocr/menu-ocr-android/app/src/main/java/com/menuocr/SplashActivity.kt"

content = '''package com.menuocr

import android.animation.AnimatorSet
import android.animation.ObjectAnimator
import android.content.Intent
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.animation.OvershootInterpolator
import android.widget.FrameLayout
import android.widget.ImageView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsControllerCompat

class SplashActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Edge-to-edge deep purple
        WindowCompat.setDecorFitsSystemWindows(window, false)
        val deepPurple = android.graphics.Color.parseColor("#2D1B69")
        window.statusBarColor = deepPurple
        window.navigationBarColor = deepPurple
        WindowInsetsControllerCompat(window, window.decorView).apply {
            isAppearanceLightStatusBars = false
            isAppearanceLightNavigationBars = false
        }

        // Root with gradient
        val root = FrameLayout(this).apply {
            val gradient = GradientDrawable(
                GradientDrawable.Orientation.TL_BR,
                intArrayOf(
                    android.graphics.Color.parseColor("#2D1B69"),
                    android.graphics.Color.parseColor("#7C3AED")
                )
            )
            background = gradient
            layoutParams = FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT
            )
        }

        // Subtle glow circle behind logo
        val glowSize = (200 * resources.displayMetrics.density).toInt()
        val glow = View(this).apply {
            val shape = GradientDrawable()
            shape.shape = GradientDrawable.OVAL
            shape.setColor(android.graphics.Color.argb(20, 255, 255, 255))
            background = shape
            alpha = 0f
            scaleX = 0.5f
            scaleY = 0.5f
            layoutParams = FrameLayout.LayoutParams(glowSize, glowSize, Gravity.CENTER)
        }

        // Logo - device-adaptive size (40% of screen width, max 180dp)
        val screenWidth = resources.displayMetrics.widthPixels
        val maxSize = (180 * resources.displayMetrics.density).toInt()
        val logoSize = minOf((screenWidth * 0.4f).toInt(), maxSize)
        val iconView = ImageView(this).apply {
            setImageResource(R.drawable.ic_splash_logo)
            scaleType = ImageView.ScaleType.FIT_CENTER
            // Rounded corners via outline
            clipToOutline = true
            outlineProvider = object : android.view.ViewOutlineProvider() {
                override fun getOutline(view: View?, outline: android.graphics.Outline?) {
                    outline?.setRoundRect(0, 0, view?.width ?: 0, view?.height ?: 0,
                        28 * resources.displayMetrics.density)
                }
            }
            elevation = 16f
            scaleX = 0f
            scaleY = 0f
            alpha = 0f
            layoutParams = FrameLayout.LayoutParams(logoSize, logoSize, Gravity.CENTER)
        }

        root.addView(glow)
        root.addView(iconView)
        setContentView(root)

        startBreatheAnimation(iconView, glow, root)
    }

    private fun startBreatheAnimation(icon: ImageView, glow: View, root: View) {
        // Phase 1: Spring in (0-600ms)
        val iconScaleX = ObjectAnimator.ofFloat(icon, "scaleX", 0f, 1.15f).apply { duration = 500 }
        val iconScaleY = ObjectAnimator.ofFloat(icon, "scaleY", 0f, 1.15f).apply { duration = 500 }
        val iconAlpha = ObjectAnimator.ofFloat(icon, "alpha", 0f, 1f).apply { duration = 300 }
        val glowAlpha = ObjectAnimator.ofFloat(glow, "alpha", 0f, 1f).apply { duration = 400 }
        val glowScaleX = ObjectAnimator.ofFloat(glow, "scaleX", 0.5f, 1.1f).apply { duration = 500 }
        val glowScaleY = ObjectAnimator.ofFloat(glow, "scaleY", 0.5f, 1.1f).apply { duration = 500 }
        val phase1 = AnimatorSet().apply {
            playTogether(iconScaleX, iconScaleY, iconAlpha, glowAlpha, glowScaleX, glowScaleY)
            interpolator = OvershootInterpolator(2.0f)
        }

        // Phase 2: Settle (600-800ms)
        val settleX = ObjectAnimator.ofFloat(icon, "scaleX", 1.15f, 1.0f).apply { duration = 200 }
        val settleY = ObjectAnimator.ofFloat(icon, "scaleY", 1.15f, 1.0f).apply { duration = 200 }
        val glowSettleX = ObjectAnimator.ofFloat(glow, "scaleX", 1.1f, 1.0f).apply { duration = 200 }
        val glowSettleY = ObjectAnimator.ofFloat(glow, "scaleY", 1.1f, 1.0f).apply { duration = 200 }
        val phase2 = AnimatorSet().apply { playTogether(settleX, settleY, glowSettleX, glowSettleY) }

        // Phase 3: Gentle pulse (800-1400ms)
        val pulseUpX = ObjectAnimator.ofFloat(icon, "scaleX", 1.0f, 1.06f).apply { duration = 300 }
        val pulseUpY = ObjectAnimator.ofFloat(icon, "scaleY", 1.0f, 1.06f).apply { duration = 300 }
        val pulseDownX = ObjectAnimator.ofFloat(icon, "scaleX", 1.06f, 1.0f).apply { duration = 300 }
        val pulseDownY = ObjectAnimator.ofFloat(icon, "scaleY", 1.06f, 1.0f).apply { duration = 300 }
        val phase3 = AnimatorSet().apply {
            play(pulseUpX).with(pulseUpY)
            play(pulseDownX).with(pulseDownY).after(pulseUpX)
        }

        // Phase 4: Fade out
        val fadeAll = ObjectAnimator.ofFloat(root, "alpha", 1f, 0f).apply { duration = 350 }

        val fullAnimation = AnimatorSet().apply {
            playSequentially(phase1, phase2, phase3, fadeAll)
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
'''

with open(TARGET, 'w') as f:
    f.write(content)

print(f"Written: {content.count(chr(10))} lines")
print(f"No 'Fooder': {'Fooder' not in content}")
print(f"No tagline: {'tagline' not in content}")
print(f"Has #2D1B69: {'#2D1B69' in content}")
