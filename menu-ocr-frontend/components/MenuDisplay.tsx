"use client";

import type { MenuItem } from "@/types/menu";

interface MenuDisplayProps {
  items: MenuItem[];
  recommendations?: {
    recommended?: Array<{ name: string; reason?: string }>;
    not_recommended?: Array<{ name: string; reason?: string }>;
  };
  hasFever?: boolean;
  hasGI?: boolean;
}

export default function MenuDisplay({ items, recommendations, hasFever, hasGI }: MenuDisplayProps) {
  if (items.length === 0) {
    return (
      <div className="text-center py-12">
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <p className="mt-2 text-sm text-gray-500">
          No menu items extracted yet. Upload a menu image to get started.
        </p>
      </div>
    );
  }

  // Create lookup maps for recommendations
  const recommendedMap = new Map(
    recommendations?.recommended?.map(r => [r.name.toLowerCase(), r]) || []
  );
  const notRecommendedMap = new Map(
    recommendations?.not_recommended?.map(r => [r.name.toLowerCase(), r]) || []
  );

  // Helper to check if item is recommended/not recommended
  const getRecommendation = (itemName: string) => {
    const nameLower = itemName.toLowerCase();
    
    // Check not recommended first (higher priority)
    for (const [key, value] of notRecommendedMap.entries()) {
      if (nameLower.includes(key) || key.includes(nameLower)) {
        return { type: "not_recommended", reason: value.reason };
      }
    }
    
    // Check recommended
    for (const [key, value] of recommendedMap.entries()) {
      if (nameLower.includes(key) || key.includes(nameLower)) {
        return { type: "recommended", reason: value.reason };
      }
    }
    
    return null;
  };

  return (
    <div className="space-y-4">
      {/* Health Condition Warning */}
      {(hasFever || hasGI) && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
          <h3 className="font-semibold text-yellow-800 mb-2">
            {hasFever && hasGI ? "⚠️ Health Advisory: Fever & Gastrointestinal Symptoms" : 
             hasFever ? "⚠️ Health Advisory: Fever Detected" : 
             "⚠️ Health Advisory: Gastrointestinal Symptoms"}
          </h3>
          <p className="text-sm text-yellow-700">
            Some dishes may not be recommended based on your health condition. 
            Please review the recommendations below.
          </p>
        </div>
      )}

      {/* Not Recommended Section */}
      {recommendations?.not_recommended && recommendations.not_recommended.length > 0 && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-red-700 mb-2">
            ⚠️ Not Recommended
          </h3>
          <div className="space-y-2">
            {recommendations.not_recommended.map((item, idx) => (
              <div
                key={idx}
                className="border-2 border-red-300 rounded-lg p-3 bg-red-50"
              >
                <div className="flex justify-between items-start">
                  <h4 className="font-semibold text-red-900">{item.name}</h4>
                </div>
                {item.reason && (
                  <p className="text-sm text-red-700 mt-1">{item.reason}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommended Section */}
      {recommendations?.recommended && recommendations.recommended.length > 0 && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-green-700 mb-2">
            ✅ Recommended
          </h3>
          <div className="space-y-2">
            {recommendations.recommended.map((item, idx) => (
              <div
                key={idx}
                className="border-2 border-green-300 rounded-lg p-3 bg-green-50"
              >
                <div className="flex justify-between items-start">
                  <h4 className="font-semibold text-green-900">{item.name}</h4>
                </div>
                {item.reason && (
                  <p className="text-sm text-green-700 mt-1">{item.reason}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All Menu Items */}
      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-2">All Menu Items</h3>
        <div className="space-y-3 max-h-[400px] overflow-y-auto">
          {items.map((item, index) => {
            const rec = getRecommendation(item.name);
            
            return (
              <div
                key={index}
                className={`border rounded-lg p-4 transition ${
                  rec?.type === "not_recommended"
                    ? "border-red-300 bg-red-50"
                    : rec?.type === "recommended"
                    ? "border-green-300 bg-green-50"
                    : "border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50"
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-semibold text-lg text-gray-900">
                    {item.name}
                    {rec && (
                      <span className={`ml-2 text-xs font-normal ${
                        rec.type === "not_recommended" ? "text-red-600" : "text-green-600"
                      }`}>
                        {rec.type === "not_recommended" ? "⚠️" : "✅"}
                      </span>
                    )}
                  </h3>
                  {item.price && (
                    <span className="text-lg font-bold text-blue-600">
                      {item.price}
                    </span>
                  )}
                </div>
                
                {item.description && (
                  <p className="text-sm text-gray-600 mt-1">{item.description}</p>
                )}
                
                {rec?.reason && (
                  <p className={`text-xs mt-2 ${
                    rec.type === "not_recommended" ? "text-red-600" : "text-green-600"
                  }`}>
                    {rec.reason}
                  </p>
                )}
                
                {item.category && (
                  <span className="inline-block mt-2 px-2 py-1 text-xs font-medium text-purple-700 bg-purple-100 rounded">
                    {item.category}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
