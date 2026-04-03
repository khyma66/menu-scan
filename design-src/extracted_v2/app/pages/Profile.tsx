import { useState, useId, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  CreditCard, ClipboardList, Star, Lock, LogOut, Trash2,
  ChevronRight, Edit3, Camera, Bell, Shield, Award, TrendingUp,
  Save, Check, User, Mail, Phone, Globe, KeyRound,
} from "lucide-react";

// ── Stylish Floating-Label Input ───────────────────────────────────────────
function FloatInput({
  label,
  value,
  onChange,
  type = "text",
  disabled = false,
  icon: Icon,
  iconColor = "#3B5BDB",
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  disabled?: boolean;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  iconColor?: string;
}) {
  const [focused, setFocused] = useState(false);
  const id = useId();
  const lifted = focused || value.length > 0;

  return (
    <motion.div
      animate={focused
        ? { boxShadow: `0 0 0 2px ${iconColor}40`, borderColor: iconColor }
        : { boxShadow: "0 0 0 0 transparent", borderColor: "#E5E7EB" }
      }
      transition={{ duration: 0.2 }}
      className="relative rounded-2xl border-2 bg-white overflow-hidden"
      style={{ borderColor: focused ? iconColor : "#E5E7EB" }}
    >
      {/* Left icon strip */}
      <div
        className="absolute left-0 top-0 bottom-0 w-11 flex items-center justify-center transition-all duration-200"
        style={{ backgroundColor: focused ? iconColor + "12" : "#F9FAFB" }}
      >
        <motion.div animate={{ color: focused ? iconColor : "#9CA3AF" }} transition={{ duration: 0.2 }}>
          <Icon size={16} />
        </motion.div>
      </div>

      {/* Divider line */}
      <motion.div
        className="absolute left-11 top-3 bottom-3 w-px"
        animate={{ backgroundColor: focused ? iconColor + "60" : "#E5E7EB" }}
        transition={{ duration: 0.2 }}
      />

      {/* Floating label */}
      <motion.label
        htmlFor={id}
        animate={lifted
          ? { y: -9, scale: 0.75, color: disabled ? "#9CA3AF" : iconColor, x: 0 }
          : { y: 0, scale: 1, color: "#9CA3AF", x: 0 }
        }
        transition={{ type: "spring", stiffness: 300, damping: 25 }}
        style={{ transformOrigin: "left center", originX: 0 }}
        className="absolute left-14 top-1/2 -translate-y-1/2 pointer-events-none text-sm"
      >
        {label}
      </motion.label>

      <input
        id={id}
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        disabled={disabled}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        className="w-full pl-14 pr-4 pt-5 pb-2 bg-transparent outline-none text-sm text-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
      />

      {/* Bottom fill bar */}
      <motion.div
        className="absolute bottom-0 left-11 right-0 h-0.5 rounded-full"
        animate={{ scaleX: focused ? 1 : 0, backgroundColor: iconColor }}
        transition={{ duration: 0.25 }}
        style={{ transformOrigin: "left" }}
      />
    </motion.div>
  );
}

// ── Menu Row ───────────────────────────────────────────────────────────────
const MENU_ITEMS = [
  { id: "details", label: "Account Details", color: "#3B5BDB", emoji: "👤" },
  { id: "payment", label: "Payment Methods", color: "#22C55E", emoji: "💳" },
  { id: "scans", label: "Recent Scans", color: "#8B5CF6", emoji: "📋", badge: "3 New" },
  { id: "subscription", label: "Subscription", color: "#F59E0B", emoji: "⭐", badge: "Pro" },
  { id: "notifications", label: "Notifications", color: "#EC4899", emoji: "🔔" },
  { id: "security", label: "Privacy & Security", color: "#06B6D4", emoji: "🔒" },
  { id: "password", label: "Reset Password", color: "#6B7280", emoji: "🔑" },
];

const DANGER_ITEMS = [
  { id: "logout", label: "Logout", color: "#EF4444", emoji: "🚪" },
  { id: "delete", label: "Delete Account", color: "#DC2626", emoji: "🗑️" },
];

const STATS = [
  { value: "47", label: "Scans", icon: "📸", color: "#3B5BDB" },
  { value: "12", label: "Saved", icon: "❤️", color: "#EF4444" },
  { value: "4.8", label: "Avg Score", icon: "⭐", color: "#F59E0B" },
];

type AnyItem = { id: string; label: string; color: string; emoji: string; badge?: string };

