"use client";

import AttractiveHeader from "@/components/AttractiveHeader";
import DeliveryAppHome from "@/components/DeliveryAppHome";
import ImageUpload from "@/components/ImageUpload";
import MenuDisplay from "@/components/MenuDisplay";
import StatusDisplay from "@/components/StatusDisplay";
import UpgradeModal from "@/components/UpgradeModal";
import { useScanLimit } from "@/lib/useScanLimit";
import { useState, useEffect } from "react";
import { ocrApi } from "@/lib/api";
import type { MenuItem } from "@/types/menu";

export default function EnhancedFoodDeliveryApp() {
  const [activeTab, setActiveTab] = useState<"delivery" | "menu-ocr">("delivery");
  const [menuItems, setMenuItems] = useState<MenuItem[]>([]);
  const [translatedItems, setTranslatedItems] = useState<MenuItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [processingTime, setProcessingTime] = useState<number | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<"checking" | "connected" | "disconnected">("checking");
  const [showTranslation, setShowTranslation] = useState(false);
  const [rawText, setRawText] = useState<string>("");
  const [translating, setTranslating] = useState(false);

  const {
    scanCount,
    userTier,
    canScan,
    incrementScan,
    getRemainingScans,
    upgradeTier,
    showUpgradeModal,
    setShowUpgradeModal,
    promptUpgrade,
    FREE_SCAN_LIMIT,
  } = useScanLimit();

  // Check backend connection
  useEffect(() => {
    const checkConnection = async () => {
      try {
        await ocrApi.checkHealth();
        setConnectionStatus("connected");
      } catch (err) {
        setConnectionStatus("disconnected");
        setError("Backend server is not reachable. Please make sure it's running at http://localhost:8000");
      }
    };

    checkConnection();
    const interval = setInterval(checkConnection, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleOCRComplete = async (items: MenuItem[], time: number, metadata?: any) => {
    setMenuItems(items);
    setProcessingTime(time);
    setError(null);
    incrementScan();

    if (metadata?.raw_text) {
      setRawText(metadata.raw_text);
    }
  };

  const handleError = (errorMessage: string) => {
    setError(errorMessage);
    setMenuItems([]);
  };

  const handleLoading = (isLoading: boolean) => {
    setLoading(isLoading);
  };

  const handleBeforeUpload = (): boolean => {
    if (!canScan()) {
      promptUpgrade();
      return false;
    }
    return true;
  };

  const handleTranslateAll = async () => {
    if (!rawText || translating) return;
    setTranslating(true);
    try {
      const result = await ocrApi.translateOCR(rawText, "auto");
      setTranslatedItems(result.menu_items);
      setShowTranslation(true);
    } catch (error: any) {
      console.error("Translation failed:", error);
    } finally {
      setTranslating(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <AttractiveHeader />

      {/* Tab Navigation */}
      <div className="bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab("delivery")}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition relative ${activeTab === "delivery"
                  ? "border-orange-500 text-orange-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
            >
              🍽️ Restaurant Discovery
              {activeTab === "delivery" && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-orange-500 to-red-500"></div>
              )}
            </button>
            <button
              onClick={() => setActiveTab("menu-ocr")}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition relative ${activeTab === "menu-ocr"
                  ? "border-orange-500 text-orange-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
            >
              📱 Menu OCR
              {activeTab === "menu-ocr" && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-orange-500 to-red-500"></div>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto">
        {activeTab === "delivery" ? (
          <div className="p-6 space-y-6">
            <DeliveryAppHome />

            {/* Popular Categories */}
            <div className="bg-white rounded-2xl p-6 shadow-sm">
              <h2 className="text-xl font-bold text-gray-900 mb-4">🔥 Popular This Week</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gradient-to-br from-red-400 to-pink-500 rounded-xl p-4 text-white cursor-pointer hover:shadow-lg transition transform hover:scale-105">
                  <div className="text-2xl mb-2">🍕</div>
                  <h3 className="font-semibold text-sm">Pizza</h3>
                  <p className="text-xs opacity-90">1,234 orders</p>
                </div>
                <div className="bg-gradient-to-br from-green-400 to-teal-500 rounded-xl p-4 text-white cursor-pointer hover:shadow-lg transition transform hover:scale-105">
                  <div className="text-2xl mb-2">🌮</div>
                  <h3 className="font-semibold text-sm">Mexican</h3>
                  <p className="text-xs opacity-90">856 orders</p>
                </div>
                <div className="bg-gradient-to-br from-blue-400 to-indigo-500 rounded-xl p-4 text-white cursor-pointer hover:shadow-lg transition transform hover:scale-105">
                  <div className="text-2xl mb-2">🍔</div>
                  <h3 className="font-semibold text-sm">Burgers</h3>
                  <p className="text-xs opacity-90">1,102 orders</p>
                </div>
                <div className="bg-gradient-to-br from-purple-400 to-pink-500 rounded-xl p-4 text-white cursor-pointer hover:shadow-lg transition transform hover:scale-105">
                  <div className="text-2xl mb-2">🍣</div>
                  <h3 className="font-semibold text-sm">Japanese</h3>
                  <p className="text-xs opacity-90">623 orders</p>
                </div>
              </div>
            </div>

            {/* Trending */}
            <div className="bg-white rounded-2xl p-6 shadow-sm">
              <h2 className="text-xl font-bold text-gray-900 mb-4">🔥 Trending Now</h2>
              <div className="space-y-4">
                <div className="flex items-center space-x-4 p-3 hover:bg-gray-50 rounded-lg transition cursor-pointer">
                  <div className="w-16 h-16 bg-gradient-to-br from-orange-400 to-red-500 rounded-xl flex items-center justify-center">
                    <span className="text-white text-xl">🍕</span>
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">Tony&apos;s Pizzeria</h3>
                    <p className="text-sm text-gray-600">Italian • 0.8 miles • 4.8★</p>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">Free delivery</span>
                      <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">Fast delivery</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">25-35 min</p>
                    <p className="text-sm font-medium text-green-600">$2.99 delivery</p>
                  </div>
                </div>
                <div className="flex items-center space-x-4 p-3 hover:bg-gray-50 rounded-lg transition cursor-pointer">
                  <div className="w-16 h-16 bg-gradient-to-br from-green-400 to-teal-500 rounded-xl flex items-center justify-center">
                    <span className="text-white text-xl">🌮</span>
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">El Corazón Mexican</h3>
                    <p className="text-sm text-gray-600">Mexican • 1.2 miles • 4.9★</p>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className="bg-orange-100 text-orange-800 text-xs px-2 py-1 rounded-full">Popular</span>
                      <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded-full">Spicy</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">20-30 min</p>
                    <p className="text-sm font-medium text-green-600">$3.49 delivery</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="p-6">
            <div className="text-center mb-8">
              <h1 className="text-5xl font-bold text-gray-900 mb-4">Menu OCR</h1>
              <p className="text-xl text-gray-600">
                Extract menu items from images using AI-powered OCR
              </p>
              <div className="mt-4 flex items-center justify-center gap-3 flex-wrap">
                <div className="inline-flex items-center space-x-2 bg-gradient-to-r from-orange-100 to-red-100 px-4 py-2 rounded-full">
                  <span className="text-orange-600">🤖</span>
                  <span className="text-sm font-medium text-orange-700">Powered by AI & Ollama</span>
                </div>
                {/* Tier Badge */}
                <div className={`inline-flex items-center space-x-2 px-4 py-2 rounded-full ${userTier === "max"
                    ? "bg-gradient-to-r from-purple-100 to-indigo-100"
                    : userTier === "pro"
                      ? "bg-gradient-to-r from-blue-100 to-cyan-100"
                      : "bg-gray-100"
                  }`}>
                  <span>{userTier === "max" ? "👑" : userTier === "pro" ? "⚡" : "🆓"}</span>
                  <span className={`text-sm font-medium ${userTier === "max"
                      ? "text-purple-700"
                      : userTier === "pro"
                        ? "text-blue-700"
                        : "text-gray-700"
                    }`}>
                    {userTier.toUpperCase()} Plan
                    {userTier === "free" && ` • ${getRemainingScans()} scans left`}
                  </span>
                </div>
                {userTier === "free" && (
                  <button
                    onClick={promptUpgrade}
                    className="text-sm font-medium text-purple-600 hover:text-purple-800 underline transition"
                  >
                    Upgrade
                  </button>
                )}
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-8 max-w-6xl mx-auto">
              {/* Left Column - Upload */}
              <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl flex items-center justify-center">
                    <span className="text-white">📸</span>
                  </div>
                  <h2 className="text-2xl font-semibold text-gray-800">Upload Menu Image</h2>
                </div>

                {connectionStatus === "checking" && (
                  <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <p className="text-sm text-yellow-800 flex items-center">
                      <span className="animate-pulse mr-2">⏳</span>
                      Checking backend connection...
                    </p>
                  </div>
                )}
                {connectionStatus === "disconnected" && (
                  <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-sm text-red-800 flex items-center">
                      <span className="mr-2">⚠️</span>
                      Backend not connected. Please start the backend server.
                    </p>
                  </div>
                )}
                {connectionStatus === "connected" && (
                  <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                    <p className="text-sm text-green-800 flex items-center">
                      <span className="mr-2">✅</span>
                      Backend connected - Ready to process
                    </p>
                  </div>
                )}

                <ImageUpload
                  onOCRComplete={handleOCRComplete}
                  onError={handleError}
                  onLoading={handleLoading}
                  onBeforeUpload={handleBeforeUpload}
                />
                <StatusDisplay
                  loading={loading}
                  error={error}
                  processingTime={processingTime}
                />
              </div>

              {/* Right Column - Results */}
              <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-teal-500 rounded-xl flex items-center justify-center">
                    <span className="text-white">📋</span>
                  </div>
                  <h2 className="text-2xl font-semibold text-gray-800">Extracted Menu Items</h2>
                </div>

                {showTranslation ? (
                  <>
                    <div className="mb-4">
                      <button
                        onClick={() => setShowTranslation(false)}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition mb-4 flex items-center space-x-2"
                      >
                        <span>←</span>
                        <span>Back to Original</span>
                      </button>
                      <h3 className="text-xl font-semibold text-gray-800 mb-2">Translated Menu Items</h3>
                      <div className="inline-flex items-center space-x-2 bg-green-100 px-3 py-1 rounded-full">
                        <span className="text-green-600">🌍</span>
                        <span className="text-sm font-medium text-green-700">Auto-translated to English (all fields)</span>
                      </div>
                    </div>
                    <MenuDisplay items={translatedItems} userTier={userTier} />
                  </>
                ) : (
                  <>
                    {menuItems.length > 0 && rawText && (
                      <div className="mb-4">
                        <button
                          onClick={handleTranslateAll}
                          disabled={translating}
                          className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg transition mb-4 mr-2 flex items-center space-x-2"
                        >
                          <span>🌍</span>
                          <span>{translating ? "Translating all fields..." : "Translate All"}</span>
                        </button>
                      </div>
                    )}
                    <MenuDisplay items={menuItems} userTier={userTier} />
                  </>
                )}
              </div>
            </div>

            {/* Footer */}
            <div className="text-center mt-8 text-gray-600">
              <p className="flex items-center justify-center space-x-2">
                <span>Powered by</span>
                <span className="font-semibold">FastAPI & Next.js</span>
                <span>with</span>
                <span className="font-semibold text-orange-600">AI-Enhanced Dish Analysis</span>
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Upgrade Modal */}
      <UpgradeModal
        isOpen={showUpgradeModal}
        onClose={() => setShowUpgradeModal(false)}
        onUpgrade={upgradeTier}
        scanCount={scanCount}
        freeLimit={FREE_SCAN_LIMIT}
      />
    </div>
  );
}