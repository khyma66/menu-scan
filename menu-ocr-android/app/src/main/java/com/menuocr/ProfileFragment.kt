package com.menuocr

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
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch

class ProfileFragment : Fragment() {

    private enum class ProfileTab {
        PROFILE,
        PAYMENT,
        SCANS,
        SUBSCRIPTION,
        NOTIFICATIONS,
        PRIVACY
    }

    private lateinit var apiService: ApiService
    private var activeTab: ProfileTab = ProfileTab.PROFILE

    private lateinit var btnTabProfile: Button
    private lateinit var btnTabPayment: Button
    private lateinit var btnTabScans: Button
    private lateinit var btnTabSubscription: Button
    private lateinit var btnTabNotifications: Button
    private lateinit var btnTabPrivacy: Button

    private lateinit var sectionProfile: View
    private lateinit var sectionPayment: View
    private lateinit var sectionScans: View
    private lateinit var sectionSubscription: View
    private lateinit var sectionNotifications: View
    private lateinit var sectionPrivacy: View

    private lateinit var loadingProgress: LinearLayout
    private lateinit var loadingText: TextView

    private lateinit var profileNameHeader: TextView
    private lateinit var profileEmailHeader: TextView
    private lateinit var premiumBadge: TextView
    private lateinit var statScans: TextView
    private lateinit var statPlan: TextView
    private lateinit var statStatus: TextView

    private lateinit var inputName: EditText
    private lateinit var inputEmail: EditText
    private lateinit var inputContact: EditText
    private lateinit var inputCountry: EditText
    private lateinit var inputLanguage: EditText
    private lateinit var inputTimezone: EditText
    private lateinit var btnSaveProfile: Button

    private lateinit var inputCardHolder: EditText
    private lateinit var inputCardNumber: EditText
    private lateinit var inputCardExpiry: EditText
    private lateinit var inputCardCvv: EditText
    private lateinit var btnSaveCard: Button
    private lateinit var cardInfoText: TextView
    private lateinit var paymentHistoryText: TextView

    private lateinit var scansSummary: TextView
    private lateinit var scanHistoryText: TextView

    private lateinit var subscriptionText: TextView
    private lateinit var btnPlanFree: Button
    private lateinit var btnPlanPro: Button
    private lateinit var btnPlanMax: Button

    private lateinit var checkNotificationsEnabled: CheckBox
    private lateinit var checkNotificationsPush: CheckBox
    private lateinit var checkNotificationsEmail: CheckBox
    private lateinit var btnSaveNotifications: Button

    private lateinit var spinnerProfileVisibility: Spinner
    private lateinit var checkAnalyticsOptIn: CheckBox
    private lateinit var checkMarketingOptIn: CheckBox
    private lateinit var btnSavePrivacy: Button

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
        btnTabScans = view.findViewById(R.id.btn_tab_scans)
        btnTabSubscription = view.findViewById(R.id.btn_tab_subscription)
        btnTabNotifications = view.findViewById(R.id.btn_tab_notifications)
        btnTabPrivacy = view.findViewById(R.id.btn_tab_privacy)

        sectionProfile = view.findViewById(R.id.section_profile)
        sectionPayment = view.findViewById(R.id.section_payment)
        sectionScans = view.findViewById(R.id.section_scans)
        sectionSubscription = view.findViewById(R.id.section_subscription)
        sectionNotifications = view.findViewById(R.id.section_notifications)
        sectionPrivacy = view.findViewById(R.id.section_privacy)

        loadingProgress = view.findViewById(R.id.loading_progress)
        loadingText = view.findViewById(R.id.loading_text)

        profileNameHeader = view.findViewById(R.id.profile_name_header)
        profileEmailHeader = view.findViewById(R.id.profile_email_header)
        premiumBadge = view.findViewById(R.id.premium_badge)
        statScans = view.findViewById(R.id.stat_scans)
        statPlan = view.findViewById(R.id.stat_plan)
        statStatus = view.findViewById(R.id.stat_status)

        inputName = view.findViewById(R.id.input_name)
        inputEmail = view.findViewById(R.id.input_email)
        inputContact = view.findViewById(R.id.input_contact)
        inputCountry = view.findViewById(R.id.input_country)
        inputLanguage = view.findViewById(R.id.input_language)
        inputTimezone = view.findViewById(R.id.input_timezone)
        btnSaveProfile = view.findViewById(R.id.btn_save_profile)

