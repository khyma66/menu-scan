"use client";

import { useState } from "react";
import type { MenuItem, UserTier } from "@/types/menu";

interface MenuDisplayProps {
  items: MenuItem[];
  userTier: UserTier;
}

function SpicinessIndicator({ level }: { level: string | null }) {
  if (!level || level === "none") return null;
  const levels: Record<string, { dots: number; color: string }> = {
    mild: { dots: 1, color: "text-yellow-500" },
    medium: { dots: 2, color: "text-orange-500" },
    hot: { dots: 3, color: "text-red-500" },
    "extra hot": { dots: 4, color: "text-red-700" },
  };
  const config = levels[level.toLowerCase()] || { dots: 1, color: "text-yellow-500" };
  return (
    <span className={`${config.color} text-sm`} title={`Spiciness: ${level}`}>
      {"🌶️".repeat(config.dots)}
    </span>
  );
}

function RecommendationBadge({ rec }: { rec: string | null }) {
  if (!rec) return null;
  const styles: Record<string, string> = {
    "Most Recommended": "bg-green-100 text-green-800 border-green-200",
    Recommended: "bg-blue-100 text-blue-800 border-blue-200",
    "Not Recommended": "bg-red-100 text-red-800 border-red-200",
  };
  const icons: Record<string, string> = {
    "Most Recommended": "⭐",
    Recommended: "👍",
    "Not Recommended": "⚠️",
  };
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full border ${styles[rec] || "bg-gray-100 text-gray-700"}`}>
      {icons[rec] || ""} {rec}
    </span>
  );
}

function LockedOverlay({ tierNeeded }: { tierNeeded: string }) {
  return (
    <div className="relative">
      <div className="absolute inset-0 bg-white/80 backdrop-blur-sm rounded-lg z-10 flex flex-col items-center justify-center">
        <span className="text-2xl mb-1">🔒</span>
        <p className="text-xs font-semibold text-gray-600">
          Upgrade to <span className="text-purple-600 uppercase">{tierNeeded}</span> to unlock
        </p>
      </div>
    </div>
  );
}

export default function MenuDisplay({ items, userTier }: MenuDisplayProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (items.length === 0) {
    return (
      <div className="text-center py-12">
        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p className="mt-2 text-sm text-gray-500">No menu items extracted yet. Upload a menu image to get started.</p>
      </div>
    );
  }

  const canSeeAdditionalDetails = userTier === "max";
  const canSeeBasicEnrichment = userTier === "pro" || userTier === "max";

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-800 mb-2">
        Menu Items <span className="text-sm font-normal text-gray-500">({items.length} dishes)</span>
      </h3>
      <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1">
        {items.map((item, index) => {
          const isExpanded = expandedIndex === index;
          const hasEnrichment = (item.ingredients && item.ingredients.length > 0) || item.taste || item.similarDish1;

          return (
            <div
              key={index}
              className="border border-gray-200 rounded-xl bg-white shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden"
            >
              {/* Basic Info — Always Visible */}
              <div
                className="p-4 cursor-pointer"
                onClick={() => setExpandedIndex(isExpanded ? null : index)}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-semibold text-lg text-gray-900">{item.name}</h3>
                      <SpicinessIndicator level={item.spiciness_level} />
                      <RecommendationBadge rec={item.recommendation} />
                    </div>
                    {item.description && (
                      <p className="text-sm text-gray-600 mt-1">{item.description}</p>
                    )}
                    <div className="flex items-center gap-2 mt-2 flex-wrap">
                      {item.category && (
                        <span className="px-2 py-0.5 text-xs font-medium text-purple-700 bg-purple-50 rounded-full">
                          {item.category}
                        </span>
                      )}
                      {item.taste && (
                        <span className="px-2 py-0.5 text-xs font-medium text-amber-700 bg-amber-50 rounded-full">
                          👅 {item.taste}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    {item.price && (
                      <span className="text-lg font-bold text-blue-600">{item.price}</span>
                    )}
                    {hasEnrichment && (
                      <button
                        className="text-xs text-gray-400 hover:text-gray-600 transition"
                        title={isExpanded ? "Collapse" : "Expand details"}
                      >
                        {isExpanded ? "▲" : "▼"}
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Expanded Details — Gated by Tier */}
              {isExpanded && hasEnrichment && (
                <div className="border-t border-gray-100 bg-gradient-to-b from-gray-50 to-white p-4 space-y-3 relative">
                  {/* Recommendation — pro+ */}
                  {canSeeBasicEnrichment && (
                    <div className="flex items-start gap-2 text-sm">
                      <span className="text-gray-400 mt-0.5">💡</span>
                      <p className="text-gray-600 italic">
                        {item.recommendation_reason || "Please enter details in Health tab for recommendation."}
                      </p>
                    </div>
                  )}

                  {/* Ingredients — max only */}
                  {item.ingredients && item.ingredients.length > 0 && (
                    <div className="relative">
                      {!canSeeAdditionalDetails && (
                        <div className="absolute inset-0 bg-white/80 backdrop-blur-[2px] rounded-lg z-10 flex flex-col items-center justify-center py-4">
                          <span className="text-xl mb-1">🔒</span>
                          <p className="text-xs font-semibold text-gray-500">
                            Upgrade to <span className="text-purple-600">MAX</span> to see ingredients
                          </p>
                        </div>
                      )}
                      <div>
                        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Ingredients</p>
                        <div className="flex flex-wrap gap-1">
                          {item.ingredients.map((ing, i) => (
                            <span key={i} className="px-2 py-0.5 text-xs bg-green-50 text-green-700 rounded-full border border-green-100">
                              {ing}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Allergens — max only */}
                  {item.allergens && item.allergens.length > 0 && (
                    <div className="relative">
                      {!canSeeAdditionalDetails && (
                        <div className="absolute inset-0 bg-white/80 backdrop-blur-[2px] rounded-lg z-10 flex flex-col items-center justify-center py-4">
                          <span className="text-xl mb-1">🔒</span>
                          <p className="text-xs font-semibold text-gray-500">
                            Upgrade to <span className="text-purple-600">MAX</span> to see allergens
                          </p>
                        </div>
                      )}
                      <div>
                        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">⚠️ Allergens</p>
                        <div className="flex flex-wrap gap-1">
                          {item.allergens.map((al, i) => (
                            <span key={i} className="px-2 py-0.5 text-xs bg-red-50 text-red-700 rounded-full border border-red-100">
                              {al}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Similar Dishes — max only */}
                  {(item.similarDish1 || item.similarDish2) && (
                    <div className="relative">
                      {!canSeeAdditionalDetails && (
                        <div className="absolute inset-0 bg-white/80 backdrop-blur-[2px] rounded-lg z-10 flex flex-col items-center justify-center py-4">
                          <span className="text-xl mb-1">🔒</span>
                          <p className="text-xs font-semibold text-gray-500">
                            Upgrade to <span className="text-purple-600">MAX</span> to see similar dishes
                          </p>
                        </div>
                      )}
                      <div>
                        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Similar Dishes</p>
                        <div className="flex gap-2">
                          {item.similarDish1 && (
                            <span className="px-3 py-1 text-xs bg-indigo-50 text-indigo-700 rounded-full border border-indigo-100">
                              🍽️ {item.similarDish1}
                            </span>
                          )}
                          {item.similarDish2 && (
                            <span className="px-3 py-1 text-xs bg-indigo-50 text-indigo-700 rounded-full border border-indigo-100">
                              🍽️ {item.similarDish2}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
