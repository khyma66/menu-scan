"use client";

import { useState } from "react";
import ImageUpload from "@/components/ImageUpload";
import MenuDisplay from "@/components/MenuDisplay";
import StatusDisplay from "@/components/StatusDisplay";
import type { MenuItem } from "@/types/menu";

export default function Home() {
  const [menuItems, setMenuItems] = useState<MenuItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [processingTime, setProcessingTime] = useState<number | null>(null);

  const handleOCRComplete = (items: MenuItem[], time: number) => {
    setMenuItems(items);
    setProcessingTime(time);
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
    <main className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            Menu OCR
          </h1>
          <p className="text-xl text-gray-600">
            Extract menu items from images using AI-powered OCR
          </p>
        </div>

        {/* Main Content */}
        <div className="grid md:grid-cols-2 gap-8 max-w-6xl mx-auto">
          {/* Left Column - Upload */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">
              Upload Menu Image
            </h2>
            <ImageUpload
              onOCRComplete={handleOCRComplete}
              onError={handleError}
              onLoading={handleLoading}
            />
            <StatusDisplay
              loading={loading}
              error={error}
              processingTime={processingTime}
            />
          </div>

          {/* Right Column - Results */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">
              Extracted Menu Items
            </h2>
            <MenuDisplay items={menuItems} />
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-8 text-gray-600">
          <p>Powered by FastAPI & Next.js</p>
        </div>
      </div>
    </main>
  );
}
