"use client";

interface StatusDisplayProps {
  loading: boolean;
  error: string | null;
  processingTime: number | null;
}

export default function StatusDisplay({
  loading,
  error,
  processingTime,
}: StatusDisplayProps) {
  if (loading) {
    return (
      <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
          <p className="text-blue-800">Processing image...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-800">❌ {error}</p>
      </div>
    );
  }

  if (processingTime !== null) {
    return (
      <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
        <p className="text-green-800">
          ✅ Processed successfully in {processingTime}ms
        </p>
      </div>
    );
  }

  return null;
}

