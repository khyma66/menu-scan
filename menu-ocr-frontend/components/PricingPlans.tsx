"use client";

import { useState, useEffect } from "react";
import { createClient } from "@supabase/supabase-js";

interface PricingPlan {
  id: string;
  name: string;
  description: string;
  price_monthly_cents: number;
  price_yearly_cents?: number;
  stripe_price_id_monthly: string;
  stripe_price_id_yearly?: string;
  features: string[];
  is_active: boolean;
}

interface CurrentSubscription {
  plan_name: string;
  plan_description: string;
  status: string;
  current_period_end?: string;
  cancel_at_period_end: boolean;
  features: string[];
  billing_cycle: string;
  amount: number;
}

// Simple Icon Components
const CheckIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="currentColor" viewBox="0 0 20 20">
    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
  </svg>
);

const CrownIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="currentColor" viewBox="0 0 20 20">
    <path d="M5 4a1 1 0 00-2 0v7H2a2 2 0 002 2h12a2 2 0 002-2h-1V4a1 1 0 10-2 0v7h-3V4a1 1 0 10-2 0v7H8V4z" />
  </svg>
);

const ZapIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="currentColor" viewBox="0 0 20 20">
    <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
  </svg>
);

const UsersIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="currentColor" viewBox="0 0 20 20">
    <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
  </svg>
);

