"use client";

/**
 * /auth/login — universal login gate.
 *
 * Always accessible (no auth guard). Used by:
 *  - PricingPageFull when session is missing
 *  - Any future web feature requiring auth
 *
 * After login the user is redirected to `?redirect=` URL (defaults to /).
 */

import { useState, Suspense } from "react";
import { createClient } from "@supabase/supabase-js";
import { useSearchParams, useRouter } from "next/navigation";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

function LoginForm() {
  const searchParams = useSearchParams();
  const router       = useRouter();
  const redirectTo   = searchParams.get("redirect") ?? "/";

  const [email,    setEmail]    = useState("");
  const [password, setPassword] = useState("");
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState("");
  const [mode,     setMode]     = useState<"sign_in" | "sign_up">("sign_in");

  async function handleEmail(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const fn = mode === "sign_in"
        ? supabase.auth.signInWithPassword({ email, password })
        : supabase.auth.signUp({ email, password });
      const { error: authErr } = await fn;
      if (authErr) { setError(authErr.message); return; }
      router.replace(redirectTo);
    } finally {
      setLoading(false);
    }
  }

  function handleOAuth(provider: "google" | "apple") {
    const redirectParam = encodeURIComponent(
      `${window.location.origin}/auth/callback?next=${encodeURIComponent(redirectTo)}`
    );
    window.location.href = `/auth/${provider}?redirect_to=${redirectParam}`;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm bg-white rounded-2xl shadow-sm border border-gray-100 p-8">

        {/* Brand */}
        <div className="text-center mb-8">
          <span className="text-3xl font-bold text-red-500">Fooder</span>
          <p className="mt-1 text-sm text-gray-500">
            {mode === "sign_in" ? "Welcome back" : "Create your account"}
          </p>
        </div>

        {/* OAuth buttons */}
        <div className="flex flex-col gap-3 mb-6">
          <button
            onClick={() => handleOAuth("google")}
            className="flex items-center justify-center gap-3 w-full py-3 px-4 border border-gray-200 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continue with Google
          </button>

          <button
            onClick={() => handleOAuth("apple")}
            className="flex items-center justify-center gap-3 w-full py-3 px-4 bg-black rounded-xl text-sm font-medium text-white hover:bg-gray-900 transition-colors"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M17.05 20.28c-.98.95-2.05.8-3.08.35-1.09-.46-2.09-.48-3.24 0-1.44.62-2.2.44-3.06-.35C2.79 15.25 3.51 7.7 9.05 7.4c1.4.07 2.38.74 3.2.8 1.22-.25 2.39-.96 3.7-.84 1.58.18 2.76.84 3.53 2.1-3.26 1.98-2.44 6.12.57 7.32-.55 1.45-1.28 2.88-3 3.5M13 3.5c.13 1.9-1.42 3.5-3.27 3.5-.14-1.8 1.47-3.5 3.27-3.5"/>
            </svg>
            Continue with Apple
          </button>
        </div>

        {/* Divider */}
        <div className="flex items-center gap-3 mb-6">
          <div className="flex-1 h-px bg-gray-200" />
          <span className="text-xs text-gray-400">or</span>
          <div className="flex-1 h-px bg-gray-200" />
        </div>

        {/* Email/password form */}
        <form onSubmit={handleEmail} className="flex flex-col gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-red-400 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-red-400 focus:border-transparent"
            />
          </div>

          {error && (
            <p className="text-xs text-red-500 bg-red-50 px-3 py-2 rounded-lg">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-red-500 text-white text-sm font-semibold hover:bg-red-600 active:scale-95 transition-all disabled:opacity-60"
          >
            {loading ? "Please wait…" : mode === "sign_in" ? "Sign in" : "Create account"}
          </button>
        </form>

        {/* Toggle mode */}
        <p className="mt-5 text-center text-xs text-gray-500">
          {mode === "sign_in" ? "Don't have an account? " : "Already have an account? "}
          <button
            onClick={() => { setMode(m => m === "sign_in" ? "sign_up" : "sign_in"); setError(""); }}
            className="text-red-500 font-medium hover:underline"
          >
            {mode === "sign_in" ? "Sign up" : "Sign in"}
          </button>
        </p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