function MenuItem({
  item,
  onClick,
  danger = false,
  active = false,
}: {
  item: AnyItem;
  onClick: () => void;
  danger?: boolean;
  active?: boolean;
}) {
  return (
    <motion.button
      whileTap={{ scale: 0.97 }}
      onClick={onClick}
      className="w-full flex items-center gap-3 px-4 py-3.5 rounded-2xl transition-colors group"
      animate={{
        backgroundColor: active
          ? item.color + "12"
          : danger
          ? "#FFF5F5"
          : "#F8F9FF",
        borderColor: active ? item.color + "30" : "transparent",
      }}
      style={{ border: "1.5px solid transparent" }}
    >
      <motion.div
        className="w-9 h-9 rounded-xl flex items-center justify-center text-base flex-shrink-0"
        style={{ backgroundColor: item.color + "18" }}
        animate={active ? { rotate: [0, -8, 8, 0], scale: [1, 1.1, 1] } : {}}
        transition={{ duration: 0.4 }}
      >
        {item.emoji}
      </motion.div>
      <span
        className="flex-1 text-left text-sm"
        style={{
          color: danger ? item.color : active ? item.color : "#374151",
          fontWeight: active ? 600 : 500,
        }}
      >
        {item.label}
      </span>
      {item.badge && (
        <span
          className="text-xs px-2.5 py-0.5 rounded-full font-semibold mr-1"
          style={{ backgroundColor: item.color + "18", color: item.color }}
        >
          {item.badge}
        </span>
      )}
      <motion.div
        animate={{ x: active ? 2 : 0, color: active ? item.color : "#D1D5DB" }}
        transition={{ duration: 0.2 }}
      >
        <motion.div animate={{ rotate: active ? 90 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronRight size={16} />
        </motion.div>
      </motion.div>
    </motion.button>
  );
}

// ── Account Details expanded panel ─────────────────────────────────────────
function AccountDetailsPanel() {
  const [name, setName] = useState("Alex Johnson");
  const [email] = useState("alex@example.com");
  const [phone, setPhone] = useState("+1 202 555 0104");
  const [country, setCountry] = useState("United States");
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2200);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mt-1 mx-1 bg-white rounded-2xl shadow-sm overflow-hidden"
      style={{ border: "1.5px solid rgba(59,91,219,0.12)" }}
    >
      {/* Gradient top stripe */}
      <div
        className="h-1 w-full"
        style={{ background: "linear-gradient(90deg, #7C3AED, #06B6D4, #2563EB)" }}
      />

      <div className="p-4 space-y-3">
        <FloatInput label="Full Name" value={name} onChange={setName} icon={User} iconColor="#3B5BDB" />
        <FloatInput label="Email Address" value={email} onChange={() => {}} type="email" disabled icon={Mail} iconColor="#8B5CF6" />
        <FloatInput label="Phone Number" value={phone} onChange={setPhone} type="tel" icon={Phone} iconColor="#22C55E" />
        <FloatInput label="Country" value={country} onChange={setCountry} icon={Globe} iconColor="#06B6D4" />
      </div>

      <div className="px-4 pb-4">
        <motion.button
          whileTap={{ scale: 0.97 }}
          onClick={handleSave}
          className="w-full py-3.5 rounded-2xl font-bold text-white relative overflow-hidden"
          style={{
            background: saved
              ? "linear-gradient(135deg, #22C55E, #16A34A)"
              : "linear-gradient(135deg, #3B5BDB, #2563EB)",
          }}
        >
          {/* Shimmer */}
          <motion.div
            className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
            animate={{ x: ["-100%", "200%"] }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear", repeatDelay: 1 }}
          />
          <AnimatePresence mode="wait">
            {saved ? (
              <motion.div
                key="saved"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                className="flex items-center justify-center gap-2 relative z-10"
              >
                <Check size={17} />
                Saved Successfully!
              </motion.div>
            ) : (
              <motion.div
                key="save"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex items-center justify-center gap-2 relative z-10"
              >
                <Save size={17} />
                Save Details
              </motion.div>
            )}
          </AnimatePresence>
        </motion.button>
      </div>
    </motion.div>
  );
}

// ── PASSWORD PANEL ─────────────────────────────────────────────────────────
function PasswordPanel() {
  const [current, setCurrent] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirm, setConfirm] = useState("");
  const [saved, setSaved] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mt-1 mx-1 bg-white rounded-2xl shadow-sm overflow-hidden"
      style={{ border: "1.5px solid rgba(107,114,128,0.15)" }}
    >
      <div className="h-1 w-full" style={{ background: "linear-gradient(90deg, #6B7280, #374151)" }} />
      <div className="p-4 space-y-3">
        <FloatInput label="Current Password" value={current} onChange={setCurrent} type="password" icon={KeyRound} iconColor="#6B7280" />
        <FloatInput label="New Password" value={newPw} onChange={setNewPw} type="password" icon={Lock} iconColor="#3B5BDB" />
        <FloatInput label="Confirm Password" value={confirm} onChange={setConfirm} type="password" icon={Shield} iconColor="#22C55E" />
      </div>
      <div className="px-4 pb-4">
        <motion.button
          whileTap={{ scale: 0.97 }}
          onClick={() => { setSaved(true); setTimeout(() => setSaved(false), 2000); }}
          className="w-full py-3.5 rounded-2xl font-bold text-white"
          style={{ background: saved ? "linear-gradient(135deg,#22C55E,#16A34A)" : "linear-gradient(135deg,#6B7280,#374151)" }}
        >
          <AnimatePresence mode="wait">
            {saved ? (
              <motion.div key="ok" initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }} className="flex items-center justify-center gap-2">
                <Check size={17} /> Password Updated!
              </motion.div>
            ) : (
              <motion.div key="upd" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex items-center justify-center gap-2">
                <KeyRound size={17} /> Update Password
              </motion.div>
            )}
          </AnimatePresence>
        </motion.button>
      </div>
    </motion.div>
  );
}

