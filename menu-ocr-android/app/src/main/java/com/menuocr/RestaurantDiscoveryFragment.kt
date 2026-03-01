package com.menuocr

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.Color
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.SeekBar
import android.widget.TextView
import android.widget.Toast
import androidx.cardview.widget.CardView
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch
import org.maplibre.android.MapLibre
import org.maplibre.android.annotations.MarkerOptions
import org.maplibre.android.camera.CameraPosition
import org.maplibre.android.camera.CameraUpdateFactory
import org.maplibre.android.geometry.LatLng
import org.maplibre.android.maps.MapView
import org.maplibre.android.maps.MapLibreMap
import org.maplibre.android.maps.OnMapReadyCallback

/**
 * Restaurant Discovery Fragment
 * 
 * Uses Android Location APIs to get user location and Overpass API
 * to query nearby restaurants from OpenStreetMap data.
 * 
 * DoorDash-like UI with distance slider, map display, and dynamic restaurant cards.
 */
class RestaurantDiscoveryFragment : Fragment(), OnMapReadyCallback {

    // UI Components
    private lateinit var cuisineContainer: LinearLayout
    private lateinit var restaurantsContainer: LinearLayout
    private lateinit var searchBar: EditText
    private lateinit var locationLoadingOverlay: View
    private lateinit var locationStatusBar: LinearLayout
    private lateinit var locationStatusText: TextView
    private lateinit var enableLocationBtn: Button
    private lateinit var loadingContainer: View
    private lateinit var emptyState: View
    private lateinit var statsRestaurantsCount: TextView
    private lateinit var statsRadius: TextView
    private lateinit var statsAccuracy: TextView
    private lateinit var distanceSeekBar: SeekBar
    private lateinit var distanceValueText: TextView
    private lateinit var refreshBtn: Button
    private lateinit var deliveryLocationText: TextView
    private lateinit var deliveryAddressText: TextView
    private lateinit var mapView: MapView
    
    // Map
    private var mapLibreMap: MapLibreMap? = null

    // Services
    private lateinit var locationService: LocationService
    private lateinit var overpassApiService: OverpassApiService
    private var apiService: ApiService? = null

    // State
    private var selectedCuisine: String? = null
    private var searchQuery: String = ""
    private var currentUserLocation: UserLocation? = null
    private var allRestaurants: List<OverpassRestaurant> = emptyList()
    private var hasLocationPermission = false
    private var currentRadiusMiles = 10

    // Cuisines for filtering (extracted from data)
    private val availableCuisines = mutableSetOf<String>()

    companion object {
        private const val LOCATION_PERMISSION_REQUEST_CODE = 1001
        private const val METERS_PER_MILE = 1609.34
    }

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_restaurant_discovery, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        // Initialize services
        locationService = LocationService(requireContext())
        overpassApiService = OverpassApiService()
        apiService = ApiClient.getApiService()

