package com.menuocr

import android.content.Intent
import android.os.Bundle
import android.util.Log
import android.view.View
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch

class ProfileActivity : AppCompatActivity() {

    companion object {
        private const val PROFILE_PREFS = "user_profile"
        private const val KEY_CONTACT = "contact"
        private const val KEY_COUNTRY = "country"
        private const val KEY_PLAN_NAME = "plan_name"
        private const val KEY_CARD_MASK = "card_mask"
        private const val KEY_LOCAL_PAYMENT_LOG = "local_payment_log"
        private const val PRO_PLAN_AMOUNT_CENTS = 699
        private const val MAX_PLAN_AMOUNT_CENTS = 999
    }

    private lateinit var profileNameHeader: TextView
    private lateinit var profileEmailHeader: TextView
    private lateinit var inputName: EditText
    private lateinit var inputEmail: EditText
    private lateinit var inputContact: EditText
    private lateinit var inputCountry: EditText
    private lateinit var scansSummary: TextView
    private lateinit var scanHistoryText: TextView
    private lateinit var subscriptionText: TextView
    private lateinit var cardInfoText: TextView
    private lateinit var paymentHistoryText: TextView
    private lateinit var loadingText: TextView
    private lateinit var btnSaveProfile: Button
    private lateinit var btnBackProfile: Button
    private lateinit var btnResetPassword: Button
    private lateinit var btnLogout: Button
    private lateinit var btnDeleteAccount: Button
    private lateinit var btnSaveCard: Button
    private lateinit var btnPlanFree: Button
    private lateinit var btnPlanPro: Button
    private lateinit var btnPlanMax: Button
    private lateinit var btnTabDetails: Button
    private lateinit var btnTabPayment: Button
    private lateinit var btnTabScans: Button
    private lateinit var btnTabSubscription: Button
    private lateinit var sectionDetails: View
    private lateinit var sectionPayment: View
    private lateinit var sectionScans: View
    private lateinit var sectionSubscription: View
    private lateinit var inputCardNumber: EditText
    private lateinit var inputCardExpiry: EditText
    private lateinit var inputCardCvv: EditText
    private lateinit var loadingProgress: LinearLayout

    private enum class TabType { DETAILS, PAYMENT, SCANS, SUBSCRIPTION }