// ── Subscription Plans ──────────────────────────────────────────────────────
const SUBSCRIPTION_PLANS = [
  {
    id: "free",
    name: "Free",
    emoji: "🍃",
    badge: null,
    badgeBg: "",
    badgeText: "",
    price: "$0",
    period: "/mo",
    priceColor: "#6B7280",
    borderColor: "#D1D5DB",
    glowColor: "rgba(209,213,219,0.7)",
    bgFrom: "#F9FAFB",
    bgTo: "#F3F4F6",
    checkBg: "#E5E7EB",
    checkColor: "#6B7280",
    btnBg: "linear-gradient(135deg, #9CA3AF, #6B7280)",
    isCurrent: true,
    features: [
      "3 menu scans per day",
      "Basic dish translation",
      "Restaurant discovery",
    ],
  },
  {
    id: "pro",
    name: "Pro",
    emoji: "⭐",
    badge: "Most Popular",
    badgeBg: "#DBEAFE",
    badgeText: "#1D4ED8",
    price: "$6.99",
    period: "/mo",
    priceColor: "#2563EB",
    borderColor: "#93C5FD",
    glowColor: "rgba(147,197,253,0.55)",
    bgFrom: "#EFF6FF",
    bgTo: "#DBEAFE",
    checkBg: "#BFDBFE",
    checkColor: "#1D4ED8",
    btnBg: "linear-gradient(135deg, #3B5BDB, #2563EB)",
    isCurrent: false,
    features: [
      "Unlimited menu scans",
      "Full ingredient details",
      "Similar dish suggestions",
      "Allergen warnings",
    ],
  },
  {
    id: "max",
    name: "Max",
    emoji: "💎",
    badge: "Best Value",
    badgeBg: "#EDE9FE",
    badgeText: "#6D28D9",
    price: "$9.99",
    period: "/mo",
    priceColor: "#7C3AED",
    borderColor: "#C4B5FD",
    glowColor: "rgba(196,181,253,0.55)",
    bgFrom: "#F5F3FF",
    bgTo: "#EDE9FE",
    checkBg: "#DDD6FE",
    checkColor: "#6D28D9",
    btnBg: "linear-gradient(135deg, #7C3AED, #6D28D9)",
    isCurrent: false,
    features: [
      "Everything in Pro",
      "Personalized recommendations",
      "Priority support",
      "Advanced health analysis",
    ],
  },
];

