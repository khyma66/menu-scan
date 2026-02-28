import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Search, MapPin, Navigation, RefreshCw, Star, Clock, ChevronRight,
  Utensils, Filter, Flame, Leaf, Fish, Coffee, Pizza, Award
} from "lucide-react";
import { ImageWithFallback } from "../components/figma/ImageWithFallback";
import { AnimatedFooditLogo } from "../components/AnimatedFooditLogo";

const CATEGORIES = [
  { id: "all", label: "All", icon: Utensils },
  { id: "trending", label: "Trending", icon: Flame },
  { id: "healthy", label: "Healthy", icon: Leaf },
  { id: "seafood", label: "Seafood", icon: Fish },
  { id: "cafe", label: "Café", icon: Coffee },
  { id: "pizza", label: "Pizza", icon: Pizza },
];

const RESTAURANTS = [
  {
    id: 1,
    name: "The Golden Plate",
    cuisine: "International • Fine Dining",
    rating: 4.8,
    reviews: 342,
    distance: "0.4 mi",
    time: "20–30 min",
    tags: ["Trending", "Award Winner"],
    image: "https://images.unsplash.com/photo-1712746784068-703c0c915611?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=400",
    open: true,
    healthScore: 92,
  },
  {
    id: 2,
    name: "Burgr Republic",
    cuisine: "American • Burgers",
    rating: 4.5,
    reviews: 218,
    distance: "0.9 mi",
    time: "15–25 min",
    tags: ["Popular"],
    image: "https://images.unsplash.com/photo-1632898658030-ead731d252d4?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=400",
    open: true,
    healthScore: 68,
  },
  {
    id: 3,
    name: "Sakura Sushi Bar",
    cuisine: "Japanese • Sushi",
    rating: 4.9,
    reviews: 511,
    distance: "1.2 mi",
    time: "25–35 min",
    tags: ["Healthy", "Top Rated"],
    image: "https://images.unsplash.com/photo-1717838207789-62684e75a770?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=400",
    open: true,
    healthScore: 88,
  },
  {
    id: 4,
    name: "Trattoria Bella",
    cuisine: "Italian • Pasta & Pizza",
    rating: 4.6,
    reviews: 389,
    distance: "1.8 mi",
    time: "30–40 min",
    tags: ["Family Friendly"],
    image: "https://images.unsplash.com/photo-1669131447025-548a65e91e24?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=400",
    open: false,
    healthScore: 74,
  },
  {
    id: 5,
    name: "Napoli Express",
    cuisine: "Italian • Wood-fire Pizza",
    rating: 4.4,
    reviews: 167,
    distance: "2.1 mi",
    time: "20–30 min",
    tags: ["Cozy"],
    image: "https://images.unsplash.com/photo-1770629681079-86c4d2adb83f?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=400",
    open: true,
    healthScore: 71,
  },
];

function HealthScoreBadge({ score }: { score: number }) {
  const color = score >= 85 ? "#22c55e" : score >= 70 ? "#f59e0b" : "#ef4444";
  return (
    <div className="flex items-center gap-1 px-2 py-0.5 rounded-full" style={{ backgroundColor: color + "20" }}>
      <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: color }} />
      <span className="text-xs font-semibold" style={{ color }}>{score}</span>
    </div>
  );
}

