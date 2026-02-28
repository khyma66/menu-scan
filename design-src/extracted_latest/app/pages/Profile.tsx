import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  ChevronRight, Edit3, Camera, Award, TrendingUp, LogOut,
} from "lucide-react";
import {
  ProfilePanel, PaymentPanel, SubscriptionPanel, RecentScansPanel,
  NotificationsPanel, PrivacySecurityPanel, PasswordPanel,
} from "../components/ProfilePanels";
import { getSupabase, getUserId } from "../lib/supabaseClient";

// ── Menu Row Items ─────────────────────────────────────────────────────────
const MENU_ITEMS = [
  { id: "profile", label: "Profile", color: "#3B5BDB", emoji: "👤" },
  { id: "payment", label: "Payment Methods", color: "#22C55E", emoji: "💳" },
  { id: "scans", label: "Recent Scans", color: "#8B5CF6", emoji: "📋", badge: "3 New" },
  { id: "subscription", label: "Subscription", color: "#F59E0B", emoji: "⭐" },
  { id: "notifications", label: "Notifications", color: "#EC4899", emoji: "🔔" },
  { id: "security", label: "Privacy & Security", color: "#06B6D4", emoji: "🔒" },
  { id: "password", label: "Reset Password", color: "#6B7280", emoji: "🔑" },
];

const STATS = [
  { value: "47", label: "Scans", icon: "📸", color: "#3B5BDB" },
  { value: "12", label: "Saved", icon: "❤️", color: "#EF4444" },
  { value: "4.8", label: "Avg Score", icon: "⭐", color: "#F59E0B" },
];

type AnyItem = { id: string; label: string; color: string; emoji: string; badge?: string };

