package com.menuocr

import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.FrameLayout
import android.widget.ImageButton
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsControllerCompat
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch

/**
 * Branded in-app OAuth WebView activity.
 * Shows Fooder logo at the top instead of exposing the Supabase domain in a Chrome Custom Tab.
 */
class OAuthWebViewActivity : AppCompatActivity() {

    companion object {
        private const val EXTRA_URL = "extra_url"

        fun launch(context: Context, url: String) {
            val i = Intent(context, OAuthWebViewActivity::class.java)
            i.putExtra(EXTRA_URL, url)
            context.startActivity(i)
        }
    }

    private lateinit var webView: WebView
    private lateinit var loadingBar: ProgressBar

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Edge-to-edge light violet matching splash
        WindowCompat.setDecorFitsSystemWindows(window, false)
        val headerBg = Color.parseColor("#F3F0FF")
        window.statusBarColor = headerBg
        window.navigationBarColor = Color.WHITE
        WindowInsetsControllerCompat(window, window.decorView).apply {
            isAppearanceLightStatusBars = true
            isAppearanceLightNavigationBars = true
        }

        val url = intent.getStringExtra(EXTRA_URL) ?: run { finish(); return }

        // ── Root layout ───────────────────────────────────────────────────────
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            layoutParams = FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT
            )
        }

        // ── Fooder header ─────────────────────────────────────────────────────
        val statusBarHeight = getStatusBarHeight()
        val header = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setBackgroundColor(headerBg)
            gravity = Gravity.CENTER_VERTICAL
            setPadding(0, statusBarHeight, 0, 0)
            val dp = resources.displayMetrics.density
            minimumHeight = (56 * dp).toInt() + statusBarHeight
        }

        val closeBtn = ImageButton(this).apply {
            setImageResource(android.R.drawable.ic_menu_close_clear_cancel)
            setBackgroundColor(Color.TRANSPARENT)
            val dp = resources.displayMetrics.density
            val size = (48 * dp).toInt()
            layoutParams = LinearLayout.LayoutParams(size, size)
            setColorFilter(Color.parseColor("#666666"))
            setOnClickListener { finish() }
            contentDescription = "Close"
        }

        val logoIcon = ImageView(this).apply {
            setImageResource(R.drawable.ic_app_logo)
            val dp = resources.displayMetrics.density
            val size = (32 * dp).toInt()
            layoutParams = LinearLayout.LayoutParams(size, size).apply {
                marginStart = (8 * dp).toInt()
            }
            scaleType = ImageView.ScaleType.FIT_CENTER
            adjustViewBounds = true
        }

        val appNameText = TextView(this).apply {
            text = getString(R.string.app_name)
            textSize = 18f
            setTextColor(Color.parseColor("#222222"))
            setTypeface(typeface, android.graphics.Typeface.BOLD)
            val dp = resources.displayMetrics.density
            setPadding((10 * dp).toInt(), 0, 0, 0)
            layoutParams = LinearLayout.LayoutParams(
                0,
                LinearLayout.LayoutParams.WRAP_CONTENT,
                1f
            )
        }

        header.addView(closeBtn)
        header.addView(logoIcon)
        header.addView(appNameText)

        // ── Loading bar ───────────────────────────────────────────────────────
        loadingBar = ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal).apply {
            isIndeterminate = true
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                (3 * resources.displayMetrics.density).toInt()
            )
            progressDrawable = android.graphics.drawable.ColorDrawable(Color.parseColor("#7C3AED"))
        }

        // ── WebView ───────────────────────────────────────────────────────────
        webView = WebView(this).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                0,
                1f
            )
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.setSupportZoom(false)

            webViewClient = object : WebViewClient() {
                override fun shouldOverrideUrlLoading(
                    view: WebView?,
                    request: WebResourceRequest?
                ): Boolean {
                    val uri = request?.url ?: return false
                    // Intercept auth callback deep-link and hand off to LoginActivity
                    if (uri.scheme == "com.menuocr" && uri.host == "auth-callback") {
                        handleCallback(uri)
                        return true
                    }
                    return false
                }

                override fun onPageFinished(view: WebView?, url: String?) {
                    loadingBar.visibility = View.GONE
                }
            }
        }

        root.addView(header)
        root.addView(loadingBar)
        root.addView(webView)
        setContentView(root)

        webView.loadUrl(url)
    }

    private fun handleCallback(uri: Uri) {
        loadingBar.visibility = View.VISIBLE
        lifecycleScope.launch {
            try {
                val result = SupabaseClient.handleOAuthCallback(uri)
                result.fold(
                    onSuccess = {
                        val prefs = getSharedPreferences("fooder_auth", Context.MODE_PRIVATE)
                        SupabaseClient.saveSession(prefs)
                        ApiClient.updateAuthToken()
                        val intent = Intent(this@OAuthWebViewActivity, DoorDashMainActivity::class.java)
                        intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                        startActivity(intent)
                    },
                    onFailure = {
                        finish()
                    }
                )
            } catch (_: Exception) {
                finish()
            }
        }
    }

    private fun getStatusBarHeight(): Int {
        val resourceId = resources.getIdentifier("status_bar_height", "dimen", "android")
        return if (resourceId > 0) resources.getDimensionPixelSize(resourceId) else 0
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) webView.goBack() else super.onBackPressed()
    }
}
