"use client";

import type { MenuItem } from "@/types/menu";

interface MenuDisplayProps {
  items: MenuItem[];
}

export default function MenuDisplay({ items }: MenuDisplayProps) {
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

  return (
    <div className="space-y-4 max-h-[600px] overflow-y-auto">
      {items.map((item, index) => (
        <div
          key={index}
          className="border border-gray-200 rounded-lg p-4 bg-gradient-to-r from-blue-50 to-purple-50 hover:shadow-md transition"
        >
          <div className="flex justify-between items-start mb-2">
            <h3 className="font-semibold text-lg text-gray-900">
              {item.name}
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
          
          {item.category && (
            <span className="inline-block mt-2 px-2 py-1 text-xs font-medium text-purple-700 bg-purple-100 rounded">
              {item.category}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}

