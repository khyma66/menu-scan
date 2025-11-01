"use client";

import { useState } from "react";
import { ocrApi } from "@/lib/api";
import type { MenuItem } from "@/types/menu";

interface ImageUploadProps {
  onOCRComplete: (items: MenuItem[], time: number) => void;
  onError: (error: string) => void;
  onLoading: (loading: boolean) => void;
}

export default function ImageUpload({
  onOCRComplete,
  onError,
  onLoading,
}: ImageUploadProps) {
  const [imageUrl, setImageUrl] = useState("");
  const [useLLM, setUseLLM] = useState(true);
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!imageUrl.trim()) {
      onError("Please enter an image URL");
      return;
    }

    onLoading(true);
    try {
      const response = await ocrApi.processImage(imageUrl, useLLM);
      
      if (response.success) {
        onOCRComplete(response.menu_items, response.processing_time_ms);
        setUploadedImage(imageUrl);
      } else {
        onError("Failed to process image");
      }
    } catch (error: any) {
      onError(error.message || "An error occurred");
    } finally {
      onLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Image Input */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Image URL
          </label>
          <input
            type="url"
            value={imageUrl}
            onChange={(e) => setImageUrl(e.target.value)}
            placeholder="https://example.com/menu.jpg"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* LLM Toggle */}
        <div className="flex items-center space-x-3">
          <input
            type="checkbox"
            id="useLLM"
            checked={useLLM}
            onChange={(e) => setUseLLM(e.target.checked)}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          <label htmlFor="useLLM" className="text-sm text-gray-700">
            Use AI Enhancement (slower but more accurate)
          </label>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition duration-200"
        >
          Process Image
        </button>
      </form>

      {/* Preview Image */}
      {uploadedImage && (
        <div className="mt-4">
          <p className="text-sm text-gray-600 mb-2">Last Uploaded:</p>
          <img
            src={uploadedImage}
            alt="Uploaded menu"
            className="w-full rounded-lg border border-gray-300 max-h-64 object-contain bg-gray-100"
          />
        </div>
      )}
    </div>
  );
}