// ── Menu Item Row ──────────────────────────────────────────────────────────
function MenuItem({
  item, onClick, active = false,
}: { item: AnyItem; onClick: () => void; active?: boolean }) {
  return (
    <motion.button whileTap={{ scale: 0.97 }} onClick={onClick}
      className="w-full flex items-center gap-3 px-4 py-3.5 rounded-2xl transition-colors group"
      animate={{
        backgroundColor: active ? item.color + "12" : "#F8F9FF",
        borderColor: active ? item.color + "30" : "transparent",
      }}
      style={{ border: "1.5px solid transparent" }}
    >
      <motion.div className="w-9 h-9 rounded-xl flex items-center justify-center text-base flex-shrink-0"
        style={{ backgroundColor: item.color + "18" }}
        animate={active ? { rotate: [0, -8, 8, 0], scale: [1, 1.1, 1] } : {}}
        transition={{ duration: 0.4 }}>
        {item.emoji}
      </motion.div>
      <span className="flex-1 text-left text-sm"
        style={{ color: active ? item.color : "#374151", fontWeight: active ? 600 : 500 }}>
        {item.label}
      </span>
      {item.badge && (
        <span className="text-xs px-2.5 py-0.5 rounded-full font-semibold mr-1"
          style={{ backgroundColor: item.color + "18", color: item.color }}>
          {item.badge}
        </span>
      )}
      <motion.div animate={{ x: active ? 2 : 0, color: active ? item.color : "#D1D5DB" }}
        transition={{ duration: 0.2 }}>
        <motion.div animate={{ rotate: active ? 90 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronRight size={16} />
        </motion.div>
      </motion.div>
    </motion.button>
  );
}

/* ── Panel expander that renders the correct panel for each section ─────── */
function PanelExpander({ id }: { id: string }) {
  const panels: Record<string, React.ReactNode> = {
    profile: <ProfilePanel />,
    payment: <PaymentPanel />,
    scans: <RecentScansPanel />,
    subscription: <SubscriptionPanel />,
    notifications: <NotificationsPanel />,
    security: <PrivacySecurityPanel />,
    password: <PasswordPanel />,
  };
  return <>{panels[id] || null}</>;
}

// ── PROFILE PAGE ───────────────────────────────────────────────────────────
export function Profile() {
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [subscriptionPlan, setSubscriptionPlan] = useState<string>("free");
  const [userName, setUserName] = useState("Alex Johnson");
  const [userEmail, setUserEmail] = useState("alex@example.com");

  // Load subscription plan and user info from Supabase
  useEffect(() => {
    (async () => {
      const sb = getSupabase();
      const uid = await getUserId();
      if (!sb || !uid) return;

      // Load subscription
      const { data: sub } = await sb.from("user_subscriptions").select("plan_name, status")
        .eq("user_id", uid).eq("status", "active").maybeSingle();
      if (sub?.plan_name) setSubscriptionPlan(sub.plan_name.toLowerCase());

      // Load profile
      const { data: profile } = await sb.from("user_profile_details").select("full_name, email")
        .eq("user_id", uid).maybeSingle();
      if (profile) {
        if (profile.full_name) setUserName(profile.full_name);
        if (profile.email) setUserEmail(profile.email);
      }
    })();
  }, []);

  const handleMenuClick = (id: string) => {
    setActiveSection(prev => prev === id ? null : id);
  };

  const handleSignOut = async () => {
    const sb = getSupabase();
    if (sb) await sb.auth.signOut();
    window.location.reload();
  };

  const isPremium = subscriptionPlan === "pro" || subscriptionPlan === "max";
  const badgeConfig = subscriptionPlan === "max"
    ? { emoji: "💎", label: "Max Member", bg: "bg-purple-500/90", textColor: "text-purple-900" }
    : subscriptionPlan === "pro"
      ? { emoji: "⚡", label: "Pro Member", bg: "bg-amber-400/90", textColor: "text-amber-900" }
      : null;

  return (
    <div className="flex flex-col min-h-full bg-gray-50">

      {/* ── Hero Header ──────────────────────────────────────────────── */}
      <div className="relative px-5 pt-7 pb-8 overflow-hidden" style={{ backgroundColor: "#EC4899" }}>
        {/* Decorative circles */}
        <div className="absolute -top-8 -right-8 w-32 h-32 rounded-full bg-white/10" />
        <div className="absolute top-4 -right-4 w-20 h-20 rounded-full bg-white/5" />
        <div className="absolute -bottom-6 -left-6 w-24 h-24 rounded-full bg-white/10" />

        <motion.div initial={{ opacity: 0, scale: 0.85 }} animate={{ opacity: 1, scale: 1 }}
          className="flex flex-col items-center">
          {/* Avatar */}
          <div className="relative mb-3">
            <motion.div whileTap={{ scale: 0.96 }}
              className="w-20 h-20 rounded-full flex items-center justify-center text-4xl shadow-xl"
              style={{ background: "rgba(255,255,255,0.18)", border: "2.5px solid rgba(255,255,255,0.45)" }}>
              👨‍💼
            </motion.div>
            <motion.button whileTap={{ scale: 0.88 }}
              className="absolute -bottom-1 -right-1 w-7 h-7 bg-white rounded-full flex items-center justify-center shadow-lg">
              <Camera size={13} className="text-blue-600" />
            </motion.button>

            {/* Premium diamond overlay on avatar */}
            {isPremium && (
              <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }}
                className="absolute -top-1 -left-1 w-7 h-7 rounded-full flex items-center justify-center shadow-lg"
                style={{
                  background: subscriptionPlan === "max"
                    ? "linear-gradient(135deg, #7C3AED, #6D28D9)"
                    : "linear-gradient(135deg, #F59E0B, #D97706)"
                }}>
                <span className="text-sm">{subscriptionPlan === "max" ? "💎" : "⚡"}</span>
              </motion.div>
            )}

            {/* Ring pulse */}
            <motion.div className="absolute inset-0 rounded-full"
              style={{ border: "2px solid rgba(255,255,255,0.4)" }}
              animate={{ scale: [1, 1.25, 1.5], opacity: [0.6, 0.3, 0] }}
              transition={{ duration: 2, repeat: Infinity, repeatDelay: 1 }} />
          </div>

          <div className="flex items-center gap-2">
            <h2 className="text-white" style={{ fontWeight: 800, fontSize: "20px" }}>{userName}</h2>
            <motion.button whileTap={{ scale: 0.88 }}
              className="w-6 h-6 bg-white/20 rounded-full flex items-center justify-center">
              <Edit3 size={11} className="text-white" />
            </motion.button>
          </div>
          <p className="text-white/70 text-sm mt-0.5">{userEmail}</p>

          {/* Premium Badge */}
          {badgeConfig && (
            <motion.div initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className={`mt-3 flex items-center gap-1.5 px-4 py-1.5 ${badgeConfig.bg} rounded-full`}>
              <Award size={12} className={badgeConfig.textColor} />
              <span className={`${badgeConfig.textColor} font-bold`} style={{ fontSize: "11px" }}>
                {badgeConfig.label}
              </span>
            </motion.div>
          )}
        </motion.div>
      </div>

      {/* ── Stats Card ───────────────────────────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.08 }}
        className="mx-4 -mt-4 bg-white rounded-2xl shadow-lg p-4 flex items-center justify-around">
        {STATS.map((stat, i) => (
          <motion.div key={stat.label} initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.12 + i * 0.06 }} className="flex flex-col items-center gap-0.5">
            <span className="text-xl">{stat.icon}</span>
            <span className="font-bold" style={{ color: stat.color, fontSize: "15px" }}>{stat.value}</span>
            <span className="text-gray-500" style={{ fontSize: "11px" }}>{stat.label}</span>
          </motion.div>
        ))}
      </motion.div>

      {/* ── Activity Banner ──────────────────────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.18 }}
        className="mx-4 mt-3 rounded-2xl p-3.5 flex items-center gap-3 overflow-hidden relative"
        style={{ background: "linear-gradient(135deg, #3B5BDB, #6D28D9)" }}>
        <motion.div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/10 to-white/0"
          animate={{ x: ["-100%", "200%"] }}
          transition={{ duration: 3, repeat: Infinity, ease: "linear", repeatDelay: 2 }} />
        <div className="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center flex-shrink-0">
          <TrendingUp size={18} className="text-white" />
        </div>
        <div className="flex-1">
          <p className="text-white font-bold" style={{ fontSize: "13px" }}>Great progress this week!</p>
          <p className="text-white/70" style={{ fontSize: "11px" }}>8 dishes scanned with 85+ health score</p>
        </div>
        <span className="text-2xl">🏆</span>
      </motion.div>

      {/* ── Menu Items ───────────────────────────────────────────────── */}
      <div className="mx-4 mt-4">
        <p className="text-gray-400 font-bold mb-2 ml-1" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>ACCOUNT</p>
        <div className="space-y-1.5">
          {MENU_ITEMS.map((item, i) => (
            <motion.div key={item.id} initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.04 * i }}>
              <MenuItem item={item} active={activeSection === item.id}
                onClick={() => handleMenuClick(item.id)} />
              <AnimatePresence>
                {activeSection === item.id && (
                  <motion.div key={`${item.id}-panel`}
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.32, ease: [0.32, 0.72, 0, 1] }}
                    className="overflow-hidden">
                    <PanelExpander id={item.id} />
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>

        {/* Sign Out Button (replaces Danger Zone) */}
        <div className="mt-6 mb-4">
          <motion.button whileTap={{ scale: 0.97 }} onClick={handleSignOut}
            className="w-full flex items-center justify-center gap-2 py-3.5 rounded-2xl font-bold text-red-500 transition-colors"
            style={{ backgroundColor: "#FFF5F5", border: "1.5px solid #FEE2E2" }}>
            <LogOut size={16} />
            Sign Out
          </motion.button>
        </div>

        <div className="mt-2 mb-4 text-center">
          <p className="text-gray-400" style={{ fontSize: "11px" }}>Foodit v2.0.1 • Made with ❤️</p>
        </div>
      </div>
    </div>
  );
}