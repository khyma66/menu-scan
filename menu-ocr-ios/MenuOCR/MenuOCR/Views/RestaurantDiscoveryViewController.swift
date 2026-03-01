//
//  RestaurantDiscoveryViewController.swift
//  MenuOCR
//
//  Restaurant Discovery with DoorDash-like UI
//  Equivalent to Android RestaurantDiscoveryFragment.kt
//

import UIKit
import CoreLocation

class RestaurantDiscoveryViewController: UIViewController {
    
    // MARK: - Services (injected via associated objects from DoorDashTabBarController)
    // locationService and overpassService are defined in an extension
    private let apiService = ApiService()
    
    // MARK: - State
    
    private var currentLocation: UserLocation?
    private var allRestaurants: [OverpassRestaurant] = []
    private var filteredRestaurants: [OverpassRestaurant] = []
    private var selectedCuisine: String?
    private var searchQuery: String = ""
    private var currentRadiusMiles: Int = 10
    private var availableCuisines: [String] = ["All"]
    
    // MARK: - UI Components
    
    private let scrollView = UIScrollView()
    private let contentView = UIView()
    
    // Header
    private let headerView = UIView()
    private let titleLabel = UILabel()
    private let subtitleLabel = UILabel()
    private let profileButton = UIButton()
    
    // Location status
    private let locationStatusBar = UIView()
    private let locationStatusIcon = UIImageView()
    private let locationStatusLabel = UILabel()
    private let enableLocationButton = UIButton()
    
    // Search
    private let searchBar = UISearchBar()
    
    // Distance selector
    private let distanceContainer = UIView()
    private let distanceLabel = UILabel()
    private let distanceSlider = UISlider()
    private let distanceValueLabel = UILabel()
    
    // Stats
    private let statsStackView = UIStackView()
    private var restaurantsCountLabel = UILabel()
    private var radiusLabel = UILabel()
    private var accuracyLabel = UILabel()
    
    // Cuisine categories
    private let cuisineScrollView = UIScrollView()
    private let cuisineStackView = UIStackView()
    
    // Restaurants
    private let restaurantsStackView = UIStackView()
    
    // Loading
    private let loadingContainer = UIView()
    private let loadingIndicator = UIActivityIndicatorView(style: .large)
    private let loadingLabel = UILabel()
    
    // Empty state
    private let emptyStateView = UIView()
    private let emptyStateIcon = UILabel()
    private let emptyStateLabel = UILabel()
    
    // Refresh
    private let refreshButton = UIButton()
    