export function Discover() {
  const [search, setSearch] = useState("");
  const [activeCategory, setActiveCategory] = useState("all");
  const [distance, setDistance] = useState(10);
  const [refreshing, setRefreshing] = useState(false);
  const [favorites, setFavorites] = useState<number[]>([]);

  const handleRefresh = () => {
    setRefreshing(true);
    setTimeout(() => setRefreshing(false), 1500);
  };

  const toggleFavorite = (id: number) => {
    setFavorites(prev => prev.includes(id) ? prev.filter(f => f !== id) : [...prev, id]);
  };

  const filtered = RESTAURANTS.filter(r => {
    const matchSearch = r.name.toLowerCase().includes(search.toLowerCase()) ||
      r.cuisine.toLowerCase().includes(search.toLowerCase());
    const matchCategory = activeCategory === "all" || r.tags.some(t =>
      t.toLowerCase().includes(activeCategory.toLowerCase()));
    return matchSearch && matchCategory;
  });

  return (
    <div className="flex flex-col min-h-full bg-gray-50">
      {/* Hero Header */}
      <div
        className="relative px-5 pt-7 pb-5 overflow-hidden"
        style={{ backgroundColor: "#D05220" }}
      >
        {/* Decorative circles */}
        <div className="absolute -top-8 -right-8 w-32 h-32 rounded-full bg-white/10" />
        <div className="absolute top-4 -right-4 w-20 h-20 rounded-full bg-white/5" />
        <div className="absolute -bottom-6 -left-6 w-24 h-24 rounded-full bg-white/10" />

        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col items-center mb-4"
        >
          <AnimatedFooditLogo />
          <p className="text-white/85 text-sm mt-2">Snap • Understand • Choose Better</p>
        </motion.div>

        {/* Search */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="relative"
        >
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input
            type="text"
            placeholder="Search restaurants, cuisines..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-11 pr-4 py-3.5 bg-white/95 backdrop-blur rounded-2xl text-sm text-gray-700 outline-none shadow-lg placeholder:text-gray-400"
          />
          <button className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 bg-blue-600 rounded-xl">
            <Filter size={14} className="text-white" />
          </button>
        </motion.div>
      </div>

      {/* Stats Row */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="mx-4 -mt-4 bg-white rounded-2xl shadow-lg p-4 flex items-center justify-around"
      >
        {[
          { value: `${filtered.length}`, label: "Nearby", color: "#3B5BDB" },
          { value: `${distance} mi`, label: "Radius", color: "#0EA5E9" },
        ].map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 + i * 0.05 }}
            className="flex flex-col items-center gap-1"
          >
            <span className="font-bold text-lg" style={{ color: stat.color }}>{stat.value}</span>
            <span className="text-xs text-gray-500">{stat.label}</span>
          </motion.div>
        ))}
      </motion.div>

      {/* Distance Slider */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mx-4 mt-4 bg-white rounded-2xl p-4 shadow-sm"
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <MapPin size={16} className="text-red-500" />
            <span className="font-semibold text-sm text-gray-700">Distance</span>
          </div>
          <motion.span
            key={distance}
            initial={{ scale: 1.2, color: "#3B5BDB" }}
            animate={{ scale: 1, color: "#3B5BDB" }}
            className="font-bold text-sm"
            style={{ color: "#3B5BDB" }}
          >
            {distance} mi
          </motion.span>
        </div>
        <input
          type="range"
          min={1}
          max={20}
          value={distance}
          onChange={e => setDistance(Number(e.target.value))}
          className="w-full accent-blue-600"
        />
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>1 mi</span>
          <span>20 mi</span>
        </div>
      </motion.div>

      {/* Categories */}
      <div className="mt-4 px-4">
        <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
          {CATEGORIES.map((cat, i) => {
            const Icon = cat.icon;
            const active = activeCategory === cat.id;
            return (
              <motion.button
                key={cat.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 + i * 0.04 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setActiveCategory(cat.id)}
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-medium whitespace-nowrap transition-all flex-shrink-0"
                style={{
                  backgroundColor: active ? "#3B5BDB" : "white",
                  color: active ? "white" : "#6B7280",
                  boxShadow: active ? "0 4px 12px rgba(59,91,219,0.3)" : "0 1px 4px rgba(0,0,0,0.08)",
                }}
              >
                <Icon size={13} />
                {cat.label}
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* Nearby Restaurants Header */}
      <div className="flex items-center justify-between px-4 mt-5 mb-3">
        <div className="flex items-center gap-2">
          <span className="text-lg">🏪</span>
          <span className="font-bold text-gray-800">Nearby Restaurants</span>
        </div>
        <motion.button
          onClick={handleRefresh}
          whileTap={{ scale: 0.9 }}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-white rounded-xl shadow-sm border border-gray-100 text-xs font-medium text-gray-600"
        >
          <motion.div
            animate={refreshing ? { rotate: 360 } : {}}
            transition={{ duration: 0.8, repeat: refreshing ? Infinity : 0, ease: "linear" }}
          >
            <RefreshCw size={13} />
          </motion.div>
          REFRESH
        </motion.button>
      </div>

      {/* Restaurant Cards */}
      <div className="px-4 pb-4 space-y-3">
        <AnimatePresence mode="popLayout">
          {filtered.map((restaurant, i) => (
            <motion.div
              key={restaurant.id}
              layout
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ delay: i * 0.06 }}
              whileHover={{ y: -2 }}
              whileTap={{ scale: 0.98 }}
              className="bg-white rounded-2xl shadow-sm overflow-hidden cursor-pointer"
            >
              <div className="relative h-36">
                <ImageWithFallback
                  src={restaurant.image}
                  alt={restaurant.name}
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />

                {/* Favorite button */}
                <motion.button
                  whileTap={{ scale: 0.8 }}
                  onClick={(e) => { e.stopPropagation(); toggleFavorite(restaurant.id); }}
                  className="absolute top-3 right-3 w-8 h-8 bg-white/90 backdrop-blur rounded-full flex items-center justify-center shadow"
                >
                  <motion.span
                    animate={{ scale: favorites.includes(restaurant.id) ? [1, 1.4, 1] : 1 }}
                    transition={{ duration: 0.3 }}
                  >
                    {favorites.includes(restaurant.id) ? "❤️" : "🤍"}
                  </motion.span>
                </motion.button>

                {/* Open/Closed badge */}
                <div className="absolute top-3 left-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${restaurant.open ? "bg-green-500 text-white" : "bg-gray-500 text-white"}`}>
                    {restaurant.open ? "Open" : "Closed"}
                  </span>
                </div>

                {/* Tags */}
                <div className="absolute bottom-3 left-3 flex gap-1">
                  {restaurant.tags.map(tag => (
                    <span key={tag} className="text-xs px-2 py-0.5 bg-white/90 backdrop-blur rounded-full text-gray-700 font-medium">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>

              <div className="p-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-gray-900">{restaurant.name}</h3>
                      <HealthScoreBadge score={restaurant.healthScore} />
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5">{restaurant.cuisine}</p>
                  </div>
                  <ChevronRight size={18} className="text-gray-400 mt-1 flex-shrink-0" />
                </div>

                <div className="flex items-center gap-4 mt-2.5">
                  <div className="flex items-center gap-1">
                    <Star size={13} className="text-amber-400 fill-amber-400" />
                    <span className="text-xs font-semibold text-gray-700">{restaurant.rating}</span>
                    <span className="text-xs text-gray-400">({restaurant.reviews})</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Navigation size={12} className="text-blue-500" />
                    <span className="text-xs text-gray-600">{restaurant.distance}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock size={12} className="text-green-500" />
                    <span className="text-xs text-gray-600">{restaurant.time}</span>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {filtered.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-16"
          >
            <div className="text-5xl mb-3">🔍</div>
            <p className="text-gray-500">No restaurants found</p>
            <p className="text-gray-400 text-sm mt-1">Try adjusting your search</p>
          </motion.div>
        )}
      </div>
    </div>
  );
}