export default function PricingPlans() {
  const [plans, setPlans] = useState<PricingPlan[]>([]);
  const [currentSubscription, setCurrentSubscription] = useState<CurrentSubscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');
  const [subscribing, setSubscribing] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [user, setUser] = useState<any>(null);

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
  const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";
  const supabase = supabaseUrl && supabaseKey ? createClient(supabaseUrl, supabaseKey) : null;

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    if (!supabase) {
      setLoading(false);
      return;
    }

    try {
      // Check if user is authenticated
      const { data: { user } } = await supabase.auth.getUser();
      setUser(user);

      // Load pricing plans
      const plansResponse = await fetch("/api/pricing/plans");
      if (plansResponse.ok) {
        const plansData = await plansResponse.json();
        setPlans(plansData);
      }

      // Load current subscription if user is authenticated
      if (user) {
        const token = await supabase.auth.getSession();
        if (token.data.session) {
          const subscriptionResponse = await fetch("/api/pricing/current-subscription", {
            headers: {
              'Authorization': `Bearer ${token.data.session.access_token}`
            }
          });
          if (subscriptionResponse.ok) {
            const subscriptionData = await subscriptionResponse.json();
            setCurrentSubscription(subscriptionData);
          }
        }
      }
    } catch (error) {
      console.error("Error loading data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async (plan: PricingPlan) => {
    if (!user || !supabase) {
      setMessage("Please sign in to subscribe to a plan");
      return;
    }

    setSubscribing(plan.id);
    setMessage("");

    try {
      const token = await supabase.auth.getSession();
      if (!token.data.session) {
        throw new Error("No active session");
      }

      const requestBody = {
        plan_id: plan.id,
        billing_cycle: billingCycle
      };

      const response = await fetch("/api/pricing/subscribe", {
        method: "POST",
        headers: {
          'Authorization': `Bearer ${token.data.session.access_token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to create subscription");
      }

      // In a real implementation, you would redirect to Stripe Checkout or use Stripe Elements
      setMessage(`Successfully subscribed to ${plan.name}! Subscription ID: ${data.subscription_id}`);

      // Refresh current subscription
      await loadData();

    } catch (error: any) {
      setMessage(error.message || "Failed to subscribe to plan");
    } finally {
      setSubscribing(null);
    }
  };

  const formatPrice = (cents: number) => {
    return (cents / 100).toFixed(2);
  };

  const formatCurrency = (cents: number) => {
    return `$${formatPrice(cents)}`;
  };

  const getPlanIcon = (planName: string) => {
    switch (planName.toLowerCase()) {
      case 'basic':
        return <ZapIcon className="w-8 h-8" />;
      case 'premium':
        return <CrownIcon className="w-8 h-8" />;
      default:
        return <UsersIcon className="w-8 h-8" />;
    }
  };

  const isCurrentPlan = (planName: string) => {
    if (!currentSubscription) return false;
    return currentSubscription.plan_name.toLowerCase() === planName.toLowerCase();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="animate-pulse">
              <div className="h-8 bg-gray-200 rounded w-1/3 mx-auto mb-4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2 mx-auto"></div>
            </div>
            <div className="mt-12 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="bg-white p-8 rounded-lg shadow-lg">
                  <div className="animate-pulse">
                    <div className="h-6 bg-gray-200 rounded w-3/4 mb-4"></div>
                    <div className="h-8 bg-gray-200 rounded w-1/2 mb-6"></div>
                    <div className="space-y-2">
                      {[...Array(5)].map((_, j) => (
                        <div key={j} className="h-4 bg-gray-200 rounded w-full"></div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Choose Your Plan
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Unlock the full power of AI-powered menu analysis
          </p>

          {/* Billing Cycle Toggle */}
          <div className="inline-flex rounded-lg bg-gray-100 p-1">
            <button
              onClick={() => setBillingCycle('monthly')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition ${
                billingCycle === 'monthly'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingCycle('yearly')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition ${
                billingCycle === 'yearly'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Yearly
              <span className="ml-2 px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                Save 20%
              </span>
            </button>
          </div>
        </div>

        {/* Current Plan Status */}
        {currentSubscription && (
          <div className="mb-12 bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-900 mb-2">Current Plan</h3>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-800 font-medium">{currentSubscription.plan_name}</p>
                <p className="text-sm text-blue-600">{currentSubscription.plan_description}</p>
                <p className="text-sm text-blue-600 mt-1">
                  Status: <span className="font-medium">{currentSubscription.status}</span>
                  {currentSubscription.cancel_at_period_end && (
                    <span className="ml-2 text-orange-600">(Cancels at end of period)</span>
                  )}
                </p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-blue-900">
                  {formatCurrency(currentSubscription.amount * 100)}
                </p>
                <p className="text-sm text-blue-600">per {currentSubscription.billing_cycle}</p>
              </div>
            </div>
          </div>
        )}

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {plans.map((plan) => {
            const isCurrent = isCurrentPlan(plan.name);
            const price = billingCycle === 'yearly' && plan.price_yearly_cents 
              ? plan.price_yearly_cents / 12 
              : plan.price_monthly_cents;
            
            return (
              <div
                key={plan.id}
                className={`relative bg-white rounded-2xl shadow-lg overflow-hidden transform hover:scale-105 transition duration-200 ${
                  plan.name.toLowerCase() === 'premium' 
                    ? 'ring-2 ring-blue-500 border-2 border-blue-500' 
                    : ''
                }`}
              >
                {plan.name.toLowerCase() === 'premium' && (
                  <div className="absolute top-0 right-0 bg-blue-500 text-white px-3 py-1 text-sm font-medium rounded-bl-lg">
                    Most Popular
                  </div>
                )}

                <div className="p-8">
                  {/* Plan Header */}
                  <div className="text-center mb-8">
                    <div className="flex justify-center mb-4">
                      <div className={`p-3 rounded-full ${
                        plan.name.toLowerCase() === 'premium' 
                          ? 'bg-blue-100 text-blue-600' 
                          : 'bg-gray-100 text-gray-600'
                      }`}>
                        {getPlanIcon(plan.name)}
                      </div>
                    </div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                    <p className="text-gray-600 mb-6">{plan.description}</p>
                    
                    {/* Price */}
                    <div className="mb-6">
                      <span className="text-4xl font-bold text-gray-900">
                        {formatCurrency(price)}
                      </span>
                      <span className="text-gray-500 ml-2">/month</span>
                      {billingCycle === 'yearly' && plan.price_yearly_cents && (
                        <p className="text-sm text-green-600 mt-1">
                          Save {formatCurrency((plan.price_monthly_cents - price) * 12)} per year
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Features */}
                  <ul className="space-y-4 mb-8">
                    {plan.features.map((feature, index) => (
                      <li key={index} className="flex items-center">
                        <CheckIcon className="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
                        <span className="text-gray-700">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  {/* Subscribe Button */}
                  <button
                    onClick={() => handleSubscribe(plan)}
                    disabled={subscribing === plan.id || isCurrent}
                    className={`w-full py-3 px-4 rounded-lg font-semibold transition ${
                      isCurrent
                        ? 'bg-green-100 text-green-800 cursor-not-allowed'
                        : plan.name.toLowerCase() === 'premium'
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'bg-gray-900 text-white hover:bg-gray-800'
                    } ${subscribing === plan.id ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    {subscribing === plan.id
                      ? 'Processing...'
                      : isCurrent
                      ? 'Current Plan'
                      : `Subscribe to ${plan.name}`
                    }
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Referral Program */}
        <div className="mt-16 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 text-white text-center">
          <h3 className="text-2xl font-bold mb-4">Refer Friends & Earn Rewards</h3>
          <p className="text-lg mb-6">
            Share your unique referral link and earn 1 month free for each friend who subscribes!
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <div className="bg-white/10 rounded-lg p-4 flex-1 max-w-md">
              <p className="text-sm text-blue-100">Your referral link</p>
              <p className="font-mono text-sm">
                {user ? `${window.location.origin}/signup?ref=YOUR_CODE` : 'Sign in to get your referral link'}
              </p>
            </div>
            <button 
              className="bg-white text-blue-600 px-6 py-3 rounded-lg font-semibold hover:bg-blue-50 transition"
              disabled={!user}
            >
              {user ? 'Copy Link' : 'Sign In Required'}
            </button>
          </div>
        </div>

        {/* FAQ Section */}
        <div className="mt-16">
          <h3 className="text-2xl font-bold text-center text-gray-900 mb-8">
            Frequently Asked Questions
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-white p-6 rounded-lg shadow">
              <h4 className="font-semibold text-gray-900 mb-2">Can I cancel anytime?</h4>
              <p className="text-gray-600">
                Yes, you can cancel your subscription at any time. You'll continue to have access until the end of your billing period.
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h4 className="font-semibold text-gray-900 mb-2">Is there a free trial?</h4>
              <p className="text-gray-600">
                Yes! New users get 7 days free access to all Premium features. No credit card required.
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h4 className="font-semibold text-gray-900 mb-2">What payment methods do you accept?</h4>
              <p className="text-gray-600">
                We accept all major credit cards, debit cards, and digital wallets through our secure payment processor.
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h4 className="font-semibold text-gray-900 mb-2">Need a custom plan?</h4>
              <p className="text-gray-600">
                Contact our sales team for enterprise plans with custom pricing and features tailored to your needs.
              </p>
            </div>
          </div>
        </div>

        {/* Message Display */}
        {message && (
          <div className={`mt-8 p-4 rounded-lg ${
            message.includes('success') || message.includes('Successfully')
              ? 'bg-green-50 border border-green-200 text-green-800'
              : 'bg-red-50 border border-red-200 text-red-800'
          }`}>
            {message}
          </div>
        )}
      </div>
    </div>
  );
}