        inputCardHolder = view.findViewById(R.id.input_card_holder)
        inputCardNumber = view.findViewById(R.id.input_card_number)
        inputCardExpiry = view.findViewById(R.id.input_card_expiry)
        inputCardCvv = view.findViewById(R.id.input_card_cvv)
        btnSaveCard = view.findViewById(R.id.btn_save_card)
        cardInfoText = view.findViewById(R.id.card_info_text)
        paymentHistoryText = view.findViewById(R.id.payment_history_text)

        scansSummary = view.findViewById(R.id.scans_summary)
        scanHistoryText = view.findViewById(R.id.scan_history_text)

        subscriptionText = view.findViewById(R.id.subscription_text)
        btnPlanFree = view.findViewById(R.id.btn_plan_free)
        btnPlanPro = view.findViewById(R.id.btn_plan_pro)
        btnPlanMax = view.findViewById(R.id.btn_plan_max)

        checkNotificationsEnabled = view.findViewById(R.id.check_notifications_enabled)
        checkNotificationsPush = view.findViewById(R.id.check_notifications_push)
        checkNotificationsEmail = view.findViewById(R.id.check_notifications_email)
        btnSaveNotifications = view.findViewById(R.id.btn_save_notifications)

        spinnerProfileVisibility = view.findViewById(R.id.spinner_profile_visibility)
        checkAnalyticsOptIn = view.findViewById(R.id.check_analytics_opt_in)
        checkMarketingOptIn = view.findViewById(R.id.check_marketing_opt_in)
        btnSavePrivacy = view.findViewById(R.id.btn_save_privacy)

