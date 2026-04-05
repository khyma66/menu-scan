package com.menuocr

import android.content.Intent
import android.os.Bundle
import android.util.Log
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.*
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class HealthConditionsFragment : Fragment() {
    companion object {
        private const val HEALTH_PREFS = "health_profile_cache"
        private const val KEY_HEALTH_CONDITIONS = "health_conditions"
        private const val KEY_ALLERGIES = "allergies"
        private const val KEY_DIETARY_PREFERENCES = "dietary_preferences"
        private const val KEY_TASTE_PREFERENCES = "taste_preferences"
        private const val KEY_MEDICAL_NOTES = "medical_notes"
    }

    private lateinit var healthConditionsInput: EditText
    private lateinit var allergiesInput: EditText
    private lateinit var dietaryPreferencesInput: EditText
    private lateinit var tastePreferenceInput: EditText
    private lateinit var medicalNotesInput: EditText
    private lateinit var btnSaveProfile: Button
    private lateinit var loadingProgress: LinearLayout
    private lateinit var statusMessage: TextView
    private lateinit var currentConditionsCard: LinearLayout
    private lateinit var inputsCard: View
    private var btnHealthLogin: Button? = null

    private var apiService: ApiService? = null
    private var loadProfileJob: Job? = null

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_health_conditions, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        // Initialize views
        healthConditionsInput = view.findViewById(R.id.input_health_conditions)
        allergiesInput = view.findViewById(R.id.input_allergies)
        dietaryPreferencesInput = view.findViewById(R.id.input_dietary_preferences)
        tastePreferenceInput = view.findViewById(R.id.input_taste_preference)
        medicalNotesInput = view.findViewById(R.id.input_medical_notes)
        btnSaveProfile = view.findViewById(R.id.btn_save_profile)
        loadingProgress = view.findViewById(R.id.loading_progress)
        statusMessage = view.findViewById(R.id.status_message)
        currentConditionsCard = view.findViewById(R.id.current_conditions_card)

        inputsCard = view.findViewById(R.id.inputs_card)
        btnHealthLogin = view.findViewById(R.id.btn_health_login)
        btnHealthLogin?.setOnClickListener {
            startActivity(Intent(requireContext(), LoginActivity::class.java))
        }

        setupApiService()
        setupClickListeners()
        // Profile loaded in onResume to avoid duplicate calls
    }

    override fun onResume() {
        super.onResume()
        loadCurrentProfile()
    }

    private fun setupApiService() {
        apiService = ApiClient.getApiService()
    }

    private fun setupClickListeners() {
        btnSaveProfile.setOnClickListener {
            saveHealthProfile()
        }
    }

    private fun loadCurrentProfile() {
        loadProfileJob?.cancel()
        loadProfileJob = viewLifecycleOwner.lifecycleScope.launch {
            // Show loading state while checking auth
            statusMessage.text = "⏳ Checking your account…"
            statusMessage.setTextColor(requireContext().getColor(R.color.gray_600))
            statusMessage.visibility = View.VISIBLE
            btnHealthLogin?.visibility = View.GONE
            inputsCard.visibility = View.GONE
            currentConditionsCard.visibility = View.GONE

            // Check authentication first
            val authenticated = try { SupabaseClient.isAuthenticated() } catch (e: Exception) { false }
            if (!authenticated) {
                updateStatus("🔐 Please login to view and save your health options.", false)
                btnHealthLogin?.visibility = View.VISIBLE
                inputsCard.visibility = View.GONE
                currentConditionsCard.visibility = View.GONE
                return@launch
            }
            btnHealthLogin?.visibility = View.GONE
            inputsCard.visibility = View.VISIBLE
            currentConditionsCard.visibility = View.VISIBLE
            updateStatus("⏳ Loading your health profile…", true)

            // Ensure API auth token is fresh before loading
            try { ApiClient.updateAuthToken() } catch (_: Exception) {}

            try {
                val response = apiService?.getHealthProfile()
                if (response?.isSuccessful == true && response.body() != null) {
                    val profileWrapper = response.body()!!
                    val profile = profileWrapper.health_profile
                    val tasteFromDietary = mutableListOf<String>()
                    val pureDietary = mutableListOf<String>()

                    profile?.dietary_preferences.orEmpty().forEach { pref ->
                        val value = pref.trim()
                        if (value.startsWith("taste:", ignoreCase = true)) {
                            tasteFromDietary.add(value.substringAfter(":").trim())
                        } else {
                            pureDietary.add(value)
                        }
                    }
                    
                    // Populate the fields with existing data
                    if (profile?.health_conditions?.isNotEmpty() == true) {
                        healthConditionsInput.setText(profile.health_conditions.joinToString(", "))
                    }
                    if (profile?.allergies?.isNotEmpty() == true) {
                        allergiesInput.setText(profile.allergies.joinToString(", "))
                    }
                    if (pureDietary.isNotEmpty()) {
                        dietaryPreferencesInput.setText(pureDietary.joinToString(", "))
                    }
                    if (tasteFromDietary.isNotEmpty()) {
                        tastePreferenceInput.setText(tasteFromDietary.joinToString(", "))
                    }
                    if (profile?.medical_notes?.isNotBlank() == true) {
                        medicalNotesInput.setText(profile.medical_notes)
                    }

                    persistHealthProfileLocally(
                        healthConditions = profile?.health_conditions.orEmpty(),
                        allergies = profile?.allergies.orEmpty(),
                        dietaryPreferences = pureDietary,
                        tastePreferences = tasteFromDietary,
                        medicalNotes = profile?.medical_notes,
                    )

                    statusMessage.visibility = View.GONE
                } else if (response?.code() == 401 || response?.code() == 403) {
                    // Token may be stale - refresh and retry once
                    try { ApiClient.updateAuthToken() } catch (_: Exception) {}
                    val retryResponse = apiService?.getHealthProfile()
                    if (retryResponse?.isSuccessful == true && retryResponse.body() != null) {
                        // retry succeeded - reload
                        loadCurrentProfile()
                        return@launch
                    }
                    inputsCard.visibility = View.VISIBLE
                    currentConditionsCard.visibility = View.VISIBLE
                    updateStatus("ℹ️ Add your health preferences below.", true)
                } else {
                    inputsCard.visibility = View.VISIBLE
                    currentConditionsCard.visibility = View.VISIBLE
                    updateStatus("ℹ️ Add your health preferences below.", true)
                }
            } catch (e: CancellationException) {
                // Coroutine was cancelled (e.g. fragment destroyed) - don't update UI
                throw e
            } catch (e: Exception) {
                Log.w("HealthConditionsFragment", "Could not load profile: ${e.message}")
                updateStatus("ℹ️ No existing profile found. Create a new one.", true)
            }
        }
    }

    private fun saveHealthProfile() {
        val healthConditions = healthConditionsInput.text.toString().trim()
            .split(',', ';', '\n')
            .map { it.trim() }
            .filter { it.isNotEmpty() }
            .distinct()

        val allergies = allergiesInput.text.toString().trim()
            .split(',', ';', '\n')
            .map { it.trim() }
            .filter { it.isNotEmpty() }
            .distinct()

        val dietaryPreferences = dietaryPreferencesInput.text.toString().trim()
            .split(',', ';', '\n')
            .map { it.trim() }
            .filter { it.isNotEmpty() }
            .distinct()

        val tastePreferences = tastePreferenceInput.text.toString().trim()
            .split(',', ';', '\n')
            .map { it.trim() }
            .filter { it.isNotEmpty() }
            .distinct()

        val medicalNotes = medicalNotesInput.text.toString().trim()

        if (healthConditions.isEmpty() && allergies.isEmpty() && dietaryPreferences.isEmpty() && tastePreferences.isEmpty() && medicalNotes.isEmpty()) {
            Toast.makeText(requireContext(), "Please enter at least one health condition or preference", Toast.LENGTH_SHORT).show()
            return
        }

        val mergedDietaryPreferences = (dietaryPreferences + tastePreferences.map { "taste:$it" }).distinct()

        showLoading(true)

        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val response = apiService?.updateHealthProfile(
                    HealthProfileRequest(
                        health_conditions = healthConditions,
                        allergies = allergies,
                        dietary_preferences = mergedDietaryPreferences,
                        medical_notes = medicalNotes.ifBlank { null }
                    )
                )

                if (response?.isSuccessful == true) {
                    persistHealthProfileLocally(
                        healthConditions = healthConditions,
                        allergies = allergies,
                        dietaryPreferences = dietaryPreferences,
                        tastePreferences = tastePreferences,
                        medicalNotes = medicalNotes.ifBlank { null },
                    )
                    updateStatus("✅ Health profile saved successfully!", true)
                    Toast.makeText(requireContext(), "Profile saved!", Toast.LENGTH_SHORT).show()
                } else if (response?.code() == 401 || response?.code() == 403) {
                    updateStatus("⚠️ Please login before saving health profile.", false)
                } else {
                    updateStatus("⚠️ Failed to save profile: ${response?.message()}", false)
                }
            } catch (e: Exception) {
                Log.e("HealthConditionsFragment", "Failed to save profile", e)
                updateStatus("❌ Error: ${e.localizedMessage ?: "Unknown error"}", false)
            } finally {
                showLoading(false)
            }
        }
    }

    private fun showLoading(show: Boolean) {
        if (show) {
            loadingProgress.visibility = View.VISIBLE
            btnSaveProfile.isEnabled = false
        } else {
            loadingProgress.visibility = View.GONE
            btnSaveProfile.isEnabled = true
        }
    }

    private fun updateStatus(message: String, isSuccess: Boolean) {
        statusMessage.text = message
        statusMessage.setTextColor(
            android.content.res.ColorStateList.valueOf(
                if (isSuccess) {
                    requireContext().getColor(R.color.green_700)
                } else {
                    requireContext().getColor(R.color.red_500)
                }
            )
        )
        statusMessage.visibility = View.VISIBLE
    }

    private fun persistHealthProfileLocally(
        healthConditions: List<String>,
        allergies: List<String>,
        dietaryPreferences: List<String>,
        tastePreferences: List<String>,
        medicalNotes: String?,
    ) {
        val prefs = requireContext().getSharedPreferences(HEALTH_PREFS, android.content.Context.MODE_PRIVATE)
        prefs.edit()
            .putString(KEY_HEALTH_CONDITIONS, healthConditions.joinToString("|"))
            .putString(KEY_ALLERGIES, allergies.joinToString("|"))
            .putString(KEY_DIETARY_PREFERENCES, dietaryPreferences.joinToString("|"))
            .putString(KEY_TASTE_PREFERENCES, tastePreferences.joinToString("|"))
            .putString(KEY_MEDICAL_NOTES, medicalNotes.orEmpty())
            .apply()
    }
}
