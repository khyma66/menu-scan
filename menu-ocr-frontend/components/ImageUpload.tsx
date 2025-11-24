"use client";

import { useState, useRef } from "react";
import { ocrApi } from "@/lib/api";
import type { MenuItem } from "@/types/menu";

interface ImageUploadProps {
  onOCRComplete: (items: MenuItem[], time: number, metadata?: any) => void;
  onError: (error: string) => void;
  onLoading: (loading: boolean) => void;
}

export default function ImageUpload({
  onOCRComplete,
  onError,
  onLoading,
}: ImageUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [useLLM, setUseLLM] = useState(false); // Disabled by default for faster processing
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith("image/")) {
      onError("Please select an image file");
      return;
    }

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      onError("Image size exceeds 10MB limit");
      return;
    }

    setSelectedFile(file);
    onError(""); // Clear previous errors

    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreview(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleUpload = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    e.stopPropagation();
    
    // CRITICAL: Check if event came from health form
    const target = e.target as HTMLElement;
    const healthForm = target.closest('#health-condition-form');
    if (healthForm) {
      console.log("🟢 BLOCKED: ImageUpload form submit blocked - came from health form");
      console.log("🟢 Health form element:", healthForm);
      e.stopPropagation();
      if (e.nativeEvent && typeof e.nativeEvent.stopImmediatePropagation === 'function') {
        e.nativeEvent.stopImmediatePropagation();
      }
      return;
    }
    
    // Additional check: ensure this form was actually submitted (has selected file)
    // This prevents accidental submissions
    if (!selectedFile) {
      console.log("🟢 Blocked: No file selected, preventing submission");
      return;
    }
    
    console.log("🟢🟢🟢 ImageUpload: handleUpload called");
    console.log("🟢🟢🟢 Event type:", e.type);
    console.log("🟢🟢🟢 Event target:", target);
    console.log("🟢🟢🟢 Selected file:", selectedFile?.name);

    if (!selectedFile) {
      onError("Please select an image file");
      return;
    }

    onLoading(true);
    onError("");

    try {
      // Upload file and process
      const response = await ocrApi.processImageFile(selectedFile, useLLM);

      if (response.success) {
        onOCRComplete(response.menu_items, response.processing_time_ms, { ...response.metadata, raw_text: response.raw_text });
      } else {
        onError("Failed to process image");
      }
    } catch (error: any) {
      // Handle connection errors
      if (error.message?.includes("fetch") || error.message?.includes("network")) {
        onError("Connection error: Could not reach the server. Please check if the backend is running at http://localhost:8000");
      } else if (error.message?.includes("Failed to upload")) {
        onError("Failed to upload image. Please check the file and try again.");
      } else {
        onError(error.message || "An error occurred while processing the image");
      }
    } finally {
      onLoading(false);
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setPreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    onError("");
  };

  return (
    <div className="space-y-4">
      {/* File Upload */}
      <form 
        onSubmit={handleUpload} 
        className="space-y-4"
        id="image-upload-form"
        onClick={(e) => {
          // Only handle clicks inside this form
          if (!(e.target as HTMLElement).closest('#image-upload-form')) {
            e.stopPropagation();
          }
        }}
      >
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Upload Menu Image
          </label>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileSelect}
              className="hidden"
              id="file-upload"
            />
            <label
              htmlFor="file-upload"
              className="cursor-pointer flex flex-col items-center"
            >
              <svg
                className="w-12 h-12 text-gray-400 mb-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              <span className="text-sm text-gray-600">
                Click to upload or drag and drop
              </span>
              <span className="text-xs text-gray-500 mt-1">
                PNG, JPG, JPEG, WEBP (max 10MB)
              </span>
            </label>
          </div>

          {selectedFile && (
            <div className="mt-2 text-sm text-gray-600">
              Selected: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
            </div>
          )}
        </div>

        {/* Preview */}
        {preview && (
          <div className="mt-4">
            <p className="text-sm text-gray-600 mb-2">Preview:</p>
            <img
              src={preview}
              alt="Preview"
              className="w-full rounded-lg border border-gray-300 max-h-64 object-contain bg-gray-100"
            />
          </div>
        )}

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

        {/* Submit and Clear Buttons */}
        <div className="flex gap-2">
          <button
            type="submit"
            disabled={!selectedFile}
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Process Image
          </button>
          {selectedFile && (
            <button
              type="button"
              onClick={handleClear}
              className="px-4 py-2 bg-gray-300 hover:bg-gray-400 text-gray-800 font-medium rounded-lg transition"
            >
              Clear
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