    private val paymentService by lazy { ApiClient.getPaymentService() }
    private val apiService by lazy { ApiClient.getApiService() }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_profile)

        // Initialize views
        profileNameHeader = findViewById(R.id.profile_name_header)
        profileEmailHeader = findViewById(R.id.profile_email_header)
        inputName = findViewById(R.id.input_name)
        inputEmail = findViewById(R.id.input_email)
        inputContact = findViewById(R.id.input_contact)
        inputCountry = findViewById(R.id.input_country)
        scansSummary = findViewById(R.id.scans_summary)
        scanHistoryText = findViewById(R.id.scan_history_text)
        subscriptionText = findViewById(R.id.subscription_text)
        cardInfoText = findViewById(R.id.card_info_text)
        paymentHistoryText = findViewById(R.id.payment_history_text)
        loadingText = findViewById(R.id.loading_text)
        btnSaveProfile = findViewById(R.id.btn_save_profile)
        btnBackProfile = findViewById(R.id.btn_back_profile)
        btnResetPassword = findViewById(R.id.btn_reset_password)
        btnLogout = findViewById(R.id.btn_logout)
        btnDeleteAccount = findViewById(R.id.btn_delete_account)
        btnSaveCard = findViewById(R.id.btn_save_card)
        btnPlanFree = findViewById(R.id.btn_plan_free)
        btnPlanPro = findViewById(R.id.btn_plan_pro)
        btnPlanMax = findViewById(R.id.btn_plan_max)
        btnTabDetails = findViewById(R.id.btn_tab_details)
        btnTabPayment = findViewById(R.id.btn_tab_payment)
        btnTabScans = findViewById(R.id.btn_tab_scans)
        btnTabSubscription = findViewById(R.id.btn_tab_subscription)
        sectionDetails = findViewById(R.id.section_details)
        sectionPayment = findViewById(R.id.section_payment)
        sectionScans = findViewById(R.id.section_scans)
        sectionSubscription = findViewById(R.id.section_subscription)
        inputCardNumber = findViewById(R.id.input_card_number)
        inputCardExpiry = findViewById(R.id.input_card_expiry)
        inputCardCvv = findViewById(R.id.input_card_cvv)
        loadingProgress = findViewById(R.id.loading_progress)

        setupClickListeners()
        selectTab(TabType.DETAILS)
        loadUserProfile()
        loadRecentScanDates()
        loadPaymentSection()
        loadPaymentDetails()
        loadSubscriptionSection()
    }

    private fun setupClickListeners() {
        btnBackProfile.setOnClickListener {
            onBackPressedDispatcher.onBackPressed()
        }

        btnSaveProfile.setOnClickListener {
            saveProfile()
        }

        btnResetPassword.setOnClickListener {
            resetPassword()
        }

        btnLogout.setOnClickListener {
            logout()
        }

        btnDeleteAccount.setOnClickListener {
            confirmDeleteAccount()
        }

        btnSaveCard.setOnClickListener {
            saveCardLocally()
        }

        btnPlanFree.setOnClickListener {
            setPlan("FREE", ScanLimitManager.PlanTier.FREE)
        }

        btnPlanPro.setOnClickListener {
            startPlanPurchase("PRO", PRO_PLAN_AMOUNT_CENTS, ScanLimitManager.PlanTier.PRO)
        }

        btnPlanMax.setOnClickListener {
            startPlanPurchase("MAX", MAX_PLAN_AMOUNT_CENTS, ScanLimitManager.PlanTier.MAX)
        }

        btnTabDetails.setOnClickListener { selectTab(TabType.DETAILS) }
        btnTabPayment.setOnClickListener { selectTab(TabType.PAYMENT) }
        btnTabScans.setOnClickListener { selectTab(TabType.SCANS) }
        btnTabSubscription.setOnClickListener { selectTab(TabType.SUBSCRIPTION) }
    }

    private fun selectTab(tab: TabType) {
        sectionDetails.visibility = if (tab == TabType.DETAILS) View.VISIBLE else View.GONE
        sectionPayment.visibility = if (tab == TabType.PAYMENT) View.VISIBLE else View.GONE
        sectionScans.visibility = if (tab == TabType.SCANS) View.VISIBLE else View.GONE
        sectionSubscription.visibility = if (tab == TabType.SUBSCRIPTION) View.VISIBLE else View.GONE

        setSubtabState(btnTabDetails, tab == TabType.DETAILS)
        setSubtabState(btnTabPayment, tab == TabType.PAYMENT)
        setSubtabState(btnTabScans, tab == TabType.SCANS)
        setSubtabState(btnTabSubscription, tab == TabType.SUBSCRIPTION)
    }

    private fun setSubtabState(button: Button, isActive: Boolean) {
        button.setBackgroundResource(
            if (isActive) R.drawable.profile_subtab_active else R.drawable.profile_subtab_inactive
        )
        button.setTextColor(
            if (isActive) getColor(R.color.white) else getColor(R.color.gray_900)
        )
    }

    private fun prefs() = getSharedPreferences(PROFILE_PREFS, MODE_PRIVATE)

    private fun loadSubscriptionSection() {
        subscriptionText.text = "Current: ${prefs().getString(KEY_PLAN_NAME, "FREE") ?: "FREE"}"
        updatePlanOptionVisibility()
    }

    private fun loadPaymentSection() {
        cardInfoText.text = "Card: ${prefs().getString(KEY_CARD_MASK, "Not stored") ?: "Not stored"}"
        val localLog = prefs().getString(KEY_LOCAL_PAYMENT_LOG, "") ?: ""
        if (localLog.isNotBlank()) {
            paymentHistoryText.text = localLog
        } else {
            paymentHistoryText.text = "Last payments will show here"
        }
    }

    private fun saveCardLocally() {
        val number = inputCardNumber.text.toString().trim()
        val expiry = inputCardExpiry.text.toString().trim()
        val cvv = inputCardCvv.text.toString().trim()

        if (number.length < 12 || expiry.isBlank() || cvv.length < 3) {
            Toast.makeText(this, "Enter valid card details", Toast.LENGTH_SHORT).show()
            return
        }

        val last4 = number.takeLast(4)
        val masked = "**** **** **** $last4 (exp $expiry)"
        prefs().edit().putString(KEY_CARD_MASK, masked).apply()
        cardInfoText.text = "Card: $masked"
        inputCardNumber.setText("")
        inputCardExpiry.setText("")
        inputCardCvv.setText("")
        Toast.makeText(this, "Card stored", Toast.LENGTH_SHORT).show()
    }

    private fun loadUserProfile() {
        showLoading("Loading profile...")

        lifecycleScope.launch {
            try {
                // Get current user from Supabase
                val user = SupabaseClient.getCurrentUser()
                val email = user?.email ?: "user@example.com"
                val name = user?.userMetadata?.get("name")?.toString()?.trim('"') ?: "User"

                // Load profile details from backend first, fallback to local
                val prefs = prefs()
                val backendProfile = try {
                    val profileResponse = apiService.getAppProfile()
                    if (profileResponse.isSuccessful) profileResponse.body() else null
                } catch (_: Exception) {
                    null
                }

                val displayName = backendProfile?.full_name?.takeIf { it.isNotBlank() } ?: name
                val displayEmail = backendProfile?.email?.takeIf { it.isNotBlank() } ?: email
                val contact = backendProfile?.contact ?: prefs.getString(KEY_CONTACT, "") ?: ""
                val country = backendProfile?.country ?: prefs.getString(KEY_COUNTRY, "") ?: ""

                profileNameHeader.text = displayName
                profileEmailHeader.text = displayEmail
                inputName.setText(displayName)
                inputEmail.setText(displayEmail)
                inputContact.setText(contact)
                inputCountry.setText(country)

                // Keep lightweight local cache as fallback
                prefs.edit()
                    .putString("name", displayName)
                    .putString("email", displayEmail)
                    .putString(KEY_CONTACT, contact)
                    .putString(KEY_COUNTRY, country)
                    .apply()

                updateScanSummary()
                loadPaymentSection()
                loadSubscriptionSection()
            } catch (e: Exception) {
                Log.e("ProfileActivity", "Failed to load user profile", e)
                loadLocalProfile()
            } finally {
                hideLoading()
            }
        }
    }

    private fun loadLocalProfile() {
        // Load from SharedPreferences
        val prefs = prefs()
        val name = prefs.getString("name", "User") ?: "User"
        val email = prefs.getString("email", "user@example.com") ?: "user@example.com"
        val contact = prefs.getString(KEY_CONTACT, "") ?: ""
        val country = prefs.getString(KEY_COUNTRY, "") ?: ""

        profileNameHeader.text = name
        profileEmailHeader.text = email
        inputName.setText(name)
        inputEmail.setText(email)
        inputContact.setText(contact)
        inputCountry.setText(country)

        updateScanSummary()
        loadPaymentSection()
        loadSubscriptionSection()
    }

    private fun saveProfile() {
        val name = inputName.text.toString().trim()
        val email = inputEmail.text.toString().trim()
        val contact = inputContact.text.toString().trim()
        val country = inputCountry.text.toString().trim()

        if (name.isEmpty()) {
            Toast.makeText(this, "Please enter your name", Toast.LENGTH_SHORT).show()
            return
        }

        showLoading("Saving profile...")

        lifecycleScope.launch {
            try {
                // Save to SharedPreferences
                val prefs = prefs()
                prefs.edit()
                    .putString("name", name)
                    .putString("email", email)
                    .putString(KEY_CONTACT, contact)
                    .putString(KEY_COUNTRY, country)
                    .apply()

                // Persist to backend
                try {
                    apiService.updateAppProfile(
                        AppProfileDetailsRequest(
                            full_name = name,
                            email = email.ifBlank { null },
                            contact = contact.ifBlank { null },
                            phone = contact.ifBlank { null },
                            country = country.ifBlank { null }
                        )
                    )
                } catch (e: Exception) {
                    Log.w("ProfileActivity", "Backend profile save failed: ${e.message}")
                }

                // Update header
                profileNameHeader.text = name

                Toast.makeText(this@ProfileActivity, "Profile saved successfully", Toast.LENGTH_SHORT).show()
            } catch (e: Exception) {
                Log.e("ProfileActivity", "Failed to save profile", e)
                Toast.makeText(this@ProfileActivity, "Failed to save profile: ${e.message}", Toast.LENGTH_SHORT).show()
            } finally {
                hideLoading()
            }
        }
    }

    private fun resetPassword() {
        val email = inputEmail.text.toString().trim()

        if (email.isEmpty() || email == "user@example.com") {
            Toast.makeText(this, "Password reset requires a valid email account. Please log in first.", Toast.LENGTH_LONG).show()
            return
        }

        showLoading("Sending reset email...")

        lifecycleScope.launch {
            try {
                val result = SupabaseClient.resetPassword(email)
                result.fold(
                    onSuccess = {
                        Toast.makeText(this@ProfileActivity, "Password reset email sent to $email", Toast.LENGTH_LONG).show()
                    },
                    onFailure = { error ->
                        Toast.makeText(this@ProfileActivity, "Failed to send reset email: ${error.message}", Toast.LENGTH_SHORT).show()
                    }
                )
            } catch (e: Exception) {
                Log.e("ProfileActivity", "Failed to send reset email", e)
                Toast.makeText(this@ProfileActivity, "Failed to send reset email: ${e.message}", Toast.LENGTH_SHORT).show()
            } finally {
                hideLoading()
            }
        }
    }

    private fun logout() {
        showLoading("Logging out...")

        lifecycleScope.launch {
            try {
                // Sign out from Supabase
                SupabaseClient.signOut()

                // Clear local profile
                val prefs = prefs()
                prefs.edit().clear().apply()
                ScanLimitManager.setLoggedIn(this@ProfileActivity, false)
                ApiClient.reset()

                Toast.makeText(this@ProfileActivity, "Logged out successfully", Toast.LENGTH_SHORT).show()

                // Navigate to login
                val intent = Intent(this@ProfileActivity, LoginActivity::class.java)
                intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                startActivity(intent)
                finish()
            } catch (e: Exception) {
                Log.e("ProfileActivity", "Failed to logout", e)
                Toast.makeText(this@ProfileActivity, "Logout failed: ${e.message}", Toast.LENGTH_SHORT).show()
                hideLoading()
            }
        }
    }

    private fun loadRecentScanDates() {
        lifecycleScope.launch {
            try {
                val response = apiService.getUserMenus()
                if (response.isSuccessful) {
                    val menus = response.body()?.menus.orEmpty()
                    if (menus.isEmpty()) {
                        scanHistoryText.text = "No scan history"
                    } else {
                        val dates = menus.mapNotNull { menu ->
                            menu.created_at?.take(10)
                        }.distinct().take(12)
                        val text = if (dates.isEmpty()) {
                            "No scan dates available"
                        } else {
                            dates.joinToString("\n") { "• $it" }
                        }
                        scanHistoryText.text = text
                        scansSummary.text = "Total scan dates: ${dates.size}"
                    }
                } else {
                    scanHistoryText.text = "Unable to load scan history"
                }
            } catch (e: Exception) {
                scanHistoryText.text = "Unable to load scan history"
            }
        }
        updateScanSummary()
    }

    private fun updateScanSummary() {
        scansSummary.text = "Testing mode: Unlimited scans • All additional details visible"
    }

    private fun startPlanPurchase(
        planLabel: String,
        amountCents: Int,
        targetTier: ScanLimitManager.PlanTier,
    ) {
        showLoading("Creating Stripe payment for $planLabel...")
        lifecycleScope.launch {
            try {
                val response = paymentService.createPaymentIntent(
                    PaymentIntentRequest(
                        amount = amountCents,
                        currency = "usd",
                        description = "$planLabel subscription upgrade",
                        metadata = mapOf("plan" to planLabel.lowercase())
                    )
                )

                if (response.isSuccessful && response.body() != null) {
                    val payment = response.body()!!
                    setPlan(planLabel, targetTier)
                    val previous = prefs().getString(KEY_LOCAL_PAYMENT_LOG, "") ?: ""
                    val newLine = "• ${payment.status} • ${payment.amount / 100.0} ${payment.currency.uppercase()}"
                    val updatedLog = (listOf(newLine) + previous.split("\n").filter { it.isNotBlank() }).take(8).joinToString("\n")
                    prefs().edit().putString(KEY_LOCAL_PAYMENT_LOG, updatedLog).apply()
                    Toast.makeText(this@ProfileActivity, "$planLabel activated", Toast.LENGTH_SHORT).show()
                    loadPaymentSection()
                    loadSubscriptionSection()
                    updateScanSummary()
                } else {
                    Toast.makeText(this@ProfileActivity, "Stripe payment setup failed", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Log.e("ProfileActivity", "Plan purchase failed", e)
                Toast.makeText(this@ProfileActivity, "Payment failed: ${e.localizedMessage ?: "unknown error"}", Toast.LENGTH_SHORT).show()
            } finally {
                hideLoading()
            }
        }
    }

    private fun setPlan(planName: String, tier: ScanLimitManager.PlanTier) {
        ScanLimitManager.setPlanTier(this, tier)
        prefs().edit().putString(KEY_PLAN_NAME, planName).apply()
        subscriptionText.text = "Current: $planName"
        updatePlanOptionVisibility()
    }

    private fun updatePlanOptionVisibility() {
        when (ScanLimitManager.getPlanTier(this)) {
            ScanLimitManager.PlanTier.FREE -> {
                btnPlanFree.visibility = View.GONE
                btnPlanPro.visibility = View.VISIBLE
                btnPlanMax.visibility = View.VISIBLE
            }
            ScanLimitManager.PlanTier.PRO -> {
                btnPlanFree.visibility = View.VISIBLE
                btnPlanPro.visibility = View.GONE
                btnPlanMax.visibility = View.VISIBLE
            }
            ScanLimitManager.PlanTier.MAX -> {
                btnPlanFree.visibility = View.VISIBLE
                btnPlanPro.visibility = View.VISIBLE
                btnPlanMax.visibility = View.GONE
            }
        }
    }

    private fun loadPaymentDetails() {
        lifecycleScope.launch {
            try {
                val response = apiService.getPaymentHistory()
                if (response.isSuccessful && response.body() != null) {
                    val body = response.body()!!
                    val subscriptions = body.subscriptions
                    val payments = body.payment_intents

                    if (subscriptions.isNotEmpty()) {
                        val sub = subscriptions.first()
                        val inferredPlan = inferPlanNameFromSubscription(sub)
                        subscriptionText.text = "Current: $inferredPlan"

                        val mappedTier = when (inferredPlan) {
                            "MAX" -> ScanLimitManager.PlanTier.MAX
                            "PRO", "PREMIUM" -> ScanLimitManager.PlanTier.PRO
                            else -> ScanLimitManager.PlanTier.FREE
                        }
                        setPlan(inferredPlan, mappedTier)
                    } else {
                        subscriptionText.text = "Current: FREE"
                    }

                    if (payments.isNotEmpty()) {
                        paymentHistoryText.text = payments.take(5).joinToString("\n") {
                            val amount = it.amount / 100.0
                            "• ${it.status} • $amount ${it.currency.uppercase()}"
                        }
                    } else {
                        loadPaymentSection()
                    }
                } else {
                    loadPaymentSection()
                }
            } catch (e: Exception) {
                loadPaymentSection()
            }
        }
    }

    private fun inferPlanNameFromSubscription(subscription: Subscription): String {
        val nickname = subscription.items.firstOrNull()?.price?.nickname?.lowercase().orEmpty()
        return when {
            "max" in nickname -> "MAX"
            "pro" in nickname || "premium" in nickname -> "PRO"
            else -> "FREE"
        }
    }

    private fun confirmDeleteAccount() {
        android.app.AlertDialog.Builder(this)
            .setTitle("Delete Account")
            .setMessage("This will permanently delete your account, scan history, health profile, and related data. Continue?")
            .setPositiveButton("Delete") { _, _ ->
                deleteAccount()
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    private fun deleteAccount() {
        showLoading("Deleting account...")
        lifecycleScope.launch {
            try {
                val response = apiService.deleteUserAccount()
                if (response.isSuccessful) {
                    SupabaseClient.signOut()
                    prefs().edit().clear().apply()
                    ScanLimitManager.setLoggedIn(this@ProfileActivity, false)
                    ApiClient.reset()
                    Toast.makeText(this@ProfileActivity, "Account deleted", Toast.LENGTH_LONG).show()
                    val intent = Intent(this@ProfileActivity, LoginActivity::class.java)
                    intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                    startActivity(intent)
                    finish()
                } else {
                    Toast.makeText(this@ProfileActivity, "Failed to delete account", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Log.e("ProfileActivity", "Delete account failed", e)
                Toast.makeText(this@ProfileActivity, "Delete account failed: ${e.message}", Toast.LENGTH_SHORT).show()
            } finally {
                hideLoading()
            }
        }
    }

    private fun showLoading(message: String) {
        loadingText.text = message
        loadingProgress.visibility = View.VISIBLE
    }

    private fun hideLoading() {
        loadingProgress.visibility = View.GONE
    }
}
