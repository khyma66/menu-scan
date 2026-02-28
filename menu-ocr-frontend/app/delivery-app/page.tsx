"use client";

import DeliveryAppHome from "@/components/DeliveryAppHome";
import ImageUpload from "@/components/ImageUpload";
import MenuDisplay from "@/components/MenuDisplay";
import { useState } from "react";
import { ocrApi } from "@/lib/api";
import type { MenuItem } from "@/types/menu";

export default function DeliveryAppPage() {
  const [activeTab, setActiveTab] = useState<"delivery" | "menu-ocr">("delivery");
  const [menuItems, setMenuItems] = useState<MenuItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleOCRComplete = async (items: MenuItem[], time: number, metadata?: any) => {
    setMenuItems(items);
    setError(null);
  };

  const handleError = (errorMessage: string) => {
    setError(errorMessage);
    setMenuItems([]);
  };

  const handleLoading = (isLoading: boolean) => {
    setLoading(isLoading);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Tab Navigation */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab("delivery")}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition ${activeTab === "delivery"
                  ? "border-orange-500 text-orange-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
            >
              🍽️ Restaurant Discovery
            </button>
            <button
              onClick={() => setActiveTab("menu-ocr")}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition ${activeTab === "menu-ocr"
                  ? "border-orange-500 text-orange-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
            >
              📱 Menu OCR
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto">
        {activeTab === "delivery" ? (
          <DeliveryAppHome />
        ) : (
          <div className="grid md:grid-cols-2 gap-8 max-w-6xl mx-auto p-6">
            {/* Left Column - Upload */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">
                Upload Menu Image
              </h2>

              <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-sm text-green-800">✅ Backend connected</p>
              </div>

              <ImageUpload
                onOCRComplete={handleOCRComplete}
                onError={handleError}
                onLoading={handleLoading}
              />

              {error && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              )}
            </div>

            {/* Right Column - Results */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">
                Extracted Menu Items
              </h2>
              <MenuDisplay items={menuItems} userTier="free" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}