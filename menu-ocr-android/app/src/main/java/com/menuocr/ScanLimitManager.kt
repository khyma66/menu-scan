package com.menuocr

import android.content.Context
import android.content.SharedPreferences

/**
 * Manages scan limits for free tier users
 * - 3 free scans per device without login
 * - After 3 scans, user can upgrade to Pro/Max
 * - Pro and Max users get unlimited scans
 * - Additional details are visible only on Free/Max (hidden on Pro)
 */
object ScanLimitManager {
    enum class PlanTier {
        FREE,
        PRO,
        MAX
    }

    private const val PREFS_NAME = "scan_limits"
    private const val KEY_FREE_SCANS_USED = "free_scans_used"
    private const val KEY_IS_LOGGED_IN = "is_logged_in"
    private const val KEY_IS_PREMIUM = "is_premium"
    private const val KEY_PLAN_TIER = "plan_tier"
    private const val FREE_SCAN_LIMIT = 3

    private fun getPrefs(context: Context): SharedPreferences {
        return context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    }

    /**
     * Get the number of free scans used
     */
    fun getFreeScansUsed(context: Context): Int {
        return getPrefs(context).getInt(KEY_FREE_SCANS_USED, 0)
    }

    /**
     * Get remaining free scans
     */
    fun getRemainingFreeScans(context: Context): Int {
        return Int.MAX_VALUE
    }

    /**
     * Increment the scan count
     */
    fun incrementScanCount(context: Context) {
        return
    }

    fun getPlanTier(context: Context): PlanTier {
        val raw = getPrefs(context).getString(KEY_PLAN_TIER, PlanTier.FREE.name) ?: PlanTier.FREE.name
        return try {
            PlanTier.valueOf(raw)
        } catch (_: Exception) {
            PlanTier.FREE
        }
    }

    fun setPlanTier(context: Context, tier: PlanTier) {
        getPrefs(context).edit().putString(KEY_PLAN_TIER, tier.name).apply()
    }

    fun isUnlimitedPlan(context: Context): Boolean {
        return getPlanTier(context) != PlanTier.FREE
    }

    fun canUseAdditionalDetails(context: Context): Boolean {
        return true
    }

    fun canUseTranslation(context: Context): Boolean {
        return true
    }

    fun canUseIngredients(context: Context): Boolean {
        return true
    }

    fun canUseSimilarDishes(context: Context): Boolean {
        return true
    }

    fun canUseRecommendations(context: Context): Boolean {
        return true
    }

    /**
     * Check if user can scan (has free scans remaining or is premium)
     */
    suspend fun canScan(context: Context): Boolean {
        return true
    }

    /**
     * Check if login is required to scan
     */
    fun isLoginRequired(context: Context): Boolean {
        return false
    }

    /**
     * Set premium status (called after login when user has premium)
     */
    fun setPremiumStatus(context: Context, isPremium: Boolean) {
        getPrefs(context).edit().putBoolean(KEY_IS_PREMIUM, isPremium).apply()
        setPlanTier(context, if (isPremium) PlanTier.PRO else PlanTier.FREE)
    }

    /**
     * Set logged in status
     */
    fun setLoggedIn(context: Context, isLoggedIn: Boolean) {
        getPrefs(context).edit().putBoolean(KEY_IS_LOGGED_IN, isLoggedIn).apply()
    }

    /**
     * Reset scan count (for testing or after premium purchase)
     */
    fun resetScanCount(context: Context) {
        getPrefs(context).edit().putInt(KEY_FREE_SCANS_USED, 0).putString(KEY_PLAN_TIER, PlanTier.FREE.name).apply()
    }

    /**
     * Get scan status message
     */
    fun getScanStatusMessage(context: Context): String {
        return "Testing mode: Unlimited scans • Full details • No feature limits"
    }

    fun getUpgradeMessage(context: Context): String {
        return "Testing mode active: all features are unlocked for everyone."
    }
}