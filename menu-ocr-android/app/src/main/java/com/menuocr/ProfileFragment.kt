package com.menuocr

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.CheckBox
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.Spinner
import android.widget.TextView
import android.widget.Toast
import androidx.browser.customtabs.CustomTabColorSchemeParams
import androidx.browser.customtabs.CustomTabsIntent
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch

class ProfileFragment : Fragment() {

    private enum class ProfileTab {
        PROFILE,
        PAYMENT,
        RECENT_PAYMENTS,
        SCANS,
        SUBSCRIPTION,
        NOTIFICATIONS
    }

    private lateinit var apiService: ApiService
    private var activeTab: ProfileTab = ProfileTab.PROFILE

    private lateinit var btnTabProfile: Button
    private lateinit var btnTabPayment: Button
    private var btnTabRecentPayments: Button? = null
    private lateinit var btnTabScans: Button
    private lateinit var btnTabSubscription: Button
    private lateinit var btnTabNotifications: Button

    private lateinit var sectionProfile: View
    private lateinit var sectionPayment: View
    private var sectionRecentPayments: View? = null
    private lateinit var sectionScans: View
    private lateinit var sectionSubscription: View
    private lateinit var sectionNotifications: View

    private lateinit var loadingProgress: LinearLayout
    private lateinit var loadingText: TextView

    private lateinit var profileNameHeader: TextView
    private lateinit var profileEmailHeader: TextView
    private lateinit var premiumBadge: TextView
    private var btnHeaderAuth: Button? = null
    private lateinit var statScans: TextView
    private lateinit var statPlan: TextView
    private lateinit var statStatus: TextView

    private var tvSignInProvider: TextView? = null
    private var btnSignOut: Button? = null
    private var btnManageSubscription: Button? = null

    private lateinit var inputName: EditText
    private lateinit var inputEmail: EditText
    private lateinit var inputContact: EditText
    private lateinit var inputCountry: EditText
    private lateinit var btnSaveProfile: Button

    private lateinit var inputCardHolder: EditText
    private lateinit var inputCardNumber: EditText
    private lateinit var inputCardExpiry: EditText
    private lateinit var inputCardCvv: EditText
    private lateinit var btnSaveCard: Button
    private lateinit var cardInfoText: TextView
    private lateinit var paymentHistoryText: TextView
    private var recentPaymentsText: TextView? = null

    private lateinit var scansSummary: TextView
    private lateinit var scanHistoryText: TextView

    private lateinit var subscriptionText: TextView
    private lateinit var btnPlanFree: Button
    private lateinit var btnPlanPro: Button
    private lateinit var btnPlanMax: Button
    private lateinit var tvPriceFree: TextView
    private lateinit var tvPricePro: TextView
    private lateinit var tvPriceMax: TextView

    private lateinit var checkNotificationsEnabled: CheckBox
    private lateinit var checkNotificationsPush: CheckBox
    private lateinit var checkNotificationsEmail: CheckBox
    private lateinit var btnSaveNotifications: Button

