"use client";

/**
 * PricingPageFull — commission-free web subscription checkout.
 *
 * WHY THIS EXISTS:
 *   Apple/Google charge 15-30% on all in-app subscriptions.
 *   By routing ALL purchases through Stripe on the web, we keep full revenue.
 *   Native apps open this page in the system browser with ?token= so the user
 *   is already authenticated — no re-login needed.
 *
 * FLOW:
 *   1. App opens: https://menuocr.com/pricing?token=<supabase_access_token>&refresh=<refresh_token>
 *   2. Page restores Supabase session from token params
 *   3. User picks a plan → POST /subscriptions/checkout-session
 *   4. Stripe Checkout opens (still in same browser tab)
 *   5. Success → /subscription/complete → deep-link menuocr://subscription-result?status=success
 *   6. Native app receives deep-link, re-fetches /subscriptions/status, updates plan UI
 *
 * EDGE CASES:
 *   - No token param (direct web visit) → standard Supabase session / login redirect
 *   - Invalid/expired token → user sees login prompt
 *   - Already subscribed → shows "Current plan" badge + Manage link
 *   - Stripe unavailable → graceful error with support email
 *   - Yearly/monthly toggle with live price preview
 */

import { useState, useEffect, useCallback } from "react";
import { createClient } from "@supabase/supabase-js";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

interface Plan {
  id: string;
  display_name: string;
  description: string;
  price_monthly_cents: number;
  price_yearly_cents: number | null;
  features: string[];
  sort_order: number;
}

interface SubStatus {
  plan_id: string;
  plan_name: string;
  status: string;
  is_effective: boolean;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
}

function formatPrice(cents: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(cents / 100);
}

function CheckIcon() {
  return (
    <svg className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
    </svg>
  );
}

