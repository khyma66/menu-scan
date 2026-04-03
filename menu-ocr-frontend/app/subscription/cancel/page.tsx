"use client";

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

function CancelContent() {
  const params = useSearchParams();
  const deeplink = params.get("deeplink") ?? "fooder://subscription-result?status=cancel";

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-white px-6">
      <div className="text-5xl mb-4">😔</div>
      <h1 className="text-xl font-bold text-gray-800 mb-2">Subscription not started</h1>
      <p className="text-gray-500 text-sm text-center mb-8">
        No payment was taken. You can upgrade any time from the app.
      </p>
      <a
        href={deeplink}
        className="w-full max-w-xs bg-gray-900 text-white text-center py-3 px-6 rounded-xl font-semibold text-base block"
      >
        Back to App
      </a>
    </div>
  );
}

export default function SubscriptionCancelPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen"><div className="animate-spin w-8 h-8 border-4 border-gray-400 border-t-transparent rounded-full" /></div>}>
      <CancelContent />
    </Suspense>
  );
}
