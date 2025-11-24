// Cuisine banner data
export const cuisineCategories = [
  {
    id: 'italian',
    name: 'Italian',
    icon: '🍝',
    color: 'from-red-400 to-pink-500',
    image: '/api/placeholder/120/120',
    restaurants: 12
  },
  {
    id: 'chinese',
    name: 'Chinese',
    icon: '🥢',
    color: 'from-yellow-400 to-orange-500',
    image: '/api/placeholder/120/120',
    restaurants: 8
  },
  {
    id: 'mexican',
    name: 'Mexican',
    icon: '🌮',
    color: 'from-green-400 to-teal-500',
    image: '/api/placeholder/120/120',
    restaurants: 15
  },
  {
    id: 'japanese',
    name: 'Japanese',
    icon: '🍣',
    color: 'from-purple-400 to-indigo-500',
    image: '/api/placeholder/120/120',
    restaurants: 10
  },
  {
    id: 'indian',
    name: 'Indian',
    icon: '🍛',
    color: 'from-orange-400 to-red-500',
    image: '/api/placeholder/120/120',
    restaurants: 6
  },
  {
    id: 'american',
    name: 'American',
    icon: '🍔',
    color: 'from-blue-400 to-cyan-500',
    image: '/api/placeholder/120/120',
    restaurants: 20
  },
  {
    id: 'thai',
    name: 'Thai',
    icon: '🌶️',
    color: 'from-pink-400 to-rose-500',
    image: '/api/placeholder/120/120',
    restaurants: 7
  },
  {
    id: 'mediterranean',
    name: 'Mediterranean',
    icon: '🫒',
    color: 'from-emerald-400 to-green-500',
    image: '/api/placeholder/120/120',
    restaurants: 9
  }
];

// Featured restaurants data
export const featuredRestaurants = [
  {
    id: '1',
    name: 'Mario\'s Pizzeria',
    cuisine: 'Italian',
    rating: 4.8,
    deliveryTime: '25-35 min',
    deliveryFee: '$2.99',
    image: '/api/placeholder/300/200',
    tags: ['Popular', 'Fast Delivery'],
    distance: '0.8 miles'
  },
  {
    id: '2', 
    name: 'Golden Dragon',
    cuisine: 'Chinese',
    rating: 4.6,
    deliveryTime: '30-40 min',
    deliveryFee: '$1.99',
    image: '/api/placeholder/300/200',
    tags: ['Family Style', 'Large Portions'],
    distance: '1.2 miles'
  },
  {
    id: '3',
    name: 'El Corazón',
    cuisine: 'Mexican',
    rating: 4.9,
    deliveryTime: '20-30 min', 
    deliveryFee: '$3.49',
    image: '/api/placeholder/300/200',
    tags: ['Authentic', 'Spicy'],
    distance: '0.5 miles'
  },
  {
    id: '4',
    name: 'Sakura Sushi',
    cuisine: 'Japanese',
    rating: 4.7,
    deliveryTime: '35-45 min',
    deliveryFee: '$4.99',
    image: '/api/placeholder/300/200',
    tags: ['Fresh', 'Premium'],
    distance: '1.5 miles'
  }
];

// Location service utilities
export const getCurrentLocation = (): Promise<{lat: number, lng: number}> => {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation is not supported by this browser'));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          lat: position.coords.latitude,
          lng: position.coords.longitude
        });
      },
      (error) => {
        reject(error);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000
      }
    );
  });
};

// Mock nearby restaurants API
export const getNearbyRestaurants = async (location: {lat: number, lng: number}) => {
  // In a real app, this would call your Supabase backend
  return featuredRestaurants;
};

// Distance calculation
export const calculateDistance = (lat1: number, lng1: number, lat2: number, lng2: number): number => {
  const R = 3959; // Earth's radius in miles
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a = 
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
    Math.sin(dLng/2) * Math.sin(dLng/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
};