    // MARK: - Lifecycle
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
        setupConstraints()
        loadDiscoveryPreferences()
        checkLocationPermissions()
    }

    private func loadDiscoveryPreferences() {
        Task {
            do {
                let prefs = try await apiService.getDiscoveryPreferences()
                await MainActor.run {
                    currentRadiusMiles = max(1, min(20, prefs.search_radius_miles))
                    distanceSlider.value = Float(currentRadiusMiles)
                    distanceValueLabel.text = "\(currentRadiusMiles) mi"
                    selectedCuisine = prefs.selected_cuisines.first
                    updateCuisineButtons()
                    updateStats()
                }
            } catch {
            }
        }
    }

    private func persistDiscoveryPreferences() {
        Task {
            do {
                let selected = selectedCuisine.map { [$0] } ?? []
                _ = try await apiService.updateDiscoveryPreferences(
                    request: DiscoveryPreferencesRequest(
                        search_radius_miles: currentRadiusMiles,
                        selected_cuisines: selected,
                        location_label: nil,
                        latitude: currentLocation?.latitude,
                        longitude: currentLocation?.longitude
                    )
                )
            } catch {
                await MainActor.run {
                    let banner = UILabel()
                    banner.text = "Failed to save preferences"
                    banner.textColor = .white
                    banner.backgroundColor = UIColor.systemRed.withAlphaComponent(0.9)
                    banner.textAlignment = .center
                    banner.font = .systemFont(ofSize: 14, weight: .medium)
                    banner.frame = CGRect(x: 0, y: self.view.safeAreaInsets.top, width: self.view.bounds.width, height: 36)
                    banner.layer.cornerRadius = 8
                    banner.clipsToBounds = true
                    self.view.addSubview(banner)
                    UIView.animate(withDuration: 0.3, delay: 2.0, options: [], animations: { banner.alpha = 0 }) { _ in banner.removeFromSuperview() }
                }
            }
        }
    }
    
    // MARK: - UI Setup
    
    private func setupUI() {
        view.backgroundColor = .systemGray6
        
        // Status bar background to match header
        let statusBarBg = UIView()
        statusBarBg.backgroundColor = UIColor(red: 0.816, green: 0.322, blue: 0.125, alpha: 1.0) // Discover #D05220
        statusBarBg.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(statusBarBg)
        NSLayoutConstraint.activate([
            statusBarBg.topAnchor.constraint(equalTo: view.topAnchor),
            statusBarBg.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            statusBarBg.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            statusBarBg.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
        ])
        
        // Setup navigation
        title = "Discover"
        navigationController?.navigationBar.prefersLargeTitles = false
        
        // Scroll view
        scrollView.translatesAutoresizingMaskIntoConstraints = false
        contentView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(scrollView)
        scrollView.addSubview(contentView)
        
        // Header
        setupHeader()
        
        // Location status
        setupLocationStatus()
        
        // Search
        setupSearch()
        
        // Distance selector
        setupDistanceSelector()
        
        // Stats
        setupStats()
        
        // Cuisine categories
        setupCuisineCategories()
        
        // Restaurants
        setupRestaurants()
        
        // Loading
        setupLoading()
        
        // Empty state
        setupEmptyState()
        
        // Refresh button
        setupRefreshButton()
    }
    
    private func setupHeader() {
        headerView.backgroundColor = UIColor(red: 0.816, green: 0.322, blue: 0.125, alpha: 1.0) // Discover #D05220
        headerView.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(headerView)
        
        titleLabel.text = "Discover"
        titleLabel.font = .systemFont(ofSize: 20, weight: .bold)
        titleLabel.textColor = .white
        titleLabel.textAlignment = .center
        titleLabel.translatesAutoresizingMaskIntoConstraints = false
        headerView.addSubview(titleLabel)
        
        // Subtitle removed per UX simplicity rules
        subtitleLabel.isHidden = true
        subtitleLabel.translatesAutoresizingMaskIntoConstraints = false
        headerView.addSubview(subtitleLabel)
        
        profileButton.setImage(UIImage(systemName: "person.circle.fill"), for: .normal)
        profileButton.tintColor = .white
        profileButton.addTarget(self, action: #selector(profileTapped), for: .touchUpInside)
        profileButton.translatesAutoresizingMaskIntoConstraints = false
        headerView.addSubview(profileButton)
    }
    
    private func setupLocationStatus() {
        locationStatusBar.backgroundColor = .systemYellow.withAlphaComponent(0.2)
        locationStatusBar.layer.cornerRadius = 8
        locationStatusBar.isHidden = true
        locationStatusBar.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(locationStatusBar)
        
        locationStatusIcon.image = UIImage(systemName: "location.slash")
        locationStatusIcon.tintColor = .systemOrange
        locationStatusIcon.translatesAutoresizingMaskIntoConstraints = false
        locationStatusBar.addSubview(locationStatusIcon)
        
        locationStatusLabel.text = "Location permission required"
        locationStatusLabel.font = .systemFont(ofSize: 14)
        locationStatusLabel.textColor = .systemOrange
        locationStatusLabel.translatesAutoresizingMaskIntoConstraints = false
        locationStatusBar.addSubview(locationStatusLabel)
        
        enableLocationButton.setTitle("Enable", for: .normal)
        enableLocationButton.backgroundColor = .systemOrange
        enableLocationButton.setTitleColor(.white, for: .normal)
        enableLocationButton.layer.cornerRadius = 8
        enableLocationButton.addTarget(self, action: #selector(enableLocationTapped), for: .touchUpInside)
        enableLocationButton.translatesAutoresizingMaskIntoConstraints = false
        locationStatusBar.addSubview(enableLocationButton)
    }
    
    private func setupSearch() {
        searchBar.placeholder = "Search"
        searchBar.searchBarStyle = .minimal
        searchBar.delegate = self
        searchBar.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(searchBar)
    }
    
    private func setupDistanceSelector() {
        distanceContainer.backgroundColor = .systemBackground
        distanceContainer.layer.cornerRadius = 12
        distanceContainer.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(distanceContainer)
        
        distanceLabel.text = "📍 Distance"
        distanceLabel.font = .boldSystemFont(ofSize: 16)
        distanceLabel.translatesAutoresizingMaskIntoConstraints = false
        distanceContainer.addSubview(distanceLabel)
        
        distanceSlider.minimumValue = 1
        distanceSlider.maximumValue = 20
        distanceSlider.value = Float(currentRadiusMiles)
        distanceSlider.addTarget(self, action: #selector(distanceSliderChanged), for: .valueChanged)
        distanceSlider.translatesAutoresizingMaskIntoConstraints = false
        distanceContainer.addSubview(distanceSlider)
        
        distanceValueLabel.text = "\(currentRadiusMiles) mi"
        distanceValueLabel.font = .boldSystemFont(ofSize: 16)
        distanceValueLabel.textColor = UIColor(red: 1.0, green: 0.3, blue: 0.22, alpha: 1.0)
        distanceValueLabel.translatesAutoresizingMaskIntoConstraints = false
        distanceContainer.addSubview(distanceValueLabel)
    }
    
    private func setupStats() {
        statsStackView.axis = .horizontal
        statsStackView.distribution = .fillEqually
        statsStackView.spacing = 8
        statsStackView.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(statsStackView)
        
        let restaurantsCard = createStatsCard(title: "--", subtitle: "Restaurants", color: UIColor(red: 1.0, green: 0.3, blue: 0.22, alpha: 1.0))
        let radiusCard = createStatsCard(title: "\(currentRadiusMiles) mi", subtitle: "Radius", color: .systemGreen)
        let accuracyCard = createStatsCard(title: "--", subtitle: "Accuracy (m)", color: .systemBlue)
        
        // Get labels from cards - the stack view is the first subview
        if let restaurantsStack = restaurantsCard.subviews.first(where: { $0 is UIStackView }) as? UIStackView {
            restaurantsCountLabel = restaurantsStack.arrangedSubviews.first as? UILabel ?? UILabel()
        }
        if let radiusStack = radiusCard.subviews.first(where: { $0 is UIStackView }) as? UIStackView {
            radiusLabel = radiusStack.arrangedSubviews.first as? UILabel ?? UILabel()
        }
        if let accuracyStack = accuracyCard.subviews.first(where: { $0 is UIStackView }) as? UIStackView {
            accuracyLabel = accuracyStack.arrangedSubviews.first as? UILabel ?? UILabel()
        }
        
        statsStackView.addArrangedSubview(restaurantsCard)
        statsStackView.addArrangedSubview(radiusCard)
        statsStackView.addArrangedSubview(accuracyCard)
    }
    
    private func createStatsCard(title: String, subtitle: String, color: UIColor) -> UIView {
        let card = UIView()
        card.backgroundColor = .systemBackground
        card.layer.cornerRadius = 12
        card.layer.shadowColor = UIColor.black.cgColor
        card.layer.shadowOffset = CGSize(width: 0, height: 2)
        card.layer.shadowOpacity = 0.1
        card.layer.shadowRadius = 8
        
        let titleLabel = UILabel()
        titleLabel.text = title
        titleLabel.font = .boldSystemFont(ofSize: 20)
        titleLabel.textColor = color
        titleLabel.textAlignment = .center
        
        let subtitleLabel = UILabel()
        subtitleLabel.text = subtitle
        subtitleLabel.font = .systemFont(ofSize: 12)
        subtitleLabel.textColor = .secondaryLabel
        subtitleLabel.textAlignment = .center
        
        let stack = UIStackView(arrangedSubviews: [titleLabel, subtitleLabel])
        stack.axis = .vertical
        stack.spacing = 4
        stack.alignment = .center
        stack.translatesAutoresizingMaskIntoConstraints = false
        
        card.addSubview(stack)
        
        NSLayoutConstraint.activate([
            stack.centerXAnchor.constraint(equalTo: card.centerXAnchor),
            stack.centerYAnchor.constraint(equalTo: card.centerYAnchor),
            card.heightAnchor.constraint(equalToConstant: 80)
        ])
        
        return card
    }
    
    private func setupCuisineCategories() {
        cuisineScrollView.showsHorizontalScrollIndicator = false
        cuisineScrollView.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(cuisineScrollView)
        
        cuisineStackView.axis = .horizontal
        cuisineStackView.spacing = 8
        cuisineStackView.translatesAutoresizingMaskIntoConstraints = false
        cuisineScrollView.addSubview(cuisineStackView)
        
        // Add initial "All" button
        updateCuisineButtons()
    }
    
    private func setupRestaurants() {
        restaurantsStackView.axis = .vertical
        restaurantsStackView.spacing = 12
        restaurantsStackView.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(restaurantsStackView)
    }
    
    private func setupLoading() {
        loadingContainer.backgroundColor = .systemBackground
        loadingContainer.layer.cornerRadius = 12
        loadingContainer.isHidden = true
        loadingContainer.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(loadingContainer)
        
        loadingIndicator.color = UIColor(red: 1.0, green: 0.3, blue: 0.22, alpha: 1.0)
        loadingIndicator.translatesAutoresizingMaskIntoConstraints = false
        loadingContainer.addSubview(loadingIndicator)
        
        loadingLabel.text = "Finding restaurants..."
        loadingLabel.font = .systemFont(ofSize: 16)
        loadingLabel.textColor = .secondaryLabel
        loadingLabel.translatesAutoresizingMaskIntoConstraints = false
        loadingContainer.addSubview(loadingLabel)
    }
    
    private func setupEmptyState() {
        emptyStateView.isHidden = true
        emptyStateView.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(emptyStateView)
        
        emptyStateIcon.text = "🍽️"
        emptyStateIcon.font = .systemFont(ofSize: 60)
        emptyStateIcon.textAlignment = .center
        emptyStateIcon.translatesAutoresizingMaskIntoConstraints = false
        emptyStateView.addSubview(emptyStateIcon)
        
        emptyStateLabel.text = "No restaurants found\nTry increasing the search radius"
        emptyStateLabel.font = .systemFont(ofSize: 16)
        emptyStateLabel.textColor = .secondaryLabel
        emptyStateLabel.textAlignment = .center
        emptyStateLabel.numberOfLines = 0
        emptyStateLabel.translatesAutoresizingMaskIntoConstraints = false
        emptyStateView.addSubview(emptyStateLabel)
    }
    
    private func setupRefreshButton() {
        refreshButton.setTitle("🔄 Refresh", for: .normal)
        refreshButton.backgroundColor = UIColor(red: 1.0, green: 0.3, blue: 0.22, alpha: 1.0)
        refreshButton.setTitleColor(.white, for: .normal)
        refreshButton.layer.cornerRadius = 12
        refreshButton.addTarget(self, action: #selector(refreshTapped), for: .touchUpInside)
        refreshButton.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(refreshButton)
    }
    
    // MARK: - Constraints
    
    private func setupConstraints() {
        NSLayoutConstraint.activate([
            // Scroll view
            scrollView.topAnchor.constraint(equalTo: view.topAnchor),
            scrollView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            scrollView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            scrollView.bottomAnchor.constraint(equalTo: view.bottomAnchor),
            
            contentView.topAnchor.constraint(equalTo: scrollView.topAnchor),
            contentView.leadingAnchor.constraint(equalTo: scrollView.leadingAnchor),
            contentView.trailingAnchor.constraint(equalTo: scrollView.trailingAnchor),
            contentView.bottomAnchor.constraint(equalTo: scrollView.bottomAnchor),
            contentView.widthAnchor.constraint(equalTo: scrollView.widthAnchor),
            
            // Header
            headerView.topAnchor.constraint(equalTo: contentView.topAnchor),
            headerView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor),
            headerView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor),
            headerView.heightAnchor.constraint(equalToConstant: 56),
            
            titleLabel.centerXAnchor.constraint(equalTo: headerView.centerXAnchor),
            titleLabel.centerYAnchor.constraint(equalTo: headerView.centerYAnchor),
            
            profileButton.trailingAnchor.constraint(equalTo: headerView.trailingAnchor, constant: -16),
            profileButton.centerYAnchor.constraint(equalTo: headerView.centerYAnchor),
            profileButton.widthAnchor.constraint(equalToConstant: 40),
            profileButton.heightAnchor.constraint(equalToConstant: 40),
            
            // Location status
            locationStatusBar.topAnchor.constraint(equalTo: headerView.bottomAnchor, constant: 8),
            locationStatusBar.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            locationStatusBar.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            locationStatusBar.heightAnchor.constraint(equalToConstant: 50),
            
            locationStatusIcon.leadingAnchor.constraint(equalTo: locationStatusBar.leadingAnchor, constant: 12),
            locationStatusIcon.centerYAnchor.constraint(equalTo: locationStatusBar.centerYAnchor),
            locationStatusIcon.widthAnchor.constraint(equalToConstant: 24),
            locationStatusIcon.heightAnchor.constraint(equalToConstant: 24),
            
            locationStatusLabel.leadingAnchor.constraint(equalTo: locationStatusIcon.trailingAnchor, constant: 8),
            locationStatusLabel.centerYAnchor.constraint(equalTo: locationStatusBar.centerYAnchor),
            
            enableLocationButton.trailingAnchor.constraint(equalTo: locationStatusBar.trailingAnchor, constant: -12),
            enableLocationButton.centerYAnchor.constraint(equalTo: locationStatusBar.centerYAnchor),
            enableLocationButton.widthAnchor.constraint(equalToConstant: 80),
            enableLocationButton.heightAnchor.constraint(equalToConstant: 32),
            
            // Search
            searchBar.topAnchor.constraint(equalTo: locationStatusBar.bottomAnchor, constant: 8),
            searchBar.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 8),
            searchBar.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -8),
            
            // Distance
            distanceContainer.topAnchor.constraint(equalTo: searchBar.bottomAnchor, constant: 8),
            distanceContainer.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            distanceContainer.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            distanceContainer.heightAnchor.constraint(equalToConstant: 60),
            
            distanceLabel.leadingAnchor.constraint(equalTo: distanceContainer.leadingAnchor, constant: 16),
            distanceLabel.centerYAnchor.constraint(equalTo: distanceContainer.centerYAnchor),
            
            distanceSlider.leadingAnchor.constraint(equalTo: distanceLabel.trailingAnchor, constant: 16),
            distanceSlider.centerYAnchor.constraint(equalTo: distanceContainer.centerYAnchor),
            
            distanceValueLabel.leadingAnchor.constraint(equalTo: distanceSlider.trailingAnchor, constant: 8),
            distanceValueLabel.trailingAnchor.constraint(equalTo: distanceContainer.trailingAnchor, constant: -16),
            distanceValueLabel.centerYAnchor.constraint(equalTo: distanceContainer.centerYAnchor),
            distanceValueLabel.widthAnchor.constraint(equalToConstant: 50),
            
            // Stats
            statsStackView.topAnchor.constraint(equalTo: distanceContainer.bottomAnchor, constant: 16),
            statsStackView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            statsStackView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            
            // Cuisine
            cuisineScrollView.topAnchor.constraint(equalTo: statsStackView.bottomAnchor, constant: 16),
            cuisineScrollView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor),
            cuisineScrollView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor),
            cuisineScrollView.heightAnchor.constraint(equalToConstant: 40),
            
            cuisineStackView.topAnchor.constraint(equalTo: cuisineScrollView.topAnchor),
            cuisineStackView.leadingAnchor.constraint(equalTo: cuisineScrollView.leadingAnchor, constant: 16),
            cuisineStackView.trailingAnchor.constraint(equalTo: cuisineScrollView.trailingAnchor, constant: -16),
            cuisineStackView.bottomAnchor.constraint(equalTo: cuisineScrollView.bottomAnchor),
            
            // Restaurants
            restaurantsStackView.topAnchor.constraint(equalTo: cuisineScrollView.bottomAnchor, constant: 16),
            restaurantsStackView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            restaurantsStackView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            
            // Loading
            loadingContainer.topAnchor.constraint(equalTo: restaurantsStackView.topAnchor),
            loadingContainer.leadingAnchor.constraint(equalTo: restaurantsStackView.leadingAnchor),
            loadingContainer.trailingAnchor.constraint(equalTo: restaurantsStackView.trailingAnchor),
            loadingContainer.heightAnchor.constraint(equalToConstant: 100),
            
            loadingIndicator.centerXAnchor.constraint(equalTo: loadingContainer.centerXAnchor, constant: -60),
            loadingIndicator.centerYAnchor.constraint(equalTo: loadingContainer.centerYAnchor),
            
            loadingLabel.leadingAnchor.constraint(equalTo: loadingIndicator.trailingAnchor, constant: 16),
            loadingLabel.centerYAnchor.constraint(equalTo: loadingContainer.centerYAnchor),
            
            // Empty state
            emptyStateView.topAnchor.constraint(equalTo: restaurantsStackView.topAnchor),
            emptyStateView.leadingAnchor.constraint(equalTo: restaurantsStackView.leadingAnchor),
            emptyStateView.trailingAnchor.constraint(equalTo: restaurantsStackView.trailingAnchor),
            emptyStateView.heightAnchor.constraint(equalToConstant: 200),
            
            emptyStateIcon.centerXAnchor.constraint(equalTo: emptyStateView.centerXAnchor),
            emptyStateIcon.topAnchor.constraint(equalTo: emptyStateView.topAnchor, constant: 40),
            
            emptyStateLabel.topAnchor.constraint(equalTo: emptyStateIcon.bottomAnchor, constant: 16),
            emptyStateLabel.centerXAnchor.constraint(equalTo: emptyStateView.centerXAnchor),
            
            // Refresh
            refreshButton.topAnchor.constraint(equalTo: restaurantsStackView.bottomAnchor, constant: 16),
            refreshButton.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            refreshButton.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            refreshButton.heightAnchor.constraint(equalToConstant: 50),
            refreshButton.bottomAnchor.constraint(equalTo: contentView.bottomAnchor, constant: -32)
        ])
    }
    
    // MARK: - Location
    
    private func checkLocationPermissions() {
        guard let locationService = locationService else {
            showLocationDisabled()
            return
        }
        
        if locationService.hasLocationPermission() {
            showLocationEnabled()
            fetchUserLocationAndRestaurants()
        } else {
            showLocationDisabled()
        }
    }
    
    private func showLocationDisabled() {
        locationStatusBar.isHidden = false
        locationStatusLabel.text = "Location permission required to find nearby restaurants"
        emptyStateView.isHidden = false
        restaurantsStackView.isHidden = true
    }
    
    private func showLocationEnabled() {
        locationStatusBar.isHidden = true
        emptyStateView.isHidden = true
        restaurantsStackView.isHidden = false
    }
    
    @objc private func enableLocationTapped() {
        locationService?.requestLocationPermission()
    }
    
    // MARK: - Data Fetching
    
    private func fetchUserLocationAndRestaurants() {
        showLoading(true)
        
        Task {
            do {
                guard let locationService = locationService else { return }
                
                let location = try await locationService.getCurrentLocation()
                currentLocation = location
                
                await MainActor.run {
                    showLocationEnabled()
                    updateStats()
                }
                
                await fetchRestaurants()
                
            } catch {
                await MainActor.run {
                    showLoading(false)
                    showLocationDisabled()
                    locationStatusLabel.text = "Could not get location: \(error.localizedDescription)"
                }
            }
        }
    }
    
    private func fetchRestaurants() async {
        guard let location = currentLocation,
              let overpassService = overpassService else {
            await MainActor.run { showLoading(false) }
            return
        }
        
        let radiusMeters = Int(Double(currentRadiusMiles) * 1609.34)
        
        do {
            let restaurants = try await overpassService.queryRestaurants(
                latitude: location.latitude,
                longitude: location.longitude,
                radius: radiusMeters
            )
            
            await MainActor.run {
                self.allRestaurants = restaurants
                self.extractCuisines()
                self.filterAndDisplayRestaurants()
                self.showLoading(false)
                self.updateStats()
            }
            
        } catch {
            await MainActor.run {
                self.showLoading(false)
                self.emptyStateView.isHidden = false
                self.emptyStateLabel.text = "Failed to load restaurants:\n\(error.localizedDescription)"
            }
        }
    }
    
    private func extractCuisines() {
        var cuisines = Set<String>()
        cuisines.insert("All")
        
        for restaurant in allRestaurants {
            if !restaurant.cuisine.isEmpty && restaurant.cuisine != "Unknown" {
                restaurant.cuisine.split(separator: ";").forEach { cuisine in
                    let trimmed = cuisine.trimmingCharacters(in: .whitespaces).capitalized
                    cuisines.insert(trimmed)
                }
            }
        }
        
        availableCuisines = Array(cuisines).sorted()
        availableCuisines.remove(at: availableCuisines.firstIndex(of: "All")!)
        availableCuisines.insert("All", at: 0)
        
        updateCuisineButtons()
    }
    
    private func updateCuisineButtons() {
        cuisineStackView.arrangedSubviews.forEach { $0.removeFromSuperview() }
        
        for cuisine in availableCuisines.prefix(10) {
            let button = createCuisineButton(cuisine)
            cuisineStackView.addArrangedSubview(button)
        }
    }
    
    private func createCuisineButton(_ cuisine: String) -> UIButton {
        let button = UIButton()
        button.setTitle(cuisine, for: .normal)
        button.titleLabel?.font = .systemFont(ofSize: 14, weight: .medium)
        
        let isSelected = (cuisine == selectedCuisine) || (cuisine == "All" && selectedCuisine == nil)
        
        if isSelected {
            button.backgroundColor = UIColor(red: 1.0, green: 0.3, blue: 0.22, alpha: 1.0)
            button.setTitleColor(.white, for: .normal)
        } else {
            button.backgroundColor = .systemBackground
            button.setTitleColor(.darkGray, for: .normal)
        }
        
        button.layer.cornerRadius = 16
        button.contentEdgeInsets = UIEdgeInsets(top: 8, left: 16, bottom: 8, right: 16)
        button.addTarget(self, action: #selector(cuisineTapped(_:)), for: .touchUpInside)
        
        return button
    }
    
    @objc private func cuisineTapped(_ sender: UIButton) {
        guard let title = sender.title(for: .normal) else { return }
        selectedCuisine = (title == "All") ? nil : title
        updateCuisineButtons()
        filterAndDisplayRestaurants()
        persistDiscoveryPreferences()
    }
    
    private func filterAndDisplayRestaurants() {
        guard let location = currentLocation else { return }
        
        filteredRestaurants = allRestaurants.filter { restaurant in
            let matchesCuisine = selectedCuisine == nil ||
                restaurant.cuisine.localizedCaseInsensitiveContains(selectedCuisine!)
            let matchesSearch = searchQuery.isEmpty ||
                restaurant.name.localizedCaseInsensitiveContains(searchQuery) ||
                restaurant.cuisine.localizedCaseInsensitiveContains(searchQuery)
            return matchesCuisine && matchesSearch
        }.sorted { $0.distanceFrom(location.latitude, location.longitude) < $1.distanceFrom(location.latitude, location.longitude) }
        
        displayRestaurants()
    }
    
    private func displayRestaurants() {
        restaurantsStackView.arrangedSubviews.forEach { $0.removeFromSuperview() }
        
        if filteredRestaurants.isEmpty {
            emptyStateView.isHidden = false
            restaurantsStackView.isHidden = true
            return
        }
        
        emptyStateView.isHidden = true
        restaurantsStackView.isHidden = false
        
        for restaurant in filteredRestaurants {
            let card = createRestaurantCard(restaurant)
            restaurantsStackView.addArrangedSubview(card)
        }
    }
    
    private func createRestaurantCard(_ restaurant: OverpassRestaurant) -> UIView {
        let card = UIView()
        card.backgroundColor = .systemBackground
        card.layer.cornerRadius = 12
        card.layer.shadowColor = UIColor.black.cgColor
        card.layer.shadowOffset = CGSize(width: 0, height: 2)
        card.layer.shadowOpacity = 0.1
        card.layer.shadowRadius = 8
        
        // Calculate distance
        let distanceMeters = currentLocation.map { restaurant.distanceFrom($0.latitude, $0.longitude) } ?? 0
        let distanceMiles = distanceMeters * 0.000621371
        let distanceText: String
        if distanceMiles < 0.1 {
            distanceText = String(format: "%.0f ft", distanceMiles * 5280)
        } else {
            distanceText = String(format: "%.1f mi", distanceMiles)
        }
        
        // Icon
        let iconView = UIView()
        iconView.backgroundColor = UIColor.systemOrange.withAlphaComponent(0.2)
        iconView.layer.cornerRadius = 25
        iconView.translatesAutoresizingMaskIntoConstraints = false
        card.addSubview(iconView)
        
        let iconLabel = UILabel()
        iconLabel.text = "🍽️"
        iconLabel.font = .systemFont(ofSize: 20)
        iconLabel.textAlignment = .center
        iconLabel.translatesAutoresizingMaskIntoConstraints = false
        iconView.addSubview(iconLabel)
        
        // Content
        let nameLabel = UILabel()
        nameLabel.text = restaurant.name
        nameLabel.font = .boldSystemFont(ofSize: 16)
        nameLabel.translatesAutoresizingMaskIntoConstraints = false
        card.addSubview(nameLabel)
        
        let detailsLabel = UILabel()
        detailsLabel.text = "\(restaurant.getCuisineDisplayName()) • \(distanceText)"
        detailsLabel.font = .systemFont(ofSize: 12)
        detailsLabel.textColor = .secondaryLabel
        detailsLabel.translatesAutoresizingMaskIntoConstraints = false
        card.addSubview(detailsLabel)
        
        // Tags
        let tagsStack = UIStackView()
        tagsStack.axis = .horizontal
        tagsStack.spacing = 4
        tagsStack.translatesAutoresizingMaskIntoConstraints = false
        card.addSubview(tagsStack)
        
        for tag in restaurant.tags.prefix(3) {
            let tagLabel = UILabel()
            tagLabel.text = tag
            tagLabel.font = .systemFont(ofSize: 10)
            tagLabel.textColor = .white
            tagLabel.backgroundColor = tagColor(for: tag)
            tagLabel.layer.cornerRadius = 4
            tagLabel.clipsToBounds = true
            tagLabel.textAlignment = .center
            tagLabel.translatesAutoresizingMaskIntoConstraints = false
            tagLabel.widthAnchor.constraint(equalToConstant: 70).isActive = true
            tagLabel.heightAnchor.constraint(equalToConstant: 16).isActive = true
            tagsStack.addArrangedSubview(tagLabel)
        }
        
        // Distance label
        let distanceLabel = UILabel()
        distanceLabel.text = distanceText
        distanceLabel.font = .boldSystemFont(ofSize: 14)
        distanceLabel.textColor = UIColor(red: 1.0, green: 0.3, blue: 0.22, alpha: 1.0)
        distanceLabel.textAlignment = .right
        distanceLabel.translatesAutoresizingMaskIntoConstraints = false
        card.addSubview(distanceLabel)
        
        // Delivery/Takeaway
        let deliveryLabel = UILabel()
        if restaurant.delivery {
            deliveryLabel.text = "Delivery"
            deliveryLabel.textColor = .systemGreen
        } else if restaurant.takeaway {
            deliveryLabel.text = "Takeaway"
            deliveryLabel.textColor = .systemBlue
        } else {
            deliveryLabel.text = ""
        }
        deliveryLabel.font = .systemFont(ofSize: 10)
        deliveryLabel.textAlignment = .right
        deliveryLabel.translatesAutoresizingMaskIntoConstraints = false
        card.addSubview(deliveryLabel)
        
        // Tap gesture
        let tapGesture = UITapGestureRecognizer(target: self, action: #selector(restaurantTapped(_:)))
        card.addGestureRecognizer(tapGesture)
        card.isUserInteractionEnabled = true
        
        // Constraints
        NSLayoutConstraint.activate([
            iconView.leadingAnchor.constraint(equalTo: card.leadingAnchor, constant: 16),
            iconView.centerYAnchor.constraint(equalTo: card.centerYAnchor),
            iconView.widthAnchor.constraint(equalToConstant: 50),
            iconView.heightAnchor.constraint(equalToConstant: 50),
            
            iconLabel.centerXAnchor.constraint(equalTo: iconView.centerXAnchor),
            iconLabel.centerYAnchor.constraint(equalTo: iconView.centerYAnchor),
            
            nameLabel.leadingAnchor.constraint(equalTo: iconView.trailingAnchor, constant: 12),
            nameLabel.topAnchor.constraint(equalTo: card.topAnchor, constant: 12),
            
            detailsLabel.leadingAnchor.constraint(equalTo: nameLabel.leadingAnchor),
            detailsLabel.topAnchor.constraint(equalTo: nameLabel.bottomAnchor, constant: 4),
            
            tagsStack.leadingAnchor.constraint(equalTo: nameLabel.leadingAnchor),
            tagsStack.topAnchor.constraint(equalTo: detailsLabel.bottomAnchor, constant: 8),
            tagsStack.bottomAnchor.constraint(equalTo: card.bottomAnchor, constant: -12),
            
            distanceLabel.trailingAnchor.constraint(equalTo: card.trailingAnchor, constant: -16),
            distanceLabel.topAnchor.constraint(equalTo: card.topAnchor, constant: 12),
            
            deliveryLabel.trailingAnchor.constraint(equalTo: card.trailingAnchor, constant: -16),
            deliveryLabel.topAnchor.constraint(equalTo: distanceLabel.bottomAnchor, constant: 4),
            
            card.heightAnchor.constraint(equalToConstant: 100)
        ])
        
        return card
    }
    
    private func tagColor(for tag: String) -> UIColor {
        switch tag.lowercased() {
        case "delivery": return .systemGreen
        case "takeaway": return .systemBlue
        case "wheelchair": return .systemPurple
        case "outdoor seating": return .systemTeal
        case "wifi": return .systemBlue
        default: return .systemGray
        }
    }
    
    // MARK: - Actions
    
    @objc private func distanceSliderChanged() {
        currentRadiusMiles = Int(distanceSlider.value)
        distanceValueLabel.text = "\(currentRadiusMiles) mi"
        
        // Update radius stat
        if let radiusCard = statsStackView.arrangedSubviews[1] as? UIView,
           let stack = radiusCard.subviews.first(where: { $0 is UIStackView }) as? UIStackView,
           let label = stack.arrangedSubviews.first as? UILabel {
            label.text = "\(currentRadiusMiles) mi"
        }
        persistDiscoveryPreferences()
    }
    
    @objc private func refreshTapped() {
        if locationService?.hasLocationPermission() == true {
            fetchUserLocationAndRestaurants()
        } else {
            locationService?.requestLocationPermission()
        }
    }
    
    @objc private func profileTapped() {
        let profileVC = ProfileViewController()
        present(profileVC, animated: true)
    }
    
    @objc private func restaurantTapped(_ gesture: UITapGestureRecognizer) {
        guard let card = gesture.view,
              let index = restaurantsStackView.arrangedSubviews.firstIndex(of: card),
              index < filteredRestaurants.count else { return }
        
        let restaurant = filteredRestaurants[index]
        showRestaurantDetails(restaurant)
    }
    
    private func showRestaurantDetails(_ restaurant: OverpassRestaurant) {
        var message = restaurant.name
        if let address = restaurant.address {
            message += "\n\(address)"
        }
        if let phone = restaurant.phone {
            message += "\n📞 \(phone)"
        }
        if let website = restaurant.website {
            message += "\n🌐 \(website)"
        }
        if let hours = restaurant.openingHours {
            message += "\n🕐 \(hours)"
        }
        
        let alert = UIAlertController(title: "Restaurant Details", message: message, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "OK", style: .default))
        present(alert, animated: true)
    }
    
    // MARK: - Helpers
    
    private func showLoading(_ show: Bool) {
        loadingContainer.isHidden = !show
        if show {
            loadingIndicator.startAnimating()
        } else {
            loadingIndicator.stopAnimating()
        }
    }
    
    private func updateStats() {
        // Update restaurants count
        if let restaurantsCard = statsStackView.arrangedSubviews.first,
           let stack = restaurantsCard.subviews.first(where: { $0 is UIStackView }) as? UIStackView,
           let label = stack.arrangedSubviews.first as? UILabel {
            label.text = "\(allRestaurants.count)"
        }
        
        // Update accuracy
        if let accuracyCard = statsStackView.arrangedSubviews.last,
           let stack = accuracyCard.subviews.first(where: { $0 is UIStackView }) as? UIStackView,
           let label = stack.arrangedSubviews.first as? UILabel {
            if let accuracy = currentLocation?.accuracy {
                label.text = String(format: "%.0f", accuracy)
            } else {
                label.text = "--"
            }
        }
    }
}

// MARK: - UISearchBarDelegate

extension RestaurantDiscoveryViewController: UISearchBarDelegate {
    func searchBar(_ searchBar: UISearchBar, textDidChange searchText: String) {
        searchQuery = searchText.trimmingCharacters(in: .whitespacesAndNewlines)
        filterAndDisplayRestaurants()
    }
    
    func searchBarSearchButtonClicked(_ searchBar: UISearchBar) {
        searchBar.resignFirstResponder()
    }
}