        // Initialize UI components
        initializeViews(view)
        setupMap(savedInstanceState)
        setupSearchBar()
        setupDistanceSelector()
        setupRefreshButton()
        loadDiscoveryPreferences()
        checkLocationPermissions()
    }

    private fun loadDiscoveryPreferences() {
        lifecycleScope.launch {
            try {
                val response = apiService?.getDiscoveryPreferences()
                val body = if (response?.isSuccessful == true) response.body() else null
                if (body != null) {
                    currentRadiusMiles = body.search_radius_miles.coerceIn(1, 20)
                    selectedCuisine = body.selected_cuisines.firstOrNull()?.takeIf { it.isNotBlank() }
                    distanceSeekBar.progress = currentRadiusMiles - 1
                    updateDistanceUi()
                }
            } catch (_: Exception) {
            }
        }
    }

    private fun persistDiscoveryPreferences() {
        lifecycleScope.launch {
            try {
                val location = currentUserLocation
                apiService?.updateDiscoveryPreferences(
                    DiscoveryPreferencesRequest(
                        search_radius_miles = currentRadiusMiles,
                        selected_cuisines = selectedCuisine?.let { listOf(it) } ?: emptyList(),
                        location_label = deliveryAddressText.text?.toString()?.takeIf { it.isNotBlank() },
                        latitude = location?.latitude,
                        longitude = location?.longitude,
                    )
                )
            } catch (_: Exception) {
            }
        }
    }
    
    private fun setupMap(savedInstanceState: Bundle?) {
        // Get the MapView
        mapView = view?.findViewById(R.id.map_view) ?: return
        mapView.onCreate(savedInstanceState)
        mapView.getMapAsync(this)
    }
    
    override fun onMapReady(map: MapLibreMap) {
        mapLibreMap = map
        
        // Configure map with OSM style
        map.setStyle(AppConfig.OSM.MAP_STYLE_URL) { style ->
            // Style loaded
            android.util.Log.d("RestaurantDiscovery", "Map style loaded")
        }
        
        // Set default camera position
        map.cameraPosition = CameraPosition.Builder()
            .zoom(12.0)
            .build()
            
        // If we already have location, move camera
        currentUserLocation?.let { location ->
            moveMapCamera(location.latitude, location.longitude)
        }
    }
    
    private fun moveMapCamera(lat: Double, lon: Double, zoom: Double = 13.0) {
        mapLibreMap?.moveCamera(
            CameraUpdateFactory.newLatLngZoom(LatLng(lat, lon), zoom)
        )
    }
    
    private fun addRestaurantMarkers(restaurants: List<OverpassRestaurant>) {
        mapLibreMap?.clear()
        
        // Add user location marker
        currentUserLocation?.let { location ->
            mapLibreMap?.addMarker(
                MarkerOptions()
                    .position(LatLng(location.latitude, location.longitude))
                    .title("Your Location")
                    .snippet("You are here")
            )
        }
        
        // Add restaurant markers
        restaurants.forEach { restaurant ->
            mapLibreMap?.addMarker(
                MarkerOptions()
                    .position(LatLng(restaurant.latitude, restaurant.longitude))
                    .title(restaurant.name)
                    .snippet(restaurant.getCuisineDisplayName())
            )
        }
    }

    private fun initializeViews(view: View) {
        cuisineContainer = view.findViewById(R.id.cuisine_categories)
        restaurantsContainer = view.findViewById(R.id.restaurants_container)
        searchBar = view.findViewById(R.id.search_bar)
        locationLoadingOverlay = view.findViewById(R.id.location_loading_overlay)
        locationStatusBar = view.findViewById(R.id.location_status_bar)
        locationStatusText = view.findViewById(R.id.location_status_text)
        enableLocationBtn = view.findViewById(R.id.enable_location_btn)
        loadingContainer = view.findViewById(R.id.loading_container)
        emptyState = view.findViewById(R.id.empty_state)
        statsRestaurantsCount = view.findViewById(R.id.stats_restaurants_count)
        statsRadius = view.findViewById(R.id.stats_radius)
        statsAccuracy = view.findViewById(R.id.stats_accuracy)
        distanceSeekBar = view.findViewById(R.id.distance_seekbar)
        distanceValueText = view.findViewById(R.id.distance_value_text)
        refreshBtn = view.findViewById(R.id.refresh_btn)
        deliveryLocationText = view.findViewById(R.id.delivery_location_text)
        deliveryAddressText = view.findViewById(R.id.delivery_address_text)
    }

    private fun setupDistanceSelector() {
        // SeekBar: 1-20 miles (progress 0-19)
        distanceSeekBar.max = 19
        distanceSeekBar.progress = currentRadiusMiles - 1
        updateDistanceUi()

        distanceSeekBar.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(seekBar: SeekBar?, progress: Int, fromUser: Boolean) {
                currentRadiusMiles = progress + 1
                updateDistanceUi()
            }

            override fun onStartTrackingTouch(seekBar: SeekBar?) = Unit

            override fun onStopTrackingTouch(seekBar: SeekBar?) {
                if (hasLocationPermission && currentUserLocation != null) {
                    fetchRestaurants()
                }
                persistDiscoveryPreferences()
            }
        })
    }

    private fun updateDistanceUi() {
        val radiusText = "$currentRadiusMiles mi"
        distanceValueText.text = radiusText
        statsRadius.text = radiusText
    }

    private fun setupSearchBar() {
        searchBar.setOnEditorActionListener { _, _, _ ->
            searchQuery = searchBar.text.toString().trim()
            filterAndDisplayRestaurants()
            true
        }
    }

    private fun setupRefreshButton() {
        refreshBtn.setOnClickListener {
            if (hasLocationPermission) {
                fetchUserLocationAndRestaurants()
            } else {
                requestLocationPermissions()
            }
        }
    }

    private fun checkLocationPermissions() {
        hasLocationPermission = locationService.hasLocationPermissions()
        
        if (hasLocationPermission) {
            showLocationEnabled()
            fetchUserLocationAndRestaurants()
        } else {
            showLocationDisabled()
        }
    }

    private fun showLocationDisabled() {
        locationStatusBar.visibility = View.VISIBLE
        locationStatusText.text = "Location permission required to find nearby restaurants"
        enableLocationBtn.visibility = View.VISIBLE
        enableLocationBtn.setOnClickListener {
            requestLocationPermissions()
        }
        
        // Show empty state
        restaurantsContainer.removeAllViews()
        emptyState.visibility = View.VISIBLE
        statsRestaurantsCount.text = "--"
        statsAccuracy.text = "--"
        deliveryAddressText.text = "Enable location to continue"
    }

    private fun showLocationEnabled() {
        locationStatusBar.visibility = View.GONE
        enableLocationBtn.visibility = View.GONE
    }

    private fun requestLocationPermissions() {
        requestPermissions(
            arrayOf(
                Manifest.permission.ACCESS_FINE_LOCATION,
                Manifest.permission.ACCESS_COARSE_LOCATION
            ),
            LOCATION_PERMISSION_REQUEST_CODE
        )
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        
        if (requestCode == LOCATION_PERMISSION_REQUEST_CODE) {
            hasLocationPermission = grantResults.isNotEmpty() && 
                grantResults.any { it == PackageManager.PERMISSION_GRANTED }
            
            if (hasLocationPermission) {
                showLocationEnabled()
                fetchUserLocationAndRestaurants()
            } else {
                showLocationDisabled()
                Toast.makeText(requireContext(), "Location permission denied.", Toast.LENGTH_LONG).show()
            }
        }
    }

    private fun fetchUserLocationAndRestaurants() {
        locationLoadingOverlay.visibility = View.VISIBLE
        
        lifecycleScope.launch {
            try {
                val location = locationService.getCurrentLocation()
                
                if (location != null) {
                    currentUserLocation = UserLocation.fromLocation(location)
                    showLocationEnabled()
                    updateLocationUi()
                    fetchRestaurants()
                } else {
                    // Fallback to last known location
                    val lastLocation = locationService.getLastKnownLocation()
                    if (lastLocation != null) {
                        currentUserLocation = UserLocation.fromLocation(lastLocation)
                        updateLocationUi()
                        fetchRestaurants()
                    } else {
                        showLocationDisabled()
                        emptyState.visibility = View.VISIBLE
                        restaurantsContainer.visibility = View.GONE
                        Toast.makeText(requireContext(), "Could not get current location.", Toast.LENGTH_SHORT).show()
                    }
                }
            } catch (e: Exception) {
                Toast.makeText(
                    requireContext(),
                    "Location error: ${e.message}",
                    Toast.LENGTH_SHORT
                ).show()
                showLocationDisabled()
                emptyState.visibility = View.VISIBLE
                restaurantsContainer.visibility = View.GONE
            } finally {
                locationLoadingOverlay.visibility = View.GONE
            }
        }
    }
    
    private fun updateLocationUi() {
        val location = currentUserLocation ?: return
        // Location display removed - just update stats
    }

    private fun fetchRestaurants() {
        val location = currentUserLocation ?: return
        
        loadingContainer.visibility = View.VISIBLE
        emptyState.visibility = View.GONE
        restaurantsContainer.visibility = View.GONE
        
        lifecycleScope.launch {
            val result = overpassApiService.queryRestaurants(
                latitude = location.latitude,
                longitude = location.longitude,
                radius = (currentRadiusMiles * METERS_PER_MILE).toInt()
            )
            
            loadingContainer.visibility = View.GONE
            
            result.fold(
                onSuccess = { restaurants ->
                    allRestaurants = restaurants.sortedBy { 
                        it.distanceFrom(location.latitude, location.longitude) 
                    }
                    
                    // Update stats
                    statsRestaurantsCount.text = allRestaurants.size.toString()
                    location.accuracy?.let { 
                        statsAccuracy.text = String.format("%.0f", it)
                    } ?: run {
                        statsAccuracy.text = "--"
                    }
                    
                    // Move map camera to user location
                    moveMapCamera(location.latitude, location.longitude)
                    
                    // Add markers to map
                    addRestaurantMarkers(allRestaurants)
                    
                    // Extract cuisines
                    extractCuisines()
                    
                    // Display restaurants
                    filterAndDisplayRestaurants()
                },
                onFailure = { error ->
                    Toast.makeText(
                        requireContext(),
                        "Failed to fetch restaurants: ${error.message}",
                        Toast.LENGTH_LONG
                    ).show()
                    emptyState.visibility = View.VISIBLE
                }
            )
        }
    }

    private fun extractCuisines() {
        availableCuisines.clear()
        availableCuisines.add("All")
        
        allRestaurants.forEach { restaurant ->
            if (restaurant.cuisine.isNotEmpty() && restaurant.cuisine != "Unknown") {
                // Handle multiple cuisines (semicolon-separated in OSM)
                restaurant.cuisine.split(";").forEach { cuisine ->
                    availableCuisines.add(cuisine.trim().lowercase().replaceFirstChar { it.uppercase() })
                }
            }
        }
        
        setupCuisineButtons()
    }

    private fun setupCuisineButtons() {
        cuisineContainer.removeAllViews()

        availableCuisines.take(10).forEach { cuisine ->
            val button = createCuisineButton(cuisine)
            cuisineContainer.addView(button)
        }
    }

    private fun createCuisineButton(cuisine: String): Button {
        val button = Button(requireContext()).apply {
            text = cuisine
            setTextColor(ContextCompat.getColor(requireContext(), R.color.gray_700))
            textSize = 14f
            setBackgroundResource(R.drawable.cuisine_button_background)
            setPadding(16, 8, 16, 8)
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                marginEnd = 8
            }

            setOnClickListener {
                selectCuisine(cuisine)
            }
        }

        // Set initial state for "All" button
        if (cuisine == "All") {
            button.setTextColor(ContextCompat.getColor(requireContext(), R.color.white))
            button.setBackgroundColor(ContextCompat.getColor(requireContext(), R.color.brand_primary))
        }

        return button
    }

    private fun selectCuisine(cuisine: String) {
        selectedCuisine = if (cuisine == "All") null else cuisine

        // Update button states
        for (i in 0 until cuisineContainer.childCount) {
            val button = cuisineContainer.getChildAt(i) as Button
            val buttonCuisine = availableCuisines.elementAtOrNull(i) ?: continue

            if (buttonCuisine == cuisine) {
                button.setTextColor(ContextCompat.getColor(requireContext(), R.color.white))
                button.setBackgroundColor(ContextCompat.getColor(requireContext(), R.color.brand_primary))
            } else {
                button.setTextColor(ContextCompat.getColor(requireContext(), R.color.gray_700))
                button.setBackgroundResource(R.drawable.cuisine_button_background)
            }
        }

        // Filter and display restaurants
        filterAndDisplayRestaurants()
        persistDiscoveryPreferences()
    }

    private fun filterAndDisplayRestaurants() {
        val location = currentUserLocation ?: return
        
        val filtered = allRestaurants.filter { restaurant ->
            val matchesCuisine = selectedCuisine == null || 
                restaurant.cuisine.contains(selectedCuisine!!, ignoreCase = true)
            val matchesSearch = searchQuery.isEmpty() ||
                    restaurant.name.contains(searchQuery, ignoreCase = true) ||
                    restaurant.cuisine.contains(searchQuery, ignoreCase = true)
            matchesCuisine && matchesSearch
        }.sortedBy { it.distanceFrom(location.latitude, location.longitude) }

        displayRestaurants(filtered)
    }

    private fun displayRestaurants(restaurants: List<OverpassRestaurant>) {
        restaurantsContainer.removeAllViews()

        if (restaurants.isEmpty()) {
            emptyState.visibility = View.VISIBLE
            restaurantsContainer.visibility = View.GONE
            return
        }

        emptyState.visibility = View.GONE
        restaurantsContainer.visibility = View.VISIBLE

        restaurants.forEach { restaurant ->
            val card = createRestaurantCard(restaurant)
            restaurantsContainer.addView(card)
        }
    }

    private fun createRestaurantCard(restaurant: OverpassRestaurant): CardView {
        val location = currentUserLocation!!
        val distanceKm = restaurant.distanceFrom(location.latitude, location.longitude)
        val distanceMiles = distanceKm * 0.621371
        val distanceText = if (distanceMiles < 0.1) {
            "${String.format("%.0f", distanceMiles * 5280)} ft"
        } else {
            "${String.format("%.1f", distanceMiles)} mi"
        }

        val card = CardView(requireContext()).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                bottomMargin = 12
            }
            radius = 12f
            cardElevation = 4f
            setCardBackgroundColor(ContextCompat.getColor(requireContext(), android.R.color.white))
        }

        val cardLayout = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(16, 16, 16, 16)
        }

        // Icon
        val iconView = androidx.appcompat.widget.AppCompatImageView(requireContext()).apply {
            layoutParams = LinearLayout.LayoutParams(60, 60).apply {
                gravity = android.view.Gravity.CENTER_VERTICAL
            }
            setImageResource(R.drawable.ic_restaurant)
            setBackgroundResource(getCuisineIconBackground(restaurant.cuisine))
            setPadding(12, 12, 12, 12)
        }

        // Content
        val contentLayout = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
            layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f).apply {
                marginStart = 16
            }
        }

        val nameText = TextView(requireContext()).apply {
            text = restaurant.name
            textSize = 16f
            setTypeface(null, android.graphics.Typeface.BOLD)
            setTextColor(ContextCompat.getColor(requireContext(), R.color.gray_900))
        }

        val cuisineDisplayName = restaurant.getCuisineDisplayName()
        val detailsText = TextView(requireContext()).apply {
            text = "$cuisineDisplayName • $distanceText"
            textSize = 12f
            setTextColor(ContextCompat.getColor(requireContext(), R.color.gray_600))
        }

        // Tags
        val tagsLayout = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(0, 4, 0, 0)
        }

        restaurant.tags.take(3).forEach { tag ->
            val tagText = TextView(requireContext()).apply {
                text = tag
                textSize = 10f
                setTextColor(getTagTextColor(tag))
                background = ContextCompat.getDrawable(requireContext(), getTagBackground(tag))
                setPadding(4, 2, 4, 2)
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.WRAP_CONTENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                ).apply {
                    marginEnd = 8
                }
            }
            tagsLayout.addView(tagText)
        }

        contentLayout.addView(nameText)
        contentLayout.addView(detailsText)
        contentLayout.addView(tagsLayout)

        // Info layout
        val infoLayout = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                gravity = android.view.Gravity.CENTER_VERTICAL
            }
        }

        // Show distance prominently
        val distanceView = TextView(requireContext()).apply {
            text = distanceText
            textSize = 14f
            setTextColor(ContextCompat.getColor(requireContext(), R.color.brand_primary))
            setTypeface(null, android.graphics.Typeface.BOLD)
        }
        infoLayout.addView(distanceView)

        if (restaurant.delivery) {
            val deliveryText = TextView(requireContext()).apply {
                text = "Delivery"
                textSize = 10f
                setTextColor(ContextCompat.getColor(requireContext(), R.color.green_600))
            }
            infoLayout.addView(deliveryText)
        } else if (restaurant.takeaway) {
            val takeawayText = TextView(requireContext()).apply {
                text = "Takeaway"
                textSize = 10f
                setTextColor(ContextCompat.getColor(requireContext(), R.color.blue_600))
            }
            infoLayout.addView(takeawayText)
        }

        cardLayout.addView(iconView)
        cardLayout.addView(contentLayout)
        cardLayout.addView(infoLayout)

        card.addView(cardLayout)

        // Add click listener
        card.setOnClickListener {
            showRestaurantDetails(restaurant)
        }

        return card
    }

    private fun showRestaurantDetails(restaurant: OverpassRestaurant) {
        val message = buildString {
            append(restaurant.name)
            restaurant.address?.let { append("\n$it") }
            restaurant.phone?.let { append("\n📞 $it") }
            restaurant.website?.let { append("\n🌐 $it") }
            restaurant.openingHours?.let { append("\n🕐 $it") }
        }
        
        Toast.makeText(requireContext(), message, Toast.LENGTH_LONG).show()
    }

    private fun getCuisineIconBackground(cuisine: String): Int {
        return when (cuisine.lowercase()) {
            "pizza", "italian" -> R.drawable.pizza_icon_background
            "mexican", "tacos" -> R.drawable.mexican_icon_background
            else -> R.drawable.pizza_icon_background
        }
    }

    private fun getTagTextColor(tag: String): Int {
        return when (tag.lowercase()) {
            "takeaway" -> ContextCompat.getColor(requireContext(), R.color.green_700)
            "delivery" -> ContextCompat.getColor(requireContext(), R.color.blue_700)
            "wheelchair" -> ContextCompat.getColor(requireContext(), R.color.purple_700)
            "outdoor seating" -> ContextCompat.getColor(requireContext(), R.color.teal_700)
            "wifi" -> ContextCompat.getColor(requireContext(), R.color.blue_700)
            else -> ContextCompat.getColor(requireContext(), R.color.gray_700)
        }
    }

    private fun getTagBackground(tag: String): Int {
        return when (tag.lowercase()) {
            "takeaway" -> R.drawable.tag_background_green
            "delivery" -> R.drawable.tag_background_blue
            "wheelchair" -> R.drawable.tag_background_purple
            "outdoor seating" -> R.drawable.tag_background_teal
            "wifi" -> R.drawable.tag_background_blue
            else -> R.drawable.tag_background_gray
        }
    }
    
    // MapView lifecycle methods
    override fun onStart() {
        super.onStart()
        mapView.onStart()
    }
    
    override fun onResume() {
        super.onResume()
        mapView.onResume()
    }
    
    override fun onPause() {
        super.onPause()
        mapView.onPause()
    }
    
    override fun onStop() {
        super.onStop()
        mapView.onStop()
    }
    
    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        mapView.onSaveInstanceState(outState)
    }
    
    override fun onLowMemory() {
        super.onLowMemory()
        mapView.onLowMemory()
    }
    
    override fun onDestroyView() {
        super.onDestroyView()
        mapView.onDestroy()
    }
}
