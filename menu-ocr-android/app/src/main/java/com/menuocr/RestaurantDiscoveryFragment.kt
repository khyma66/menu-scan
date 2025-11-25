package com.menuocr

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import androidx.cardview.widget.CardView
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment

data class Restaurant(
    val name: String,
    val cuisine: String,
    val distance: Double,
    val rating: Double,
    val deliveryTime: String,
    val deliveryFee: Double,
    val tags: List<String>
)

class RestaurantDiscoveryFragment : Fragment() {

    private lateinit var cuisineContainer: LinearLayout
    private lateinit var restaurantsContainer: LinearLayout
    private var selectedCuisine: String? = null

    private val allRestaurants = listOf(
        Restaurant("Tony's Pizzeria", "Italian", 0.8, 4.8, "25-35 min", 2.99, listOf("Free delivery", "Fast delivery")),
        Restaurant("El Corazón Mexican", "Mexican", 1.2, 4.9, "20-30 min", 3.49, listOf("Popular", "Spicy")),
        Restaurant("Spice Route Indian", "Indian", 0.5, 4.7, "30-40 min", 4.99, listOf("Authentic", "Vegetarian")),
        Restaurant("Sakura Japanese", "Japanese", 2.1, 4.6, "35-45 min", 3.99, listOf("Sushi", "Fresh")),
        Restaurant("Golden Dragon Chinese", "Chinese", 1.8, 4.5, "25-35 min", 2.49, listOf("Fast delivery", "Popular")),
        Restaurant("Mediterranean Breeze", "Mediterranean", 0.9, 4.8, "20-30 min", 3.99, listOf("Healthy", "Fresh")),
        Restaurant("Burger Haven", "American", 1.5, 4.4, "15-25 min", 1.99, listOf("Quick", "Burgers")),
        Restaurant("Taco Fiesta", "Mexican", 0.7, 4.7, "15-25 min", 2.49, listOf("Authentic", "Fresh")),
        Restaurant("Curry Palace", "Indian", 1.3, 4.9, "40-50 min", 5.99, listOf("Premium", "Spicy")),
        Restaurant("Pasta Bella", "Italian", 2.0, 4.6, "30-40 min", 3.49, listOf("Fresh pasta", "Traditional"))
    )

    private val cuisines = listOf(
        "All", "Italian", "Mexican", "Indian", "Japanese", "Chinese", "Mediterranean", "American"
    )

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_restaurant_discovery, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        cuisineContainer = view.findViewById(R.id.cuisine_categories)
        restaurantsContainer = view.findViewById(R.id.restaurants_container)