// ── Subscription Panel ──────────────────────────────────────────────────────
function SubscriptionPanel() {
  const [activeIdx, setActiveIdx] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);

  const scrollToCard = useCallback((i: number) => {
    if (!scrollRef.current) return;
    const container = scrollRef.current;
    const card = container.children[i] as HTMLElement;
    if (!card) return;
    const containerCenter = container.clientWidth / 2;
    const cardCenter = card.offsetLeft + card.offsetWidth / 2;
    container.scrollTo({ left: cardCenter - containerCenter, behavior: "smooth" });
  }, []);

  const handleScroll = useCallback(() => {
    if (!scrollRef.current) return;
    const { scrollLeft, clientWidth } = scrollRef.current;
    const center = scrollLeft + clientWidth / 2;
    let closest = 0;
    let minDist = Infinity;
    Array.from(scrollRef.current.children).forEach((child, i) => {
      const el = child as HTMLElement;
      const childCenter = el.offsetLeft + el.offsetWidth / 2;
      const dist = Math.abs(childCenter - center);
      if (dist < minDist) { minDist = dist; closest = i; }
    });
    setActiveIdx(closest);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mt-1 mx-1 bg-white rounded-2xl shadow-sm overflow-hidden"
      style={{ border: "1.5px solid rgba(245,158,11,0.18)" }}
    >
      {/* Rainbow stripe */}
      <div className="h-1 w-full" style={{ background: "linear-gradient(90deg, #6B7280 0%, #3B82F6 50%, #7C3AED 100%)" }} />

      {/* Header */}
      <div className="pt-4 px-4 pb-3">
        <p className="font-bold text-gray-800" style={{ fontSize: "15px" }}>Your Plan</p>
        <p className="text-xs text-gray-400 mt-0.5">Select a plan that fits your needs</p>
      </div>

      {/* ── Sliding cards ── */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex overflow-x-auto"
        style={{
          scrollSnapType: "x mandatory",
          WebkitOverflowScrolling: "touch",
          scrollbarWidth: "none",
          msOverflowStyle: "none",
          gap: 12,
          paddingInline: "11%",
          paddingBottom: 16,
        }}
      >
        {SUBSCRIPTION_PLANS.map((plan, i) => {
          const isActive = activeIdx === i;
          return (
            <motion.div
              key={plan.id}
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08 }}
              className="flex-shrink-0 rounded-2xl overflow-hidden"
              style={{
                minWidth: "78%",
                scrollSnapAlign: "center",
                border: `1.5px solid ${plan.borderColor}`,
                boxShadow: isActive
                  ? `0 8px 28px ${plan.glowColor}`
                  : "0 2px 8px rgba(0,0,0,0.04)",
                transition: "box-shadow 0.35s ease",
              }}
            >
              {/* Card hero: gradient background */}
              <div
                className="px-4 pt-4 pb-3"
                style={{ background: `linear-gradient(150deg, ${plan.bgFrom}, ${plan.bgTo})` }}
              >
                <div className="flex items-start justify-between">
                  {/* Left: icon + name + badge */}
                  <div>
                    <div className="flex items-center gap-2">
                      <span style={{ fontSize: "26px", lineHeight: 1 }}>{plan.emoji}</span>
                      <span style={{ fontWeight: 800, fontSize: "20px", color: "#111827" }}>{plan.name}</span>
                    </div>
                    {plan.badge && (
                      <motion.span
                        initial={{ scale: 0, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ delay: 0.18 + i * 0.09, type: "spring", stiffness: 260 }}
                        className="inline-block mt-2 text-xs px-2.5 py-0.5 rounded-full font-bold"
                        style={{ backgroundColor: plan.badgeBg, color: plan.badgeText }}
                      >
                        {plan.badge}
                      </motion.span>
                    )}
                  </div>
                  {/* Right: price */}
                  <div className="text-right pt-0.5">
                    <span style={{ fontWeight: 900, fontSize: "24px", color: plan.priceColor, lineHeight: 1 }}>
                      {plan.price}
                    </span>
                    <span className="block text-xs text-gray-400 mt-0.5">{plan.period}</span>
                  </div>
                </div>
              </div>

              {/* Thin divider */}
              <div style={{ height: "1px", backgroundColor: plan.borderColor, opacity: 0.7 }} />

              {/* Features list */}
              <div className="px-4 py-3 space-y-2.5 bg-white">
                {plan.features.map((feat, fi) => (
                  <motion.div
                    key={feat}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 + fi * 0.055 }}
                    className="flex items-center gap-2.5"
                  >
                    <div
                      className="w-[18px] h-[18px] rounded-full flex items-center justify-center flex-shrink-0"
                      style={{ backgroundColor: plan.checkBg }}
                    >
                      <Check size={10} style={{ color: plan.checkColor }} />
                    </div>
                    <span className="text-xs text-gray-600">{feat}</span>
                  </motion.div>
                ))}
              </div>

              {/* CTA button */}
              <div className="px-4 pb-4 pt-1 bg-white">
                <motion.button
                  whileTap={{ scale: 0.97 }}
                  className="w-full py-3 rounded-2xl font-bold text-white text-sm relative overflow-hidden"
                  style={{ background: plan.btnBg }}
                >
                  {!plan.isCurrent && (
                    <motion.div
                      className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
                      animate={{ x: ["-100%", "200%"] }}
                      transition={{ duration: 2.5, repeat: Infinity, ease: "linear", repeatDelay: 1.5 }}
                    />
                  )}
                  <span className="relative z-10">
                    {plan.isCurrent ? "✓  Current Plan" : `Upgrade to ${plan.name}`}
                  </span>
                </motion.button>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* ── Dot indicators ── */}
      <div className="flex items-center justify-center gap-2 pb-4">
        {SUBSCRIPTION_PLANS.map((plan, i) => (
          <motion.button
            key={plan.id}
            onClick={() => scrollToCard(i)}
            animate={{
              width: activeIdx === i ? 22 : 6,
              backgroundColor: activeIdx === i ? plan.priceColor : "#D1D5DB",
              opacity: activeIdx === i ? 1 : 0.45,
            }}
            style={{ height: 6, borderRadius: 3, cursor: "pointer", flexShrink: 0 }}
            transition={{ duration: 0.22, ease: "easeOut" }}
          />
        ))}
      </div>
    </motion.div>
  );
}

