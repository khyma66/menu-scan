package com.menuocr

import android.animation.AnimatorSet
import android.animation.ObjectAnimator
import android.content.Context
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
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch
import kotlinx.coroutines.withTimeoutOrNull

class SplashActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Edge-to-edge very light violet
        WindowCompat.setDecorFitsSystemWindows(window, false)
        val lightViolet = android.graphics.Color.parseColor("#F3F0FF")
        window.statusBarColor = lightViolet
        window.navigationBarColor = lightViolet
        WindowInsetsControllerCompat(window, window.decorView).apply {
            isAppearanceLightStatusBars = true
            isAppearanceLightNavigationBars = true
        }

        // Root with very light violet gradient
        val root = FrameLayout(this).apply {
            val gradient = GradientDrawable(
                GradientDrawable.Orientation.TL_BR,
                intArrayOf(
                    android.graphics.Color.parseColor("#F3F0FF"),
                    android.graphics.Color.parseColor("#EDE5FF")
                )
            )
            background = gradient
            layoutParams = FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT
            )
        }

        // Logo - device-adaptive size (70% of screen width, no cap)
        val screenWidth = resources.displayMetrics.widthPixels
        val logoWidth = (screenWidth * 0.70f).toInt()
        val glowSize = (screenWidth * 0.85f).toInt()

        // Glow circle behind the logo
        val glow = View(this).apply {
            val glowDrawable = android.graphics.drawable.GradientDrawable().apply {
                shape = android.graphics.drawable.GradientDrawable.OVAL
                setColor(android.graphics.Color.argb(30, 124, 58, 237))
                setSize(glowSize, glowSize)
            }
            background = glowDrawable
            alpha = 0f
            scaleX = 0.4f
            scaleY = 0.4f
            layoutParams = FrameLayout.LayoutParams(glowSize, glowSize, Gravity.CENTER)
        }

        // Logo — uses the same tomato mascot vector as the Discover tab
        // so the brand icon is identical everywhere in the app.
        val logoSize = (screenWidth * 0.45f).toInt()

        val iconView = ImageView(this).apply {
            setImageResource(R.drawable.ic_app_logo)
            scaleType = ImageView.ScaleType.FIT_CENTER
            adjustViewBounds = true
            scaleX = 0f
            scaleY = 0f
            alpha = 0f
            layoutParams = FrameLayout.LayoutParams(
                logoSize,
                logoSize,
                Gravity.CENTER
            )
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
        val glowAlpha = ObjectAnimator.ofFloat(glow, "alpha", 0f, 0.85f).apply { duration = 500 }
        val glowScaleX = ObjectAnimator.ofFloat(glow, "scaleX", 0.4f, 1.2f).apply { duration = 500 }
        val glowScaleY = ObjectAnimator.ofFloat(glow, "scaleY", 0.4f, 1.2f).apply { duration = 500 }
        val phase1 = AnimatorSet().apply {
            playTogether(iconScaleX, iconScaleY, iconAlpha, glowAlpha, glowScaleX, glowScaleY)
            interpolator = OvershootInterpolator(2.0f)
        }

        // Phase 2: Settle (600-800ms)
        val settleX = ObjectAnimator.ofFloat(icon, "scaleX", 1.15f, 1.0f).apply { duration = 200 }
        val settleY = ObjectAnimator.ofFloat(icon, "scaleY", 1.15f, 1.0f).apply { duration = 200 }
        val glowSettleX = ObjectAnimator.ofFloat(glow, "scaleX", 1.2f, 1.0f).apply { duration = 200 }
        val glowSettleY = ObjectAnimator.ofFloat(glow, "scaleY", 1.2f, 1.0f).apply { duration = 200 }
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
        lifecycleScope.launch {
            val prefs = getSharedPreferences("fooder_auth", Context.MODE_PRIVATE)
            // 8-second timeout prevents an indefinite hang on slow networks.
            // If the check times out, fall through to LoginActivity so the user
            // can sign in manually; their saved tokens are NOT cleared.
            val hasSession = withTimeoutOrNull(8_000L) {
                SupabaseClient.restoreSession(prefs)
            } ?: false

            if (hasSession) {
                ApiClient.updateAuthToken()
            }
            val destination = if (hasSession) {
                DoorDashMainActivity::class.java
            } else {
                LoginActivity::class.java
            }
            startActivity(Intent(this@SplashActivity, destination))
            overridePendingTransition(android.R.anim.fade_in, android.R.anim.fade_out)
            finish()
        }
    }
}
