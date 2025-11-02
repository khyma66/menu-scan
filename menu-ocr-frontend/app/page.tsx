"use client";

import { useState, useEffect } from "react";
import ImageUpload from "@/components/ImageUpload";
import MenuDisplay from "@/components/MenuDisplay";
import StatusDisplay from "@/components/StatusDisplay";
import AuthForm from "@/components/AuthForm";
import HealthConditionForm from "@/components/HealthConditionForm";
import { ocrApi } from "@/lib/api";
import { supabase } from "@/lib/supabase";
import type { MenuItem } from "@/types/menu";

export default function Home() {
  const [menuItems, setMenuItems] = useState<MenuItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [processingTime, setProcessingTime] = useState<number | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<"checking" | "connected" | "disconnected">("checking");
  
  // Auth state
  const [user, setUser] = useState<any>(null);
  const [showAuth, setShowAuth] = useState(false);
  const [showHealthForm, setShowHealthForm] = useState(false);
  const [healthConditions, setHealthConditions] = useState<any[]>([]);

  // Check auth state
  useEffect(() => {
    const checkUser = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      setUser(session?.user || null);
      
      if (session?.user) {
        // Load health conditions (still used for user profile display)
        const conditions = await ocrApi.getHealthConditions();
        setHealthConditions(conditions);
      }
    };

    checkUser();

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      setUser(session?.user || null);
      if (session?.user) {
        const conditions = await ocrApi.getHealthConditions();
        setHealthConditions(conditions);
      } else {
        setHealthConditions([]);
      }
    });

    return () => subscription.unsubscribe();
  }, []);

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

  const handleHealthSubmit = async (conditions: any[]) => {
    if (conditions.length === 0) {
      setShowHealthForm(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      // Check if user is authenticated
      if (!user) {
        setError("Please sign in first");
        setLoading(false);
        return;
      }
      
      console.log("Saving health conditions:", conditions);
      console.log("User:", user);
      
      // Use batch add method
      const result = await ocrApi.addHealthConditions(conditions);
      console.log("Save result:", result);
      
      setShowHealthForm(false);
      
      // Wait a moment for database to update
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Reload conditions
      const updated = await ocrApi.getHealthConditions();
      console.log("Reloaded conditions:", updated);
      setHealthConditions(updated);
      
      console.log("Health conditions saved successfully:", updated);
    } catch (error: any) {
      console.error("Error saving health conditions:", error);
      setError(error.message || "Failed to save health conditions. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    setUser(null);
    setHealthConditions([]);
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

        {/* Auth Section */}
        {!user && (
          <div className="max-w-md mx-auto mb-8">
            {showAuth ? (
              <AuthForm />
            ) : (
              <div className="bg-white rounded-xl shadow-lg p-6 text-center">
                <p className="text-gray-600 mb-4">
                  Sign in to track your health conditions and get personalized menu insights
                </p>
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    setShowAuth(true);
                  }}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded-lg transition"
                >
                  Sign In / Sign Up
                </button>
              </div>
            )}
          </div>
        )}

        {/* User Info - ISOLATED FROM FORMS */}
        {user && (
          <div className="max-w-4xl mx-auto mb-6 bg-white rounded-lg shadow p-4">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm text-gray-600">Signed in as</p>
                <p className="font-semibold">{user.email}</p>
                {healthConditions.length > 0 && (
                  <p className="text-xs text-gray-500 mt-1">
                    {healthConditions.length} health condition(s) set
                  </p>
                )}
              </div>
              <div className="flex gap-2">
                {!showHealthForm && (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      console.log("🔵 Add Health button clicked");
                      setShowHealthForm(true);
                    }}
                    className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium py-1 px-4 rounded-lg transition"
                  >
                    {healthConditions.length > 0 ? "Update Health" : "Add Health Conditions"}
                  </button>
                )}
                <button
                  type="button"
                  onClick={async (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    console.log("🔴 Sign out clicked - starting...");
                    try {
                      await handleSignOut();
                      console.log("🔴 Sign out completed");
                    } catch (err) {
                      console.error("🔴 Sign out error:", err);
                    }
                  }}
                  className="bg-gray-400 hover:bg-gray-500 text-white text-sm font-medium py-1 px-4 rounded-lg transition"
                >
                  Sign Out
                </button>
              </div>
            </div>

            {/* Health Conditions Display */}
            {healthConditions.length > 0 && (
              <div className="mt-4 pt-4 border-t">
                <p className="text-sm font-medium text-gray-700 mb-2">Health Conditions:</p>
                <div className="flex flex-wrap gap-2">
                  {healthConditions.map((condition: any, idx: number) => (
                    <span
                      key={idx}
                      className={`text-xs px-2 py-1 rounded ${
                        condition.condition_type === "illness"
                          ? "bg-red-100 text-red-800"
                          : condition.condition_type === "allergy"
                          ? "bg-yellow-100 text-yellow-800"
                          : "bg-blue-100 text-blue-800"
                      }`}
                    >
                      {condition.condition_name}
                      {condition.severity && ` (${condition.severity})`}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Health Form - COMPLETELY SEPARATE FROM MAIN CONTENT */}
      {showHealthForm && user && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={(e) => {
          // Click outside to close
          if (e.target === e.currentTarget) {
            setShowHealthForm(false);
          }
        }}>
          <div className="max-w-2xl w-full mx-4 bg-white rounded-xl shadow-2xl p-6 max-h-[90vh] overflow-y-auto" onClick={(e) => {
            e.stopPropagation(); // Prevent closing when clicking inside
          }}>
            <HealthConditionForm
              onSubmit={async (conditions) => {
                console.log("🟢🟢🟢 page.tsx: onSubmit callback received conditions:", conditions);
                console.log("🟢🟢🟢 Conditions type:", typeof conditions);
                console.log("🟢🟢🟢 Conditions is array:", Array.isArray(conditions));
                await handleHealthSubmit(conditions);
              }}
              onCancel={() => {
                console.log("Health form cancelled");
                setShowHealthForm(false);
              }}
            />
          </div>
        </div>
      )}

      {/* Main Content - SEPARATE CONTAINER */}
      <div className="container mx-auto px-4 py-8">
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

            {/* Info about translation */}
            {!user && (
              <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-800">
                  💡 Tip: Menu items are automatically translated to English from European languages!
                </p>
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
            <MenuDisplay 
              items={menuItems}
            />
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