        val visibilityOptions = listOf("private", "friends", "public")
        spinnerProfileVisibility.adapter = ArrayAdapter(
            requireContext(),
            android.R.layout.simple_spinner_dropdown_item,
            visibilityOptions
        )
    }

    private fun setupListeners() {
        btnTabProfile.setOnClickListener { selectTab(ProfileTab.PROFILE) }
        btnTabPayment.setOnClickListener { selectTab(ProfileTab.PAYMENT) }
        btnTabScans.setOnClickListener { selectTab(ProfileTab.SCANS) }
        btnTabSubscription.setOnClickListener { selectTab(ProfileTab.SUBSCRIPTION) }
        btnTabNotifications.setOnClickListener { selectTab(ProfileTab.NOTIFICATIONS) }
        btnTabPrivacy.setOnClickListener { selectTab(ProfileTab.PRIVACY) }

        btnSaveProfile.setOnClickListener { saveProfile() }
        btnSaveCard.setOnClickListener { saveCard() }
        btnSaveNotifications.setOnClickListener { savePreferences() }
        btnSavePrivacy.setOnClickListener { savePreferences() }

        btnPlanFree.setOnClickListener { selectPlan("FREE") }
        btnPlanPro.setOnClickListener { selectPlan("PRO") }
        btnPlanMax.setOnClickListener { selectPlan("MAX") }
    }

    private fun selectTab(tab: ProfileTab) {
        activeTab = tab

        sectionProfile.isVisible = tab == ProfileTab.PROFILE
        sectionPayment.isVisible = tab == ProfileTab.PAYMENT
        sectionScans.isVisible = tab == ProfileTab.SCANS
        sectionSubscription.isVisible = tab == ProfileTab.SUBSCRIPTION
        sectionNotifications.isVisible = tab == ProfileTab.NOTIFICATIONS
        sectionPrivacy.isVisible = tab == ProfileTab.PRIVACY

        setTabState(btnTabProfile, tab == ProfileTab.PROFILE)
        setTabState(btnTabPayment, tab == ProfileTab.PAYMENT)
        setTabState(btnTabScans, tab == ProfileTab.SCANS)
        setTabState(btnTabSubscription, tab == ProfileTab.SUBSCRIPTION)
        setTabState(btnTabNotifications, tab == ProfileTab.NOTIFICATIONS)
        setTabState(btnTabPrivacy, tab == ProfileTab.PRIVACY)
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
                loadPlans()
            } catch (e: Exception) {
                Toast.makeText(requireContext(), "Failed to load profile: ${e.message}", Toast.LENGTH_SHORT).show()
            } finally {
                setLoading(false)
            }
        }
    }

    private suspend fun loadProfile() {
        val response = apiService.getAppProfile()
        if (!response.isSuccessful || response.body() == null) return

        val profile = response.body()!!
        val user = SupabaseClient.getCurrentUser()
        val userEmail = user?.email

        val name = profile.full_name ?: "User"
        val email = profile.email ?: userEmail ?: ""
        profileNameHeader.text = name
        profileEmailHeader.text = email

        inputName.setText(profile.full_name ?: "")
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
        checkAnalyticsOptIn.isChecked = prefs.analytics_opt_in
        checkMarketingOptIn.isChecked = prefs.marketing_opt_in
        inputLanguage.setText(prefs.language ?: "")
        inputTimezone.setText(prefs.timezone ?: "")

        val options = listOf("private", "friends", "public")
        val selectedIndex = options.indexOf(prefs.profile_visibility.lowercase()).coerceAtLeast(0)
        spinnerProfileVisibility.setSelection(selectedIndex)
    }

    private suspend fun loadSavedCards() {
        val response = apiService.getSavedCards()
        if (!response.isSuccessful || response.body() == null) return

        val cards = response.body()!!.cards
        if (cards.isEmpty()) {
            cardInfoText.text = "Card: Not stored"
            return
        }

        val defaultCard = cards.firstOrNull { it.is_default } ?: cards.first()
        cardInfoText.text = "Card: ${defaultCard.card_brand.uppercase()} •••• ${defaultCard.card_last_four} (exp ${defaultCard.card_exp_month}/${defaultCard.card_exp_year})"
    }

    private suspend fun loadPaymentHistory() {
        val response = apiService.getUserPaymentHistory()
        if (!response.isSuccessful || response.body() == null) return

        val payments = response.body()!!.payments
        if (payments.isEmpty()) {
            paymentHistoryText.text = "No payments yet"
            return
        }

        val latest = payments.take(3)
            .joinToString("\n") { p ->
                "• ${p.transaction_type} ${p.amount_cents / 100.0} ${p.currency.uppercase()} (${p.status})"
            }
        paymentHistoryText.text = latest
    }

    private suspend fun loadScans() {
        val response = apiService.getUserMenus()
        if (!response.isSuccessful || response.body() == null) return

        val scans = response.body()!!.menus
        statScans.text = scans.size.toString()
        scansSummary.text = "Total scans: ${scans.size}"

        if (scans.isEmpty()) {
            scanHistoryText.text = "No scans yet"
            return
        }

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
    }

    private suspend fun loadPlans() {
        val response = apiService.getSubscriptionPlans()
        if (!response.isSuccessful || response.body() == null) return

        val plans = response.body()!!.plans
        plans.forEach { plan ->
            val label = "${plan.name} • ${plan.price_display}/${plan.billing_period} • ${plan.description}"
            when (plan.name.uppercase()) {
                "FREE" -> btnPlanFree.text = label
                "PRO" -> btnPlanPro.text = label
                "MAX" -> btnPlanMax.text = label
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

    private fun selectPlan(planName: String) {
        viewLifecycleOwner.lifecycleScope.launch {
            setLoading(true, "Updating subscription...")
            try {
                val response = apiService.selectSubscriptionPlan(SelectSubscriptionPlanRequest(plan_name = planName))
                if (response.isSuccessful && response.body() != null) {
                    val sub = response.body()!!
                    currentPlanName = sub.plan_name.uppercase()
                    statPlan.text = currentPlanName
                    statStatus.text = sub.status.replaceFirstChar { it.uppercase() }
                    subscriptionText.text = "Current: ${sub.plan_name} (${sub.status})"
                    premiumBadge.isVisible = currentPlanName == "PRO" || currentPlanName == "MAX"
                    Toast.makeText(requireContext(), "Plan switched to ${sub.plan_name}", Toast.LENGTH_SHORT).show()
                } else {
                    Toast.makeText(requireContext(), "Failed to switch plan", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(requireContext(), "Failed to switch plan: ${e.message}", Toast.LENGTH_SHORT).show()
            } finally {
                setLoading(false)
            }
        }
    }

    private fun savePreferences() {
        viewLifecycleOwner.lifecycleScope.launch {
            setLoading(true, "Saving preferences...")
            try {
                val visibility = spinnerProfileVisibility.selectedItem?.toString() ?: "private"
                val request = ProfilePreferencesRequest(
                    notifications_enabled = checkNotificationsEnabled.isChecked,
                    push_notifications = checkNotificationsPush.isChecked,
                    email_notifications = checkNotificationsEmail.isChecked,
                    profile_visibility = visibility,
                    analytics_opt_in = checkAnalyticsOptIn.isChecked,
                    marketing_opt_in = checkMarketingOptIn.isChecked,
                    language = inputLanguage.text.toString().trim().ifEmpty { null },
                    timezone = inputTimezone.text.toString().trim().ifEmpty { null }
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