    private var currentPlanName: String = "FREE"

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_profile, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        apiService = ApiClient.getApiService()
        setupUI(view)
        setupListeners()
        selectTab(ProfileTab.PROFILE)
        loadAllProfileData()
    }

    private fun setupUI(view: View) {
        btnTabProfile = view.findViewById(R.id.btn_tab_profile)
        btnTabPayment = view.findViewById(R.id.btn_tab_payment)
        btnTabRecentPayments = view.findViewById(R.id.btn_tab_recent_payments)
        btnTabScans = view.findViewById(R.id.btn_tab_scans)
        btnTabSubscription = view.findViewById(R.id.btn_tab_subscription)
        btnTabNotifications = view.findViewById(R.id.btn_tab_notifications)

        sectionProfile = view.findViewById(R.id.section_profile)
        sectionPayment = view.findViewById(R.id.section_payment)
        sectionRecentPayments = view.findViewById(R.id.section_recent_payments)
        sectionScans = view.findViewById(R.id.section_scans)
        sectionSubscription = view.findViewById(R.id.section_subscription)
        sectionNotifications = view.findViewById(R.id.section_notifications)

        loadingProgress = view.findViewById(R.id.loading_progress)
        loadingText = view.findViewById(R.id.loading_text)

        profileNameHeader = view.findViewById(R.id.profile_name_header)
        profileEmailHeader = view.findViewById(R.id.profile_email_header)
        premiumBadge = view.findViewById(R.id.premium_badge)
        btnHeaderAuth = view.findViewById(R.id.btn_header_auth)
        statScans = view.findViewById(R.id.stat_scans)
        statPlan = view.findViewById(R.id.stat_plan)
        statStatus = view.findViewById(R.id.stat_status)

        inputName = view.findViewById(R.id.input_name)
        inputEmail = view.findViewById(R.id.input_email)
        inputContact = view.findViewById(R.id.input_contact)
        inputCountry = view.findViewById(R.id.input_country)
        btnSaveProfile = view.findViewById(R.id.btn_save_profile)
        btnSignOut = view.findViewById(R.id.btn_sign_out)
        btnManageSubscription = view.findViewById(R.id.btn_manage_subscription)

        inputCardHolder = view.findViewById(R.id.input_card_holder)
        inputCardNumber = view.findViewById(R.id.input_card_number)
        inputCardExpiry = view.findViewById(R.id.input_card_expiry)
        inputCardCvv = view.findViewById(R.id.input_card_cvv)
        btnSaveCard = view.findViewById(R.id.btn_save_card)
        cardInfoText = view.findViewById(R.id.card_info_text)
        paymentHistoryText = view.findViewById(R.id.payment_history_text)
        recentPaymentsText = view.findViewById(R.id.recent_payments_text)

        scansSummary = view.findViewById(R.id.scans_summary)
        scanHistoryText = view.findViewById(R.id.scan_history_text)

        subscriptionText = view.findViewById(R.id.subscription_text)
        btnPlanFree = view.findViewById(R.id.btn_plan_free)
        btnPlanPro = view.findViewById(R.id.btn_plan_pro)
        btnPlanMax = view.findViewById(R.id.btn_plan_max)
        tvPriceFree = view.findViewById(R.id.tv_price_free)
        tvPricePro = view.findViewById(R.id.tv_price_pro)
        tvPriceMax = view.findViewById(R.id.tv_price_max)

        checkNotificationsEnabled = view.findViewById(R.id.check_notifications_enabled)
        checkNotificationsPush = view.findViewById(R.id.check_notifications_push)
        checkNotificationsEmail = view.findViewById(R.id.check_notifications_email)
        btnSaveNotifications = view.findViewById(R.id.btn_save_notifications)

    }

    private fun setupListeners() {
        btnTabProfile.setOnClickListener { selectTab(ProfileTab.PROFILE) }
        btnTabPayment.setOnClickListener { selectTab(ProfileTab.PAYMENT) }
        btnTabRecentPayments?.setOnClickListener { selectTab(ProfileTab.RECENT_PAYMENTS) }
        btnTabScans.setOnClickListener { selectTab(ProfileTab.SCANS) }
        btnTabSubscription.setOnClickListener { selectTab(ProfileTab.SUBSCRIPTION) }
        btnTabNotifications.setOnClickListener { selectTab(ProfileTab.NOTIFICATIONS) }

        btnSaveProfile.setOnClickListener { saveProfile() }
        btnSaveCard.setOnClickListener { saveCard() }
        btnSaveNotifications.setOnClickListener { savePreferences() }
        btnSignOut?.setOnClickListener { handleLogout() }
        btnManageSubscription?.setOnClickListener { openManageSubscription() }

        btnPlanFree.setOnClickListener { selectPlan("FREE") }
        btnPlanPro.setOnClickListener { selectPlan("PRO") }
        btnPlanMax.setOnClickListener { selectPlan("MAX") }
    }

    private fun selectTab(tab: ProfileTab) {
        activeTab = tab

        sectionProfile.isVisible = tab == ProfileTab.PROFILE
        sectionPayment.isVisible = tab == ProfileTab.PAYMENT
        sectionRecentPayments?.isVisible = tab == ProfileTab.RECENT_PAYMENTS
        sectionScans.isVisible = tab == ProfileTab.SCANS
        sectionSubscription.isVisible = tab == ProfileTab.SUBSCRIPTION
        sectionNotifications.isVisible = tab == ProfileTab.NOTIFICATIONS

        setTabState(btnTabProfile, tab == ProfileTab.PROFILE)
        setTabState(btnTabPayment, tab == ProfileTab.PAYMENT)
        btnTabRecentPayments?.let { setTabState(it, tab == ProfileTab.RECENT_PAYMENTS) }
        setTabState(btnTabScans, tab == ProfileTab.SCANS)
        setTabState(btnTabSubscription, tab == ProfileTab.SUBSCRIPTION)
        setTabState(btnTabNotifications, tab == ProfileTab.NOTIFICATIONS)
    }

    private fun setTabState(button: Button, selected: Boolean) {
        if (selected) {
            button.setBackgroundResource(R.drawable.profile_subtab_active)
            button.setTextColor(resources.getColor(R.color.white, null))
        } else {
            button.setBackgroundResource(R.drawable.profile_subtab_inactive)
            button.setTextColor(resources.getColor(R.color.gray_900, null))
        }
    }

    private fun setLoading(show: Boolean, text: String = "Loading...") {
        loadingProgress.isVisible = show
        loadingText.text = text
    }

    override fun onResume() {
        super.onResume()
        viewLifecycleOwner.lifecycleScope.launch {
            refreshAuthHeader()
            // Reload profile data so form fields populate after login
            loadAllProfileData()
        }
    }

    private suspend fun refreshAuthHeader() {
        val user = try { SupabaseClient.getCurrentUser() } catch (e: Exception) { null }
        if (user != null) {
            // Prefer OAuth display name from metadata (Google/Apple provide 'name')
            val displayName = user.userMetadata?.get("name")?.toString()?.trim('"')
                ?: user.userMetadata?.get("full_name")?.toString()?.trim('"')
                ?: user.email?.substringBefore("@")?.replaceFirstChar { it.uppercase() }
                ?: "User"
            val provider = user.appMetadata?.get("provider")?.toString()?.trim('"')
                ?.replaceFirstChar { it.uppercase() } ?: "Email"
            profileNameHeader.text = displayName
            profileEmailHeader.text = user.email ?: ""
            tvSignInProvider?.text = provider
            // Hide the header auth button — show Sign Out in the profile section instead
            btnHeaderAuth?.visibility = View.GONE
            btnSignOut?.visibility = View.VISIBLE
        } else {
            profileNameHeader.text = "Guest"
            profileEmailHeader.text = "Sign in to access your profile"
            tvSignInProvider?.text = "Not signed in"
            btnHeaderAuth?.visibility = View.VISIBLE
            btnHeaderAuth?.text = "Login / Sign Up"
            btnHeaderAuth?.setOnClickListener { openLogin() }
            btnSignOut?.visibility = View.GONE
        }
    }

    private fun openLogin() {
        startActivity(Intent(requireContext(), LoginActivity::class.java))
    }

    private fun handleLogout() {
        viewLifecycleOwner.lifecycleScope.launch {
            try {
                SupabaseClient.signOut()
                // Clear persisted tokens so user doesn't auto-login on next app start
                val prefs = requireActivity().getSharedPreferences("fooder_auth", android.content.Context.MODE_PRIVATE)
                SupabaseClient.clearSession(prefs)
                Toast.makeText(requireContext(), "Signed out", Toast.LENGTH_SHORT).show()
            } catch (e: Exception) {
                Toast.makeText(requireContext(), "Sign out failed", Toast.LENGTH_SHORT).show()
            }
            profileNameHeader.text = "Guest"
            profileEmailHeader.text = "Sign in to access your profile"
            tvSignInProvider?.text = "Not signed in"
            inputName.setText("")
            inputEmail.setText("")
            inputContact.setText("")
            inputCountry.setText("")
            btnSignOut?.visibility = View.GONE
            btnHeaderAuth?.visibility = View.VISIBLE
            btnHeaderAuth?.text = "Login / Sign Up"
            btnHeaderAuth?.setOnClickListener { openLogin() }
        }
    }

    private fun loadAllProfileData() {
        viewLifecycleOwner.lifecycleScope.launch {
            setLoading(true, "Loading profile...")
            try {
                loadProfile()
                loadPreferences()
                loadSavedCards()
                loadPaymentHistory()
                loadScans()
                loadSubscription()
                try { loadPlans() } catch (_: Exception) { /* plans fallback to XML defaults */ }
            } catch (e: Exception) {
                Toast.makeText(requireContext(), "Failed to load profile: ${e.message}", Toast.LENGTH_SHORT).show()
            } finally {
                setLoading(false)
            }
        }
    }

    private suspend fun loadProfile() {
        // Check auth and update header button
        val user = try { SupabaseClient.getCurrentUser() } catch (e: Exception) { null }
        if (user == null) {
            profileNameHeader.text = "Guest"
            profileEmailHeader.text = "Sign in to access your profile"
            tvSignInProvider?.text = "Not signed in"
            btnHeaderAuth?.visibility = View.VISIBLE
            btnHeaderAuth?.text = "Login / Sign Up"
            btnHeaderAuth?.setOnClickListener { openLogin() }
            btnSignOut?.visibility = View.GONE
            return
        }
        btnHeaderAuth?.visibility = View.GONE
        btnSignOut?.visibility = View.VISIBLE

        val provider = user.appMetadata?.get("provider")?.toString()?.trim('"')
            ?.replaceFirstChar { it.uppercase() } ?: "Email"
        tvSignInProvider?.text = provider
        // Email is read-only for OAuth users
        if (provider != "Email") {
            inputEmail.isEnabled = false
            inputEmail.alpha = 0.6f
        } else {
            inputEmail.isEnabled = true
            inputEmail.alpha = 1f
        }

        val response = try { apiService.getAppProfile() } catch (e: Exception) {
            // API failed but user is authenticated — show data from Supabase auth
            val metaName = user.userMetadata?.get("name")?.toString()?.trim('"')
                ?: user.userMetadata?.get("full_name")?.toString()?.trim('"')
                ?: user.email?.substringBefore("@")?.replaceFirstChar { it.uppercase() } ?: "User"
            profileNameHeader.text = metaName
            profileEmailHeader.text = user.email ?: ""
            inputName.setText(metaName)
            inputEmail.setText(user.email ?: "")
            return
        }
        if (!response.isSuccessful || response.body() == null) {
            val metaName = user.userMetadata?.get("name")?.toString()?.trim('"')
                ?: user.userMetadata?.get("full_name")?.toString()?.trim('"')
                ?: user.email?.substringBefore("@")?.replaceFirstChar { it.uppercase() } ?: "User"
            profileNameHeader.text = metaName
            profileEmailHeader.text = user.email ?: ""
            inputName.setText(metaName)
            inputEmail.setText(user.email ?: "")
            return
        }

        val profile = response.body()!!
        val email = profile.email ?: user.email ?: ""
        // Prefer OAuth metadata name, then saved profile name, then email prefix
        val metaName = user.userMetadata?.get("name")?.toString()?.trim('"')
            ?: user.userMetadata?.get("full_name")?.toString()?.trim('"')
        val displayName = profile.full_name?.takeIf { it.isNotBlank() }
            ?: metaName?.takeIf { it.isNotBlank() }
            ?: user.email?.substringBefore("@")?.replaceFirstChar { it.uppercase() }
            ?: "User"
        profileNameHeader.text = displayName
        profileEmailHeader.text = email

        inputName.setText(displayName)
        inputEmail.setText(email)
        inputContact.setText(profile.contact ?: profile.phone ?: "")
        inputCountry.setText(profile.country ?: "")
    }

    private suspend fun loadPreferences() {
        val response = apiService.getProfilePreferences()
        if (!response.isSuccessful || response.body() == null) return

        val prefs = response.body()!!
        checkNotificationsEnabled.isChecked = prefs.notifications_enabled
        checkNotificationsPush.isChecked = prefs.push_notifications
        checkNotificationsEmail.isChecked = prefs.email_notifications
    }

    private suspend fun loadSavedCards() {
        val response = apiService.getSavedCards()
        if (!response.isSuccessful || response.body() == null) return

        val cards = response.body()!!.cards
        if (cards.isEmpty()) {
            cardInfoText.visibility = android.view.View.GONE
            return
        }

        val defaultCard = cards.firstOrNull { it.is_default } ?: cards.first()
        cardInfoText.visibility = android.view.View.VISIBLE
        cardInfoText.text = "Card: ${defaultCard.card_brand.uppercase()} •••• ${defaultCard.card_last_four} (exp ${defaultCard.card_exp_month}/${defaultCard.card_exp_year})"
    }

    private suspend fun loadPaymentHistory() {
        val response = apiService.getUserPaymentHistory()
        if (!response.isSuccessful || response.body() == null) return

        val payments = response.body()!!.payments
        if (payments.isEmpty()) {
            btnTabRecentPayments?.visibility = android.view.View.GONE
            return
        }

        btnTabRecentPayments?.visibility = android.view.View.VISIBLE
        val latest = payments.take(3)
            .joinToString("\n") { p ->
                "• ${p.transaction_type} ${p.amount_cents / 100.0} ${p.currency.uppercase()} (${p.status})"
            }
        recentPaymentsText?.text = latest
    }

    private suspend fun loadScans() {
        val response = apiService.getUserMenus()
        if (!response.isSuccessful || response.body() == null) return

        val scans = response.body()!!.menus
        statScans.text = scans.size.toString()
        scansSummary.text = "Total scans: ${scans.size}"

        if (scans.isEmpty()) {
            scanHistoryText.visibility = android.view.View.GONE
            return
        }

        scanHistoryText.visibility = android.view.View.VISIBLE
        scanHistoryText.text = scans.take(5)
            .joinToString("\n") { menu ->
                "• ${menu.restaurant_name ?: "Unknown restaurant"} (${menu.created_at ?: "n/a"})"
            }
    }

    private suspend fun loadSubscription() {
        val response = apiService.getSubscriptionInfo()
        if (!response.isSuccessful || response.body() == null) return

        val subscription = response.body()!!
        currentPlanName = subscription.plan_name.uppercase()
        statPlan.text = currentPlanName
        statStatus.text = subscription.status.replaceFirstChar { it.uppercase() }
        subscriptionText.text = "Current: ${subscription.plan_name} (${subscription.status})"
        premiumBadge.isVisible = currentPlanName == "PRO" || currentPlanName == "MAX"
        btnManageSubscription?.visibility = if (currentPlanName != "FREE") View.VISIBLE else View.GONE
    }

    private suspend fun loadPlans() {
        val response = apiService.getSubscriptionPlans()
        if (!response.isSuccessful || response.body() == null) return

        val plans = response.body()!!.plans
        plans.forEach { plan ->
            val priceText = plan.resolvedPriceDisplay()
            when (plan.name.uppercase()) {
                "FREE" -> {
                    if (!priceText.isNullOrBlank()) tvPriceFree.text = priceText
                    if (currentPlanName == "FREE") btnPlanFree.text = "Current Plan" else btnPlanFree.text = "Select Free"
                }
                "PRO" -> {
                    if (!priceText.isNullOrBlank()) tvPricePro.text = priceText
                    if (currentPlanName == "PRO") btnPlanPro.text = "Current Plan" else btnPlanPro.text = "Upgrade to Pro"
                }
                "MAX" -> {
                    if (!priceText.isNullOrBlank()) tvPriceMax.text = priceText
                    if (currentPlanName == "MAX") btnPlanMax.text = "Current Plan" else btnPlanMax.text = "Upgrade to Max"
                }
            }
        }
    }

    private fun saveProfile() {
        viewLifecycleOwner.lifecycleScope.launch {
            setLoading(true, "Saving profile...")
            try {
                val request = AppProfileDetailsRequest(
                    full_name = inputName.text.toString().trim().ifEmpty { null },
                    email = inputEmail.text.toString().trim().ifEmpty { null },
                    contact = inputContact.text.toString().trim().ifEmpty { null },
                    country = inputCountry.text.toString().trim().ifEmpty { null }
                )

                val response = apiService.updateAppProfile(request)
                if (response.isSuccessful) {
                    profileNameHeader.text = inputName.text.toString().trim().ifEmpty { "User" }
                    profileEmailHeader.text = inputEmail.text.toString().trim()
                    Toast.makeText(requireContext(), "Profile updated", Toast.LENGTH_SHORT).show()
                } else {
                    Toast.makeText(requireContext(), "Failed to update profile", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(requireContext(), "Failed to update profile: ${e.message}", Toast.LENGTH_SHORT).show()
            } finally {
                setLoading(false)
            }
        }
    }

    private fun saveCard() {
        val holder = inputCardHolder.text.toString().trim()
        val number = inputCardNumber.text.toString().trim()
        val expiry = inputCardExpiry.text.toString().trim()

        if (number.length < 12 || !expiry.contains("/")) {
            Toast.makeText(requireContext(), "Enter valid card number and expiry", Toast.LENGTH_SHORT).show()
            return
        }

        val expiryParts = expiry.split("/")
        if (expiryParts.size != 2) {
            Toast.makeText(requireContext(), "Use MM/YY format", Toast.LENGTH_SHORT).show()
            return
        }

        val month = expiryParts[0].toIntOrNull() ?: 1
        val year = (expiryParts[1].toIntOrNull() ?: 0) + 2000
        val lastFour = number.takeLast(4)
        val brand = when {
            number.startsWith("4") -> "visa"
            number.startsWith("5") -> "mastercard"
            number.startsWith("3") -> "amex"
            else -> "card"
        }

        viewLifecycleOwner.lifecycleScope.launch {
            setLoading(true, "Storing card...")
            try {
                val response = apiService.saveCard(
                    SaveCardRequest(
                        card_brand = brand,
                        card_last_four = lastFour,
                        card_exp_month = month,
                        card_exp_year = year,
                        cardholder_name = holder.ifEmpty { null },
                        tokenized_card_id = "tok_$lastFour"
                    )
                )

                if (response.isSuccessful && response.body() != null) {
                    val card = response.body()!!
                    cardInfoText.visibility = android.view.View.VISIBLE
                    cardInfoText.text = "Card: ${card.card_brand.uppercase()} •••• ${card.card_last_four} (exp ${card.card_exp_month}/${card.card_exp_year})"
                    inputCardNumber.text?.clear()
                    inputCardCvv.text?.clear()
                    Toast.makeText(requireContext(), "Card stored securely", Toast.LENGTH_SHORT).show()
                } else {
                    Toast.makeText(requireContext(), "Failed to store card", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(requireContext(), "Failed to store card: ${e.message}", Toast.LENGTH_SHORT).show()
            } finally {
                setLoading(false)
            }
        }
    }

    /**
     * Open the web pricing page in the system browser.
     *
     * We do NOT use in-app purchases (Play Billing) here to avoid the
     * 30% Google Play commission. Payment goes directly through Stripe
     * on our web domain. After checkout the web page issues a deep-link
     * (menuocr://subscription-result?status=success) which LoginActivity
     * receives and triggers a subscription status refresh.
     */
    private fun openWebCheckout(planId: String = "") {
        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val user = SupabaseClient.getCurrentUser()
                // Build URL with Supabase tokens so the web page auto-authenticates
                val session = SupabaseClient.getCurrentSession()
                val accessToken  = session?.accessToken  ?: ""
                val refreshToken = session?.refreshToken ?: ""

                val baseUrl = AppConfig.Web.pricingUrl(accessToken, refreshToken)
                val url = if (planId.isNotBlank()) "$baseUrl&plan=$planId" else baseUrl

                launchBrandedTab(url)
            } catch (e: Exception) {
                // Fallback: just open pricing page without auth token
                val fallback = "${AppConfig.Web.BASE_URL}${AppConfig.Web.PRICING_PATH}"
                launchBrandedTab(fallback)
            }
        }
    }

    private fun openManageSubscription() {
        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val session = SupabaseClient.getCurrentSession()
                val accessToken  = session?.accessToken  ?: ""
                val refreshToken = session?.refreshToken ?: ""
                // Request portal URL from our API then open it
                val bearerToken = "Bearer $accessToken"
                val res = try { apiService.getCustomerPortal(bearerToken) } catch (_: Exception) { null }
                val portalUrl = res?.body()?.portal_url
                val url = if (!portalUrl.isNullOrBlank()) portalUrl
                          else "${AppConfig.Web.BASE_URL}${AppConfig.Web.MANAGE_SUB_PATH}?token=$accessToken&refresh=$refreshToken"
                launchBrandedTab(url)
            } catch (e: Exception) {
                val fallback = "${AppConfig.Web.BASE_URL}${AppConfig.Web.MANAGE_SUB_PATH}"
                launchBrandedTab(fallback)
            }
        }
    }

    private fun launchBrandedTab(url: String) {
        val toolbarColor = android.graphics.Color.parseColor("#222222")
        val colorParams = CustomTabColorSchemeParams.Builder()
            .setToolbarColor(toolbarColor)
            .setNavigationBarColor(toolbarColor)
            .build()
        val customTabsIntent = CustomTabsIntent.Builder()
            .setDefaultColorSchemeParams(colorParams)
            .setShowTitle(true)
            .setUrlBarHidingEnabled(true)
            .build()
        customTabsIntent.launchUrl(requireContext(), Uri.parse(url))
    }

    private fun selectPlan(planName: String) {
        // FREE downgrade: no payment needed, just call API
        if (planName == "FREE") {
            viewLifecycleOwner.lifecycleScope.launch {
                try {
                    apiService.selectSubscriptionPlan(SelectSubscriptionPlanRequest(plan_name = planName))
                    Toast.makeText(requireContext(), "Switched to Free plan", Toast.LENGTH_SHORT).show()
                    loadAllProfileData()
                } catch (_: Exception) {}
            }
            return
        }
        // PRO / MAX: open web checkout — bypasses store commission entirely
        openWebCheckout(planId = planName.lowercase())
    }

    private fun savePreferences() {
        viewLifecycleOwner.lifecycleScope.launch {
            setLoading(true, "Saving preferences...")
            try {
                val request = ProfilePreferencesRequest(
                    notifications_enabled = checkNotificationsEnabled.isChecked,
                    push_notifications = checkNotificationsPush.isChecked,
                    email_notifications = checkNotificationsEmail.isChecked,
                    language = null,
                    timezone = null
                )

                val response = apiService.updateProfilePreferences(request)
                if (response.isSuccessful) {
                    Toast.makeText(requireContext(), "Preferences updated", Toast.LENGTH_SHORT).show()
                } else {
                    Toast.makeText(requireContext(), "Failed to update preferences", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(requireContext(), "Failed to update preferences: ${e.message}", Toast.LENGTH_SHORT).show()
            } finally {
                setLoading(false)
            }
        }
    }
}
