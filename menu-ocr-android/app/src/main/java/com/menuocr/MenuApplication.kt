package com.menuocr

import android.app.Application
import android.util.Log
import com.google.android.gms.security.ProviderInstaller
import org.maplibre.android.MapLibre
import org.maplibre.android.WellKnownTileServer

class MenuApplication : Application() {
    override fun onCreate() {
        super.onCreate()

        // ── MapLibre ──────────────────────────────────────────────────────────
        MapLibre.getInstance(this, null, WellKnownTileServer.MapLibre)

        // ── Security provider ─────────────────────────────────────────────────
        try {
            ProviderInstaller.installIfNeeded(this)
        } catch (e: Exception) {
            Log.w("MenuApplication", "Security provider update failed: ${e.message}")
        }
    }
}
