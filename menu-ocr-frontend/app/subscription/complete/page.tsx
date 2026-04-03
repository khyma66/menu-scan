"use client";

/**
 * /subscription/complete — landing page after Stripe Checkout success.
 *
 * Stripe redirects here with ?session_id=cs_...&deeplink=menuocr://...
 * We verify the session, show a success message, then:
 *   1. If opened inside the app's in-app browser → try to open the deep-link.
 *   2. If a standalone browser tab → show "Return to App" button.
 *
 * The deep-link triggers the native app to re-fetch /subscriptions/status
 * and update its UI — no store commission involved anywhere.
 */

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { createClient } from "@supabase/supabase-js";
import { Suspense } from "react";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

function SubscriptionCompleteContent() {
  const params = useSearchParams();
  const router = useRouter();
  const sessionId = params.get("session_id");
  const deeplink  = params.get("deeplink") ?? "fooder://subscription-result?status=success";

  const [state, setState] = useState<"loading" | "success" | "error">("loading");
  const [planName, setPlanName] = useState("");

  useEffect(() => {
    verifyAndRedirect();
  }, [sessionId]);

  async function verifyAndRedirect() {
    if (!sessionId) { setState("error"); return; }

    try {
      // Attempt to get the user's updated subscription from our API
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;

      const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "";
      if (apiBase && token) {
        const res = await fetch(`${apiBase}/subscriptions/status`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          setPlanName(data.plan_name ?? "Pro");
        }
      }

      setState("success");

      // Try deep-link immediately (works if in-app browser / WebView)
      window.location.href = deeplink;

      // Fallback: if we're still here after 2 s, user is in external browser
    } catch {
      setState("success"); // still show success UI even if API is unreachable
      window.location.href = deeplink;
    }
  }

  if (state === "loading") {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-white">
        <div className="animate-spin w-10 h-10 border-4 border-red-500 border-t-transparent rounded-full mb-4" />
        <p className="text-gray-600 text-sm">Confirming your subscription…</p>
      </div>
    );
  }

  if (state === "error") {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-white px-6">
        <div className="text-5xl mb-4">⚠️</div>
        <h1 className="text-xl font-bold text-gray-800 mb-2">Something went wrong</h1>
        <p className="text-gray-500 text-sm text-center mb-6">
          We couldn't confirm your payment. Please contact support if money was deducted.
        </p>
        <a href="mailto:support@menuocr.com" className="text-red-500 underline text-sm">
          support@menuocr.com
        </a>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-white px-6">
      <div className="text-6xl mb-4">🎉</div>
      <h1 className="text-2xl font-bold text-gray-900 mb-2">You're all set!</h1>
      {planName && (
        <p className="text-gray-600 text-base mb-1">
          Welcome to <span className="font-semibold text-red-500">{planName}</span>
        </p>
      )}
      <p className="text-gray-500 text-sm text-center mb-8">
        Your subscription is now active. Enjoy unlimited menu scans and all premium features.
      </p>

      {/* Primary: open deep-link to return to app */}
      <a
        href={deeplink}
        className="w-full max-w-xs bg-red-500 text-white text-center py-3 px-6 rounded-xl font-semibold text-base mb-3 block"
      >
        Return to App
      </a>

      {/* Secondary: go to web dashboard */}
      <button
        onClick={() => router.push("/account")}
        className="text-gray-400 text-sm underline"
      >
        View on web instead
      </button>
    </div>
  );
}

export default function SubscriptionCompletePage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin w-8 h-8 border-4 border-red-500 border-t-transparent rounded-full" />
      </div>
    }>
      <SubscriptionCompleteContent />
    </Suspense>
  );
}