        setupCuisineButtons()
        displayRestaurants(allRestaurants)
    }

    private fun setupCuisineButtons() {
        cuisineContainer.removeAllViews()

        cuisines.forEach { cuisine ->
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
            button.setBackgroundColor(ContextCompat.getColor(requireContext(), R.color.orange_500))
        }

        return button
    }

    private fun selectCuisine(cuisine: String) {
        selectedCuisine = if (cuisine == "All") null else cuisine

        // Update button states
        for (i in 0 until cuisineContainer.childCount) {
            val button = cuisineContainer.getChildAt(i) as Button
            val buttonCuisine = cuisines[i]

            if (buttonCuisine == cuisine) {
                button.setTextColor(ContextCompat.getColor(requireContext(), R.color.white))
                button.setBackgroundColor(ContextCompat.getColor(requireContext(), R.color.orange_500))
            } else {
                button.setTextColor(ContextCompat.getColor(requireContext(), R.color.gray_700))
                button.setBackgroundResource(R.drawable.cuisine_button_background)
            }
        }

        // Filter and display restaurants
        val filteredRestaurants = if (selectedCuisine == null) {
            allRestaurants
        } else {
            allRestaurants.filter { it.cuisine == selectedCuisine }
        }.sortedBy { it.distance }

        displayRestaurants(filteredRestaurants)
    }

    private fun displayRestaurants(restaurants: List<Restaurant>) {
        restaurantsContainer.removeAllViews()

        restaurants.forEach { restaurant ->
            val card = createRestaurantCard(restaurant)
            restaurantsContainer.addView(card)
        }
    }

    private fun createRestaurantCard(restaurant: Restaurant): CardView {
        val card = CardView(requireContext()).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                bottomMargin = 12
            }
            radius = 12f
            cardElevation = 4f
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

        val detailsText = TextView(requireContext()).apply {
            text = "${restaurant.cuisine} • ${restaurant.distance} miles • ${restaurant.rating}★"
            textSize = 12f
            setTextColor(ContextCompat.getColor(requireContext(), R.color.gray_600))
        }

        // Tags
        val tagsLayout = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(0, 4, 0, 0)
        }

        restaurant.tags.take(2).forEach { tag ->
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

        // Delivery info
        val deliveryLayout = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                gravity = android.view.Gravity.CENTER_VERTICAL
            }
        }

        val timeText = TextView(requireContext()).apply {
            text = restaurant.deliveryTime
            textSize = 12f
            setTextColor(ContextCompat.getColor(requireContext(), R.color.gray_600))
        }

        val feeText = TextView(requireContext()).apply {
            text = "$${String.format("%.2f", restaurant.deliveryFee)} delivery"
            textSize = 12f
            setTypeface(null, android.graphics.Typeface.BOLD)
            setTextColor(ContextCompat.getColor(requireContext(), R.color.green_600))
        }

        deliveryLayout.addView(timeText)
        deliveryLayout.addView(feeText)

        cardLayout.addView(iconView)
        cardLayout.addView(contentLayout)
        cardLayout.addView(deliveryLayout)

        card.addView(cardLayout)
        return card
    }

    private fun getCuisineIconBackground(cuisine: String): Int {
        return when (cuisine.lowercase()) {
            "italian" -> R.drawable.pizza_icon_background
            "mexican" -> R.drawable.mexican_icon_background
            else -> R.drawable.pizza_icon_background
        }
    }

    private fun getTagTextColor(tag: String): Int {
        return when (tag.lowercase()) {
            "free delivery" -> ContextCompat.getColor(requireContext(), R.color.green_700)
            "fast delivery" -> ContextCompat.getColor(requireContext(), R.color.blue_700)
            "popular" -> ContextCompat.getColor(requireContext(), R.color.orange_700)
            "spicy" -> ContextCompat.getColor(requireContext(), R.color.red_700)
            "authentic" -> ContextCompat.getColor(requireContext(), R.color.purple_700)
            "vegetarian" -> ContextCompat.getColor(requireContext(), R.color.green_700)
            "sushi" -> ContextCompat.getColor(requireContext(), R.color.blue_700)
            "fresh" -> ContextCompat.getColor(requireContext(), R.color.teal_700)
            "healthy" -> ContextCompat.getColor(requireContext(), R.color.green_700)
            "quick" -> ContextCompat.getColor(requireContext(), R.color.orange_700)
            "burgers" -> ContextCompat.getColor(requireContext(), R.color.red_700)
            "premium" -> ContextCompat.getColor(requireContext(), R.color.purple_700)
            "fresh pasta" -> ContextCompat.getColor(requireContext(), R.color.blue_700)
            "traditional" -> ContextCompat.getColor(requireContext(), R.color.brown_700)
            else -> ContextCompat.getColor(requireContext(), R.color.gray_700)
        }
    }

    private fun getTagBackground(tag: String): Int {
        return when (tag.lowercase()) {
            "free delivery" -> R.drawable.tag_background_green
            "fast delivery" -> R.drawable.tag_background_blue
            "popular" -> R.drawable.tag_background_orange
            "spicy" -> R.drawable.tag_background_red
            "authentic" -> R.drawable.tag_background_purple
            "vegetarian" -> R.drawable.tag_background_green
            "sushi" -> R.drawable.tag_background_blue
            "fresh" -> R.drawable.tag_background_teal
            "healthy" -> R.drawable.tag_background_green
            "quick" -> R.drawable.tag_background_orange
            "burgers" -> R.drawable.tag_background_red
            "premium" -> R.drawable.tag_background_purple
            "fresh pasta" -> R.drawable.tag_background_blue
            "traditional" -> R.drawable.tag_background_brown
            else -> R.drawable.tag_background_gray
        }
    }
}