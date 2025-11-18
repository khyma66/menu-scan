"use client";

import { useState, useEffect } from "react";
import { cuisineCategories, featuredRestaurants, getCurrentLocation } from "@/lib/restaurant-data";

interface Restaurant {
  id: string;
  name: string;
  cuisine: string;
  rating: number;
  deliveryTime: string;
  deliveryFee: string;
  image: string;
  tags: string[];
  distance: string;
}

export default function DeliveryAppHome() {
  const [location, setLocation] = useState<{lat: number, lng: number} | null>(null);
  const [restaurants, setRestaurants] = useState<Restaurant[]>(featuredRestaurants);
  const [selectedCuisine, setSelectedCuisine] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [showLocationPermission, setShowLocationPermission] = useState(false);

  useEffect(() => {
    checkLocationPermission();
  }, []);

  const checkLocationPermission = async () => {
    try {
      const coords = await getCurrentLocation();
      setLocation(coords);
      setShowLocationPermission(false);
    } catch (error) {
      setShowLocationPermission(true);
    }
  };

  const requestLocation = async () => {
    try {
      const coords = await getCurrentLocation();
      setLocation(coords);
      setShowLocationPermission(false);
    } catch (error) {
      console.error('Location access denied');
    }
  };

  const filteredRestaurants = restaurants.filter(restaurant => {
    const matchesCuisine = !selectedCuisine || restaurant.cuisine.toLowerCase() === selectedCuisine.toLowerCase();
    const matchesSearch = !searchQuery || 
      restaurant.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      restaurant.cuisine.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCuisine && matchesSearch;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-r from-orange-400 to-red-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">🍽️</span>
              </div>
              <h1 className="text-xl font-bold text-gray-900">FoodDelivery</h1>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={requestLocation}
                className="flex items-center space-x-1 text-gray-600 hover:text-gray-900 transition"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span className="text-sm font-medium">Near you</span>
              </button>
              <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                <span className="text-gray-600 text-sm">👤</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Location Permission Modal */}
      {showLocationPermission && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 m-4 max-w-sm w-full">
            <h3 className="text-lg font-semibold mb-2">Enable Location</h3>
            <p className="text-gray-600 mb-4 text-sm">
              Allow access to your location to find restaurants near you and get accurate delivery times.
            </p>
            <div className="flex space-x-3">
              <button
                onClick={() => setShowLocationPermission(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition"
              >
                Maybe Later
              </button>
              <button
                onClick={requestLocation}
                className="flex-1 px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition"
              >
                Enable
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Search Bar */}
        <div className="mb-6">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              type="text"
              placeholder="Search restaurants, cuisines, or dishes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="block w-full pl-10 pr-3 py-3 border border-gray-200 rounded-xl bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-xl p-4 text-center shadow-sm">
            <div className="text-2xl font-bold text-orange-500">50+</div>
            <div className="text-sm text-gray-600">Restaurants</div>
          </div>
          <div className="bg-white rounded-xl p-4 text-center shadow-sm">
            <div className="text-2xl font-bold text-green-500">15min</div>
            <div className="text-sm text-gray-600">Avg Delivery</div>
          </div>
          <div className="bg-white rounded-xl p-4 text-center shadow-sm">
            <div className="text-2xl font-bold text-blue-500">4.8★</div>
            <div className="text-sm text-gray-600">Avg Rating</div>
          </div>
        </div>

        {/* Cuisine Categories */}
        <div className="mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Browse by Cuisine</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
            {cuisineCategories.map((cuisine) => (
              <button
                key={cuisine.id}
                onClick={() => setSelectedCuisine(
                  selectedCuisine === cuisine.name ? null : cuisine.name
                )}
                className={`relative bg-gradient-to-br ${cuisine.color} rounded-xl p-4 text-white transition transform hover:scale-105 shadow-md ${
                  selectedCuisine === cuisine.name ? 'ring-2 ring-white ring-offset-2' : ''
                }`}
              >
                <div className="text-2xl mb-2">{cuisine.icon}</div>
                <div className="text-sm font-semibold">{cuisine.name}</div>
                <div className="text-xs opacity-90">{cuisine.restaurants} places</div>
              </button>
            ))}
          </div>
        </div>

        {/* Featured Restaurants */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">
              {selectedCuisine ? `${selectedCuisine} Restaurants` : 'Featured Restaurants'}
            </h2>
            <button 
              onClick={() => setSelectedCuisine(null)}
              className="text-orange-500 text-sm font-medium hover:text-orange-600 transition"
            >
              Clear Filter
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredRestaurants.map((restaurant) => (
              <div
                key={restaurant.id}
                className="bg-white rounded-xl shadow-sm hover:shadow-md transition overflow-hidden group cursor-pointer"
              >
                <div className="relative">
                  <div className="h-48 bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center">
                    <span className="text-4xl">🍽️</span>
                  </div>
                  <div className="absolute top-3 left-3">
                    <span className="bg-white bg-opacity-90 text-gray-800 px-2 py-1 rounded-full text-xs font-medium">
                      {restaurant.deliveryFee}
                    </span>
                  </div>
                  {restaurant.tags.includes('Popular') && (
                    <div className="absolute top-3 right-3">
                      <span className="bg-orange-500 text-white px-2 py-1 rounded-full text-xs font-medium">
                        Popular
                      </span>
                    </div>
                  )}
                </div>
                
                <div className="p-4">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-semibold text-gray-900 group-hover:text-orange-500 transition">
                      {restaurant.name}
                    </h3>
                    <div className="flex items-center space-x-1">
                      <span className="text-yellow-400">⭐</span>
                      <span className="text-sm font-medium text-gray-700">{restaurant.rating}</span>
                    </div>
                  </div>
                  
                  <p className="text-gray-600 text-sm mb-2">{restaurant.cuisine} • {restaurant.distance}</p>
                  
                  <div className="flex items-center justify-between text-sm text-gray-500">
                    <span>{restaurant.deliveryTime}</span>
                    <div className="flex items-center space-x-1">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span>{restaurant.deliveryTime}</span>
                    </div>
                  </div>
                  
                  <div className="mt-3 flex flex-wrap gap-1">
                    {restaurant.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="bg-gray-100 text-gray-600 px-2 py-1 rounded-full text-xs"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Popular Items Section */}
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Popular Dishes</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="border border-gray-200 rounded-lg p-4 hover:border-orange-300 transition cursor-pointer">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-gradient-to-br from-orange-400 to-red-500 rounded-lg flex items-center justify-center">
                  <span className="text-white text-xl">🍕</span>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Margherita Pizza</h3>
                  <p className="text-sm text-gray-600">From Mario's Pizzeria</p>
                  <p className="text-orange-500 font-medium">$12.99</p>
                </div>
              </div>
            </div>
            
            <div className="border border-gray-200 rounded-lg p-4 hover:border-orange-300 transition cursor-pointer">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-gradient-to-br from-green-400 to-teal-500 rounded-lg flex items-center justify-center">
                  <span className="text-white text-xl">🌮</span>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Chicken Tacos</h3>
                  <p className="text-sm text-gray-600">From El Corazón</p>
                  <p className="text-orange-500 font-medium">$9.99</p>
                </div>
              </div>
            </div>
            
            <div className="border border-gray-200 rounded-lg p-4 hover:border-orange-300 transition cursor-pointer">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-gradient-to-br from-purple-400 to-indigo-500 rounded-lg flex items-center justify-center">
                  <span className="text-white text-xl">🍣</span>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Salmon Sushi</h3>
                  <p className="text-sm text-gray-600">From Sakura Sushi</p>
                  <p className="text-orange-500 font-medium">$16.99</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}