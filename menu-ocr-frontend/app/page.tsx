"use client";

import { useState, useEffect } from "react";
import ImageUpload from "@/components/ImageUpload";
import MenuDisplay from "@/components/MenuDisplay";
import StatusDisplay from "@/components/StatusDisplay";
import { ocrApi } from "@/lib/api";
import type { MenuItem } from "@/types/menu";

export default function Home() {
  const [menuItems, setMenuItems] = useState<MenuItem[]>([]);
  const [translatedItems, setTranslatedItems] = useState<MenuItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [processingTime, setProcessingTime] = useState<number | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<"checking" | "connected" | "disconnected">("checking");
  const [showTranslation, setShowTranslation] = useState(false);
  const [rawText, setRawText] = useState<string>("");

  // Check backend connection on mount
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
    
    // Store raw text for translation
    if (metadata?.raw_text) {
      console.log("Setting rawText:", metadata.raw_text.substring(0, 100));
      setRawText(metadata.raw_text);
    } else {
      console.log("No raw_text in metadata");
    }
    
    // Log translation info if available
    if (metadata?.translated) {
      console.log("Translation info:", {
        language: metadata.detected_language,
        translation_count: metadata.translation_count
      });
    }
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
            
            {/* Connection Status */}
            {connectionStatus === "checking" && (
              <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800">🟡 Checking backend connection...</p>
              </div>
            )}
            {connectionStatus === "disconnected" && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-800">
                  ⚠️ Backend not connected. Please start the backend server.
                </p>
              </div>
            )}
            {connectionStatus === "connected" && (
              <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-sm text-green-800">✅ Backend connected</p>
              </div>
            )}

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
            {showTranslation ? (
              <>
                <div className="mb-4">
                  <button
                    onClick={() => setShowTranslation(false)}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition mb-4"
                  >
                    ← Back to Original
                  </button>
                  <h3 className="text-xl font-semibold text-gray-800 mb-2">Translated Menu Items</h3>
                </div>
                <MenuDisplay
                  items={translatedItems}
                />
              </>
            ) : (
              <>
                {menuItems.length > 0 && rawText && (
                  <div className="mb-4">
                    <button
                      onClick={async () => {
                        alert("Button clicked! Starting translation...");
                        try {
                          const result = await ocrApi.translateOCR(rawText, "auto");
                          alert("Translation successful: " + JSON.stringify(result));
                          setTranslatedItems(result.menu_items);
                          setShowTranslation(true);
                        } catch (error: any) {
                          alert("Translation failed: " + error);
                        }
                      }}
                      disabled={loading}
                      className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg transition mb-4 mr-2"
                    >
                      {loading ? "Translating..." : "Translate to English"}
                    </button>
                  </div>
                )}
                <MenuDisplay
                  items={menuItems}
                />
              </>
            )}
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