function PricingContent() {
  const searchParams = useSearchParams();
  const [plans, setPlans]         = useState<Plan[]>([]);
  const [subStatus, setSubStatus] = useState<SubStatus | null>(null);
  const [user, setUser]           = useState<any>(null);
  const [loading, setLoading]     = useState(true);
  const [purchasing, setPurchasing] = useState<string | null>(null);
  const [cycle, setCycle]         = useState<"monthly" | "yearly">("monthly");
  const [message, setMessage]     = useState("");

  const tokenParam   = searchParams.get("token");
  const refreshParam = searchParams.get("refresh") ?? "";

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      let token: string | null = null;

      if (tokenParam) {
        // Native app passed token — restore session silently
        const { data } = await supabase.auth.setSession({
          access_token: tokenParam,
          refresh_token: refreshParam,
        });
        token = data.session?.access_token ?? null;
        setUser(data.user);
        // Remove tokens from address bar immediately — they should never be visible
        // to users or appear in browser history / server logs.
        if (typeof window !== "undefined") {
          const clean = new URL(window.location.href);
          clean.searchParams.delete("token");
          clean.searchParams.delete("refresh");
          window.history.replaceState({}, "", clean.toString());
        }
      } else {
        const { data: { session } } = await supabase.auth.getSession();
        token = session?.access_token ?? null;
        setUser(session?.user ?? null);
      }

      // Load plans (public endpoint)
      if (API_BASE) {
        const r = await fetch(`${API_BASE}/subscriptions/plans`);
        if (r.ok) {
          const d = await r.json();
          const paid = (d.plans ?? []).filter((p: Plan) => p.id !== "free");
          setPlans(paid);
        }
      }

      // Load current subscription status (requires auth)
      if (token && API_BASE) {
        const r = await fetch(`${API_BASE}/subscriptions/status`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (r.ok) setSubStatus(await r.json());
      }
    } catch (e) {
      console.error("PricingPageFull load error", e);
    } finally {
      setLoading(false);
    }
  }, [tokenParam, refreshParam]);

  useEffect(() => { loadData(); }, [loadData]);

  async function subscribe(planId: string) {
    if (!user) {
      // Redirect to login, returning here after
      window.location.href = `/auth/login?redirect=${encodeURIComponent(window.location.href)}`;
      return;
    }

    setPurchasing(planId);
    setMessage("");
    try {
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;
      if (!token) { setMessage("Session expired — please log in again."); return; }

      const res = await fetch(`${API_BASE}/subscriptions/checkout-session`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          plan_id: planId,
          billing_cycle: cycle,
          success_deeplink: "menuocr://subscription-result?status=success",
          cancel_deeplink:  "menuocr://subscription-result?status=cancel",
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setMessage(err.detail ?? "Could not start checkout — please try again.");
        return;
      }

      const { checkout_url } = await res.json();
      window.location.href = checkout_url;   // Stripe Checkout — no IAP commission
    } catch {
      setMessage("Network error. Please check your connection and try again.");
    } finally {
      setPurchasing(null);
    }
  }

  async function manageSubscription() {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;
      if (!token) return;
      const res = await fetch(`${API_BASE}/subscriptions/customer-portal`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const { portal_url } = await res.json();
        window.location.href = portal_url;
      }
    } catch {}
  }

  const yearlySavePct = (plan: Plan): number | null => {
    if (!plan.price_yearly_cents || !plan.price_monthly_cents) return null;
    const monthly = plan.price_monthly_cents * 12;
    return Math.round(((monthly - plan.price_yearly_cents) / monthly) * 100);
  };

  const isCurrent = (planId: string) =>
    subStatus?.plan_id === planId && subStatus?.is_effective;

  const isSubscribed = subStatus?.is_effective && subStatus.plan_id !== "free";

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-white">
        <div className="animate-spin w-8 h-8 border-4 border-red-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-2xl mx-auto">

        {/* Header */}
        <div className="text-center mb-10">
          <p className="text-4xl mb-3">🍅</p>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Upgrade your plan</h1>
          <p className="text-gray-500 text-sm">
            Unlimited scans · Full nutrition details · Cancel any time
          </p>
          {!user && (
            <a
              href={`/auth/login?redirect=${encodeURIComponent(typeof window !== "undefined" ? window.location.href : "/pricing")}`}
              className="mt-4 inline-block bg-red-500 text-white px-5 py-2 rounded-full text-sm font-semibold"
            >
              Log in to subscribe
            </a>
          )}
        </div>

        {/* Active subscription banner */}
        {isSubscribed && (
          <div className="bg-green-50 border border-green-200 rounded-2xl px-5 py-4 mb-8 flex items-center justify-between">
            <div>
              <p className="font-semibold text-green-800 text-sm">
                ✓ Active: {subStatus?.plan_name}
              </p>
              {subStatus?.current_period_end && (
                <p className="text-xs text-green-600 mt-0.5">
                  {subStatus.cancel_at_period_end ? "Cancels" : "Renews"}{" "}
                  {new Date(subStatus.current_period_end).toLocaleDateString(undefined, {
                    year: "numeric", month: "long", day: "numeric"
                  })}
                </p>
              )}
            </div>
            <button
              onClick={manageSubscription}
              className="text-xs font-semibold text-green-700 bg-green-100 px-3 py-1.5 rounded-lg"
            >
              Manage →
            </button>
          </div>
        )}

        {/* Billing toggle */}
        <div className="flex justify-center mb-8">
          <div className="inline-flex bg-white border border-gray-200 rounded-full p-1 gap-1">
            {(["monthly", "yearly"] as const).map((c) => {
              const saving = plans[0] ? yearlySavePct(plans[0]) : null;
              return (
                <button
                  key={c}
                  onClick={() => setCycle(c)}
                  className={`px-5 py-2 text-sm font-medium rounded-full transition-all ${
                    cycle === c
                      ? "bg-red-500 text-white shadow"
                      : "text-gray-500 hover:text-gray-800"
                  }`}
                >
                  {c === "monthly" ? "Monthly" : "Yearly"}
                  {c === "yearly" && saving && (
                    <span className={`ml-1.5 text-xs font-bold ${cycle === "yearly" ? "text-green-200" : "text-green-600"}`}>
                      −{saving}%
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Plan cards */}
        {plans.length === 0 ? (
          <div className="text-center text-gray-400 py-12">
            Plans temporarily unavailable. Please try again shortly.
          </div>
        ) : (
          <div className="grid gap-5 sm:grid-cols-2">
            {plans.map((plan, idx) => {
              const perMonthCents = cycle === "yearly" && plan.price_yearly_cents
                ? Math.round(plan.price_yearly_cents / 12)
                : plan.price_monthly_cents;
              const billedCents = cycle === "yearly" && plan.price_yearly_cents
                ? plan.price_yearly_cents
                : plan.price_monthly_cents;
              const popular  = idx === 0;
              const current  = isCurrent(plan.id);
              const saving   = yearlySavePct(plan);

              return (
                <div
                  key={plan.id}
                  className={`bg-white rounded-2xl p-6 flex flex-col relative border-2 ${
                    popular ? "border-red-400 shadow-xl" : "border-gray-100 shadow"
                  }`}
                >
                  {popular && (
                    <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                      <span className="bg-red-500 text-white text-[10px] font-bold px-3 py-1 rounded-full tracking-wide">
                        MOST POPULAR
                      </span>
                    </div>
                  )}

                  <div className="mb-3">
                    <h2 className="text-lg font-bold text-gray-900">{plan.display_name}</h2>
                    <p className="text-gray-400 text-xs mt-0.5">{plan.description}</p>
                  </div>

                  <div className="mb-5">
                    <div className="flex items-end gap-1">
                      <span className="text-3xl font-extrabold text-gray-900">
                        {formatPrice(perMonthCents)}
                      </span>
                      <span className="text-gray-400 text-sm mb-1">/mo</span>
                    </div>
                    {cycle === "yearly" && plan.price_yearly_cents && (
                      <p className="text-xs text-gray-400 mt-0.5">
                        {formatPrice(billedCents)} billed yearly
                        {saving ? (
                          <span className="ml-1 text-green-600 font-semibold">· Save {saving}%</span>
                        ) : null}
                      </p>
                    )}
                  </div>

                  <ul className="space-y-2 mb-6 flex-1">
                    {(plan.features ?? []).map((f, fi) => (
                      <li key={fi} className="flex items-start gap-2 text-sm text-gray-700">
                        <CheckIcon />
                        {f}
                      </li>
                    ))}
                  </ul>

                  {current ? (
                    <div className="w-full text-center py-3 bg-green-50 border border-green-200 text-green-700 font-semibold rounded-xl text-sm">
                      ✓ Current plan
                    </div>
                  ) : (
                    <button
                      onClick={() => subscribe(plan.id)}
                      disabled={!!purchasing}
                      className={`w-full py-3 rounded-xl font-semibold text-sm transition-all ${
                        popular
                          ? "bg-red-500 text-white hover:bg-red-600 active:scale-95"
                          : "bg-gray-900 text-white hover:bg-gray-700 active:scale-95"
                      } ${purchasing ? "opacity-50 cursor-not-allowed" : ""}`}
                    >
                      {purchasing === plan.id
                        ? "Redirecting to checkout…"
                        : `Get ${plan.display_name}`}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Free tier note */}
        <p className="text-center text-xs text-gray-400 mt-6">
          Staying on Free? You get 3 scans/month — no credit card needed.
        </p>

        {/* Error */}
        {message && (
          <div className="mt-5 bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl px-4 py-3 text-center">
            {message}
          </div>
        )}

        {/* Trust signals */}
        <div className="mt-10 border-t border-gray-100 pt-6 text-center text-xs text-gray-400 space-y-1">
          <p>🔒 Payments processed by Stripe — PCI-DSS Level 1 certified</p>
          <p>Accepts cards, PayPal, SEPA, iDEAL, BACS and 135+ currencies</p>
          <p>Automatic local tax (VAT / GST) calculated at checkout</p>
          <p>UPI and PIX available via Stripe (enable in your Stripe dashboard)</p>
          <p className="mt-2">
            Questions?{" "}
            <a href="mailto:support@menuocr.com" className="underline text-gray-500">
              support@menuocr.com
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}

export default function PricingPageFull() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-screen bg-white">
        <div className="animate-spin w-8 h-8 border-4 border-red-500 border-t-transparent rounded-full" />
      </div>
    }>
      <PricingContent />
    </Suspense>
  );
}