// ── PROFILE PAGE ───────────────────────────────────────────────────────────
export function Profile() {
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleMenuClick = (id: string) => {
    if (id === "delete") { setShowDeleteConfirm(true); return; }
    if (id === "logout") return;
    setActiveSection(prev => prev === id ? null : id);
  };

  return (
    <div className="flex flex-col min-h-full bg-gray-50">

      {/* ── Hero Header (matches other tabs) ──────────────────────────── */}
      <div
        className="relative px-5 pt-7 pb-8 overflow-hidden"
        style={{ backgroundColor: "#EC4899" }}
      >
        {/* Decorative circles */}
        <div className="absolute -top-8 -right-8 w-32 h-32 rounded-full bg-white/10" />
        <div className="absolute top-4 -right-4 w-20 h-20 rounded-full bg-white/5" />
        <div className="absolute -bottom-6 -left-6 w-24 h-24 rounded-full bg-white/10" />

        <motion.div
          initial={{ opacity: 0, scale: 0.85 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex flex-col items-center"
        >
          {/* Avatar */}
          <div className="relative mb-3">
            <motion.div
              whileTap={{ scale: 0.96 }}
              className="w-20 h-20 rounded-full flex items-center justify-center text-4xl shadow-xl"
              style={{ background: "rgba(255,255,255,0.18)", border: "2.5px solid rgba(255,255,255,0.45)" }}
            >
              👨‍💼
            </motion.div>
            <motion.button
              whileTap={{ scale: 0.88 }}
              className="absolute -bottom-1 -right-1 w-7 h-7 bg-white rounded-full flex items-center justify-center shadow-lg"
            >
              <Camera size={13} className="text-blue-600" />
            </motion.button>

            {/* Ring pulse */}
            <motion.div
              className="absolute inset-0 rounded-full"
              style={{ border: "2px solid rgba(255,255,255,0.4)" }}
              animate={{ scale: [1, 1.25, 1.5], opacity: [0.6, 0.3, 0] }}
              transition={{ duration: 2, repeat: Infinity, repeatDelay: 1 }}
            />
          </div>

          <div className="flex items-center gap-2">
            <h2 className="text-white" style={{ fontWeight: 800, fontSize: "20px" }}>Alex Johnson</h2>
            <motion.button
              whileTap={{ scale: 0.88 }}
              className="w-6 h-6 bg-white/20 rounded-full flex items-center justify-center"
            >
              <Edit3 size={11} className="text-white" />
            </motion.button>
          </div>
          <p className="text-white/70 text-sm mt-0.5">alex@example.com</p>

          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="mt-3 flex items-center gap-1.5 px-4 py-1.5 bg-amber-400/90 rounded-full"
          >
            <Award size={12} className="text-amber-900" />
            <span className="text-amber-900 font-bold" style={{ fontSize: "11px" }}>Pro Member</span>
          </motion.div>
        </motion.div>
      </div>

      {/* ── Stats Card ────────────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.08 }}
        className="mx-4 -mt-4 bg-white rounded-2xl shadow-lg p-4 flex items-center justify-around"
      >
        {STATS.map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.12 + i * 0.06 }}
            className="flex flex-col items-center gap-0.5"
          >
            <span className="text-xl">{stat.icon}</span>
            <span className="font-bold" style={{ color: stat.color, fontSize: "15px" }}>{stat.value}</span>
            <span className="text-gray-500" style={{ fontSize: "11px" }}>{stat.label}</span>
          </motion.div>
        ))}
      </motion.div>

      {/* ── Activity Banner ───────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.18 }}
        className="mx-4 mt-3 rounded-2xl p-3.5 flex items-center gap-3 overflow-hidden relative"
        style={{ background: "linear-gradient(135deg, #3B5BDB, #6D28D9)" }}
      >
        <motion.div
          className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/10 to-white/0"
          animate={{ x: ["-100%", "200%"] }}
          transition={{ duration: 3, repeat: Infinity, ease: "linear", repeatDelay: 2 }}
        />
        <div className="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center flex-shrink-0">
          <TrendingUp size={18} className="text-white" />
        </div>
        <div className="flex-1">
          <p className="text-white font-bold" style={{ fontSize: "13px" }}>Great progress this week!</p>
          <p className="text-white/70" style={{ fontSize: "11px" }}>8 dishes scanned with 85+ health score</p>
        </div>
        <span className="text-2xl">🏆</span>
      </motion.div>

      {/* ── Menu Items ────────────────────────────────────────────────── */}
      <div className="mx-4 mt-4">
        <p className="text-gray-400 font-bold mb-2 ml-1" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>ACCOUNT</p>
        <div className="space-y-1.5">
          {MENU_ITEMS.map((item, i) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, x: -16 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.04 * i }}
            >
              <MenuItem
                item={item}
                active={activeSection === item.id}
                onClick={() => handleMenuClick(item.id)}
              />
              <AnimatePresence>
                {item.id === "details" && activeSection === "details" && (
                  <motion.div
                    key="details-panel"
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.32, ease: [0.32, 0.72, 0, 1] }}
                    className="overflow-hidden"
                  >
                    <AccountDetailsPanel />
                  </motion.div>
                )}
                {item.id === "password" && activeSection === "password" && (
                  <motion.div
                    key="password-panel"
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.32, ease: [0.32, 0.72, 0, 1] }}
                    className="overflow-hidden"
                  >
                    <PasswordPanel />
                  </motion.div>
                )}
                {item.id === "subscription" && activeSection === "subscription" && (
                  <motion.div
                    key="subscription-panel"
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.32, ease: [0.32, 0.72, 0, 1] }}
                    className="overflow-hidden"
                  >
                    <SubscriptionPanel />
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>

        <p className="text-gray-400 font-bold mt-4 mb-2 ml-1" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>DANGER ZONE</p>
        <div className="space-y-1.5">
          {DANGER_ITEMS.map((item, i) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, x: -16 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.32 + 0.05 * i }}
            >
              <MenuItem item={item} onClick={() => handleMenuClick(item.id)} danger />
            </motion.div>
          ))}
        </div>

        <div className="mt-6 mb-4 text-center">
          <p className="text-gray-400" style={{ fontSize: "11px" }}>Foodit v2.0.1 • Made with ❤️</p>
        </div>
      </div>

      {/* ── Delete confirm sheet ─────────────────────────────────────── */}
      <AnimatePresence>
        {showDeleteConfirm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/50 backdrop-blur-sm flex items-end justify-center z-50"
            onClick={() => setShowDeleteConfirm(false)}
          >
            <motion.div
              initial={{ y: "100%" }}
              animate={{ y: 0 }}
              exit={{ y: "100%" }}
              transition={{ type: "spring", stiffness: 400, damping: 38 }}
              onClick={e => e.stopPropagation()}
              className="w-full bg-white rounded-t-3xl p-6"
            >
              {/* Handle */}
              <div className="w-10 h-1 bg-gray-200 rounded-full mx-auto mb-5" />
              <div className="text-center mb-6">
                <div className="text-5xl mb-3">🗑️</div>
                <h3 className="font-bold text-gray-900" style={{ fontSize: "18px" }}>Delete Account?</h3>
                <p className="text-gray-500 text-sm mt-2 leading-relaxed">
                  This will permanently delete your account and all your data. This action cannot be undone.
                </p>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  className="flex-1 py-3.5 rounded-2xl border-2 border-gray-100 font-bold text-gray-600"
                >
                  Cancel
                </button>
                <button
                  className="flex-1 py-3.5 rounded-2xl font-bold text-white"
                  style={{ background: "linear-gradient(135deg, #EF4444, #DC2626)" }}
                >
                  Delete
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}