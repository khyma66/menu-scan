//
//  RestaurantDiscoveryViewController.swift
//  MenuOCR
//
//  Created by MenuOCR on 2025-01-07.
//

import UIKit

class RestaurantDiscoveryViewController: UIViewController {

    private let scrollView = UIScrollView()
    private let contentView = UIView()

    // Header
    private let headerView = UIView()
    private let titleLabel = UILabel()
    private let subtitleLabel = UILabel()
    private let profileButton = UIButton()

    // Search bar
    private let searchBar = UISearchBar()

    // Stats cards
    private let statsStackView = UIStackView()

    // Restaurants
    private let restaurantsStackView = UIStackView()

    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
        setupConstraints()
        loadSampleData()
    }

    private func setupUI() {
        view.backgroundColor = UIColor.systemGray6

        // Header
        headerView.backgroundColor = UIColor(red: 1.0, green: 0.3, blue: 0.22, alpha: 1.0) // DoorDash orange
        headerView.layer.shadowColor = UIColor.black.cgColor
        headerView.layer.shadowOffset = CGSize(width: 0, height: 2)
        headerView.layer.shadowOpacity = 0.1
        headerView.layer.shadowRadius = 4

        titleLabel.text = "🍽️ FoodDelivery"
        titleLabel.font = UIFont.boldSystemFont(ofSize: 18)
        titleLabel.textColor = .white

        subtitleLabel.text = "DoorDash-like Restaurant Discovery"
        subtitleLabel.font = UIFont.systemFont(ofSize: 12)
        subtitleLabel.textColor = .white

        profileButton.setImage(UIImage(systemName: "person.circle"), for: .normal)
        profileButton.tintColor = .white

        // Search bar
        searchBar.placeholder = "Search restaurants, cuisines, or dishes..."
        searchBar.backgroundImage = UIImage()
        searchBar.searchBarStyle = .minimal

        // Stats
        statsStackView.axis = .horizontal
        statsStackView.distribution = .fillEqually
        statsStackView.spacing = 8

        // Restaurants
        restaurantsStackView.axis = .vertical
        restaurantsStackView.spacing = 12

        // Scroll view setup
        scrollView.translatesAutoresizingMaskIntoConstraints = false
        contentView.translatesAutoresizingMaskIntoConstraints = false

        view.addSubview(scrollView)
        scrollView.addSubview(contentView)

        // Add header elements
        headerView.addSubview(titleLabel)
        headerView.addSubview(subtitleLabel)
        headerView.addSubview(profileButton)

        // Add content elements
        contentView.addSubview(headerView)
        contentView.addSubview(searchBar)
        contentView.addSubview(statsStackView)
        contentView.addSubview(restaurantsStackView)
    }

    private func setupConstraints() {
        // Scroll view constraints
        NSLayoutConstraint.activate([
            scrollView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            scrollView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            scrollView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            scrollView.bottomAnchor.constraint(equalTo: view.bottomAnchor),

            contentView.topAnchor.constraint(equalTo: scrollView.topAnchor),
            contentView.leadingAnchor.constraint(equalTo: scrollView.leadingAnchor),
            contentView.trailingAnchor.constraint(equalTo: scrollView.trailingAnchor),
            contentView.bottomAnchor.constraint(equalTo: scrollView.bottomAnchor),
            contentView.widthAnchor.constraint(equalTo: scrollView.widthAnchor)
        ])

        // Header constraints
        headerView.translatesAutoresizingMaskIntoConstraints = false
        titleLabel.translatesAutoresizingMaskIntoConstraints = false
        subtitleLabel.translatesAutoresizingMaskIntoConstraints = false
        profileButton.translatesAutoresizingMaskIntoConstraints = false

        NSLayoutConstraint.activate([
            headerView.topAnchor.constraint(equalTo: contentView.topAnchor),
            headerView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor),
            headerView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor),
            headerView.heightAnchor.constraint(equalToConstant: 80),

            titleLabel.leadingAnchor.constraint(equalTo: headerView.leadingAnchor, constant: 16),
            titleLabel.centerYAnchor.constraint(equalTo: headerView.centerYAnchor, constant: -8),

            subtitleLabel.leadingAnchor.constraint(equalTo: titleLabel.leadingAnchor),
            subtitleLabel.topAnchor.constraint(equalTo: titleLabel.bottomAnchor, constant: 2),

            profileButton.trailingAnchor.constraint(equalTo: headerView.trailingAnchor, constant: -16),
            profileButton.centerYAnchor.constraint(equalTo: headerView.centerYAnchor),
            profileButton.widthAnchor.constraint(equalToConstant: 32),
            profileButton.heightAnchor.constraint(equalToConstant: 32)
        ])

        // Search bar constraints
        searchBar.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            searchBar.topAnchor.constraint(equalTo: headerView.bottomAnchor, constant: 16),
            searchBar.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            searchBar.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16)
        ])

        // Stats constraints
        statsStackView.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            statsStackView.topAnchor.constraint(equalTo: searchBar.bottomAnchor, constant: 16),
            statsStackView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            statsStackView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16)
        ])

        // Restaurants constraints
        restaurantsStackView.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            restaurantsStackView.topAnchor.constraint(equalTo: statsStackView.bottomAnchor, constant: 24),
            restaurantsStackView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            restaurantsStackView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            restaurantsStackView.bottomAnchor.constraint(equalTo: contentView.bottomAnchor, constant: -16)
        ])
    }

    private func loadSampleData() {
        // Create stats cards
        let restaurantsCard = createStatsCard(title: "50+", subtitle: "Restaurants", color: UIColor(red: 1.0, green: 0.3, blue: 0.22, alpha: 1.0))
        let deliveryCard = createStatsCard(title: "15min", subtitle: "Avg Delivery", color: UIColor.systemGreen)
        let ratingCard = createStatsCard(title: "4.8★", subtitle: "Avg Rating", color: UIColor.systemBlue)

        statsStackView.addArrangedSubview(restaurantsCard)
        statsStackView.addArrangedSubview(deliveryCard)
        statsStackView.addArrangedSubview(ratingCard)

        // Create restaurant cards
        let tonyCard = createRestaurantCard(
            name: "Tony's Pizzeria",
            details: "Italian • 0.8 miles • 4.8★",
            tags: ["Free delivery", "Fast delivery"],
            deliveryTime: "25-35 min",
            deliveryFee: "$2.99 delivery"
        )

        let corazonCard = createRestaurantCard(
            name: "El Corazón Mexican",
            details: "Mexican • 1.2 miles • 4.9★",
            tags: ["Popular", "Spicy"],
            deliveryTime: "20-30 min",
            deliveryFee: "$3.49 delivery"
        )

        restaurantsStackView.addArrangedSubview(tonyCard)
        restaurantsStackView.addArrangedSubview(corazonCard)
    }

    private func createStatsCard(title: String, subtitle: String, color: UIColor) -> UIView {
        let card = UIView()
        card.backgroundColor = .white
        card.layer.cornerRadius = 8
        card.layer.shadowColor = UIColor.black.cgColor
        card.layer.shadowOffset = CGSize(width: 0, height: 1)
        card.layer.shadowOpacity = 0.1
        card.layer.shadowRadius = 2

        let titleLabel = UILabel()
        titleLabel.text = title
        titleLabel.font = UIFont.boldSystemFont(ofSize: 20)
        titleLabel.textColor = color
        titleLabel.textAlignment = .center

        let subtitleLabel = UILabel()
        subtitleLabel.text = subtitle
        subtitleLabel.font = UIFont.systemFont(ofSize: 12)
        subtitleLabel.textColor = .gray
        subtitleLabel.textAlignment = .center

        let stack = UIStackView(arrangedSubviews: [titleLabel, subtitleLabel])
        stack.axis = .vertical
        stack.spacing = 4
        stack.alignment = .center

        card.addSubview(stack)
        stack.translatesAutoresizingMaskIntoConstraints = false

        NSLayoutConstraint.activate([
            stack.centerXAnchor.constraint(equalTo: card.centerXAnchor),
            stack.centerYAnchor.constraint(equalTo: card.centerYAnchor),
            card.heightAnchor.constraint(equalToConstant: 80)
        ])

        return card
    }

    private func createRestaurantCard(name: String, details: String, tags: [String], deliveryTime: String, deliveryFee: String) -> UIView {
        let card = UIView()
        card.backgroundColor = .white
        card.layer.cornerRadius = 12
        card.layer.shadowColor = UIColor.black.cgColor
        card.layer.shadowOffset = CGSize(width: 0, height: 2)
        card.layer.shadowOpacity = 0.1
        card.layer.shadowRadius = 4

        // Icon
        let iconView = UIView()
        iconView.backgroundColor = UIColor.systemOrange
        iconView.layer.cornerRadius = 25

        let iconLabel = UILabel()
        iconLabel.text = "🍽️"
        iconLabel.font = UIFont.systemFont(ofSize: 20)
        iconView.addSubview(iconLabel)

        // Content
        let nameLabel = UILabel()
        nameLabel.text = name
        nameLabel.font = UIFont.boldSystemFont(ofSize: 16)
        nameLabel.textColor = .black

        let detailsLabel = UILabel()
        detailsLabel.text = details
        detailsLabel.font = UIFont.systemFont(ofSize: 12)
        detailsLabel.textColor = .gray

        // Tags
        let tagsStack = UIStackView()
        tagsStack.axis = .horizontal
        tagsStack.spacing = 8

        for tag in tags {
            let tagLabel = UILabel()
            tagLabel.text = tag
            tagLabel.font = UIFont.systemFont(ofSize: 10)
            tagLabel.textColor = .white
            tagLabel.backgroundColor = UIColor.systemGreen
            tagLabel.layer.cornerRadius = 4
            tagLabel.clipsToBounds = true
            tagLabel.textAlignment = .center
            tagLabel.widthAnchor.constraint(equalToConstant: 80).isActive = true
            tagLabel.heightAnchor.constraint(equalToConstant: 16).isActive = true
            tagsStack.addArrangedSubview(tagLabel)
        }

        // Delivery info
        let timeLabel = UILabel()
        timeLabel.text = deliveryTime
        timeLabel.font = UIFont.systemFont(ofSize: 12)
        timeLabel.textColor = .gray

        let feeLabel = UILabel()
        feeLabel.text = deliveryFee
        feeLabel.font = UIFont.boldSystemFont(ofSize: 12)
        feeLabel.textColor = .systemGreen

        // Layout
        let leftStack = UIStackView(arrangedSubviews: [nameLabel, detailsLabel, tagsStack])
        leftStack.axis = .vertical
        leftStack.spacing = 4
        leftStack.alignment = .leading

        let rightStack = UIStackView(arrangedSubviews: [timeLabel, feeLabel])
        rightStack.axis = .vertical
        rightStack.spacing = 4
        rightStack.alignment = .trailing

        let mainStack = UIStackView(arrangedSubviews: [iconView, leftStack, rightStack])
        mainStack.axis = .horizontal
        mainStack.spacing = 12
        mainStack.alignment = .center

        card.addSubview(mainStack)

        // Constraints
        iconView.translatesAutoresizingMaskIntoConstraints = false
        mainStack.translatesAutoresizingMaskIntoConstraints = false
        iconLabel.translatesAutoresizingMaskIntoConstraints = false

        NSLayoutConstraint.activate([
            iconView.widthAnchor.constraint(equalToConstant: 50),
            iconView.heightAnchor.constraint(equalToConstant: 50),

            iconLabel.centerXAnchor.constraint(equalTo: iconView.centerXAnchor),
            iconLabel.centerYAnchor.constraint(equalTo: iconView.centerYAnchor),

            mainStack.topAnchor.constraint(equalTo: card.topAnchor, constant: 16),
            mainStack.leadingAnchor.constraint(equalTo: card.leadingAnchor, constant: 16),
            mainStack.trailingAnchor.constraint(equalTo: card.trailingAnchor, constant: -16),
            mainStack.bottomAnchor.constraint(equalTo: card.bottomAnchor, constant: -16),

            card.heightAnchor.constraint(equalToConstant: 100)
        ])

        return card
    }
}