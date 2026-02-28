import { useState, useEffect, useId } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
    User, Mail, Phone, Globe, Save, Check, KeyRound, Lock, Shield,
    CreditCard, Plus, Trash2, Star, Bell, BellOff, Eye, EyeOff,
} from "lucide-react";
import { getSupabase, getUserId } from "../lib/supabaseClient";

/* ── Shared FloatInput (same stylish design) ─────────────────────────────── */
export function FloatInput({
    label, value, onChange, type = "text", disabled = false,
    icon: Icon, iconColor = "#3B5BDB", placeholder,
}: {
    label: string; value: string; onChange: (v: string) => void;
    type?: string; disabled?: boolean;
    icon: React.ComponentType<{ size?: number; className?: string }>;
    iconColor?: string; placeholder?: string;
}) {
    const [focused, setFocused] = useState(false);
    const id = useId();
    const lifted = focused || value.length > 0;

    return (
        <motion.div
            animate={focused
                ? { boxShadow: `0 0 0 2px ${iconColor}40`, borderColor: iconColor }
                : { boxShadow: "0 0 0 0 transparent", borderColor: "#E5E7EB" }}
            transition={{ duration: 0.2 }}
            className="relative rounded-2xl border-2 bg-white overflow-hidden"
            style={{ borderColor: focused ? iconColor : "#E5E7EB" }}
        >
            <div className="absolute left-0 top-0 bottom-0 w-11 flex items-center justify-center transition-all duration-200"
                style={{ backgroundColor: focused ? iconColor + "12" : "#F9FAFB" }}>
                <motion.div animate={{ color: focused ? iconColor : "#9CA3AF" }} transition={{ duration: 0.2 }}>
                    <Icon size={16} />
                </motion.div>
            </div>
            <motion.div className="absolute left-11 top-3 bottom-3 w-px"
                animate={{ backgroundColor: focused ? iconColor + "60" : "#E5E7EB" }} transition={{ duration: 0.2 }} />
            <motion.label htmlFor={id}
                animate={lifted ? { y: -9, scale: 0.75, color: disabled ? "#9CA3AF" : iconColor, x: 0 }
                    : { y: 0, scale: 1, color: "#9CA3AF", x: 0 }}
                transition={{ type: "spring", stiffness: 300, damping: 25 }}
                style={{ transformOrigin: "left center", originX: 0 }}
                className="absolute left-14 top-1/2 -translate-y-1/2 pointer-events-none text-sm"
            >{label}</motion.label>
            <input id={id} type={type} value={value} onChange={e => onChange(e.target.value)}
                disabled={disabled} onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
                placeholder={lifted ? placeholder : undefined}
                className="w-full pl-14 pr-4 pt-5 pb-2 bg-transparent outline-none text-sm text-gray-800 disabled:opacity-50 disabled:cursor-not-allowed" />
            <motion.div className="absolute bottom-0 left-11 right-0 h-0.5 rounded-full"
                animate={{ scaleX: focused ? 1 : 0, backgroundColor: iconColor }}
                transition={{ duration: 0.25 }} style={{ transformOrigin: "left" }} />
        </motion.div>
    );
}

/* ── Save Button reusable ───────────────────────────────────────────────── */
function SaveButton({ saved, onClick, label, gradient }: {
    saved: boolean; onClick: () => void; label: string;
    gradient: string;
}) {
    return (
        <motion.button whileTap={{ scale: 0.97 }} onClick={onClick}
            className="w-full py-3.5 rounded-2xl font-bold text-white relative overflow-hidden"
            style={{ background: saved ? "linear-gradient(135deg, #22C55E, #16A34A)" : gradient }}
        >
            <motion.div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
                animate={{ x: ["-100%", "200%"] }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear", repeatDelay: 1 }} />
            <AnimatePresence mode="wait">
                {saved ? (
                    <motion.div key="saved" initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0 }} className="flex items-center justify-center gap-2 relative z-10">
                        <Check size={17} /> Saved!
                    </motion.div>
                ) : (
                    <motion.div key="save" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }} className="flex items-center justify-center gap-2 relative z-10">
                        <Save size={17} /> {label}
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.button>
    );
}

/* ── Toggle Switch ──────────────────────────────────────────────────────── */
function Toggle({ enabled, onToggle, color = "#3B5BDB" }: {
    enabled: boolean; onToggle: () => void; color?: string;
}) {
    return (
        <motion.button onClick={onToggle} className="relative w-12 h-7 rounded-full flex-shrink-0"
            animate={{ backgroundColor: enabled ? color : "#D1D5DB" }} transition={{ duration: 0.2 }}>
            <motion.div className="absolute top-0.5 w-6 h-6 rounded-full bg-white shadow-md"
                animate={{ left: enabled ? 22 : 2 }} transition={{ type: "spring", stiffness: 400, damping: 25 }} />
        </motion.button>
    );
}

/* ── Panel wrapper ──────────────────────────────────────────────────────── */
function PanelWrap({ borderColor, gradientColors, children }: {
    borderColor: string; gradientColors: string; children: React.ReactNode;
}) {
    return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
            className="mt-1 mx-1 bg-white rounded-2xl shadow-sm overflow-hidden"
            style={{ border: `1.5px solid ${borderColor}` }}>
            <div className="h-1 w-full" style={{ background: gradientColors }} />
            {children}
        </motion.div>
    );
}

/* ═══════════════════════════════════════════════════════════════════════════
   1. PROFILE PANEL
   ═══════════════════════════════════════════════════════════════════════════ */
export function ProfilePanel() {
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [phone, setPhone] = useState("");
    const [country, setCountry] = useState("");
    const [saved, setSaved] = useState(false);
    const [loaded, setLoaded] = useState(false);

    useEffect(() => {
        (async () => {
            const sb = getSupabase(); const uid = await getUserId();
            if (!sb || !uid) return;
            const { data } = await sb.from("user_profile_details").select("*").eq("user_id", uid).maybeSingle();
            if (data) {
                setName(data.full_name || ""); setEmail(data.email || "");
                setPhone(data.phone || ""); setCountry(data.country || "");
            }
            setLoaded(true);
        })();
    }, []);

    const handleSave = async () => {
        const sb = getSupabase(); const uid = await getUserId();
        if (sb && uid) {
            await sb.from("user_profile_details").upsert({
                user_id: uid, full_name: name, email, phone, country,
            }, { onConflict: "user_id" });
        }
        setSaved(true); setTimeout(() => setSaved(false), 2200);
    };

    return (
        <PanelWrap borderColor="rgba(59,91,219,0.12)" gradientColors="linear-gradient(90deg, #7C3AED, #06B6D4, #2563EB)">
            <div className="p-4 space-y-3">
                <FloatInput label="Full Name" value={name} onChange={setName} icon={User} iconColor="#3B5BDB" />
                <FloatInput label="Email Address" value={email} onChange={setEmail} type="email" icon={Mail} iconColor="#8B5CF6" disabled />
                <FloatInput label="Phone Number" value={phone} onChange={setPhone} type="tel" icon={Phone} iconColor="#22C55E" />
                <FloatInput label="Country" value={country} onChange={setCountry} icon={Globe} iconColor="#06B6D4" />
            </div>
            <div className="px-4 pb-4">
                <SaveButton saved={saved} onClick={handleSave} label="Save Profile" gradient="linear-gradient(135deg, #3B5BDB, #2563EB)" />
            </div>
        </PanelWrap>
    );
}

/* ═══════════════════════════════════════════════════════════════════════════
   2. PAYMENT PANEL
   ═══════════════════════════════════════════════════════════════════════════ */
export function PaymentPanel() {
    const [cards, setCards] = useState<any[]>([]);
    const [showAdd, setShowAdd] = useState(false);
    const [cardNum, setCardNum] = useState("");
    const [expiry, setExpiry] = useState("");
    const [cvv, setCvv] = useState("");
    const [holderName, setHolderName] = useState("");
    const [saved, setSaved] = useState(false);

    useEffect(() => { loadCards(); }, []);

    const loadCards = async () => {
        const sb = getSupabase(); const uid = await getUserId();
        if (!sb || !uid) return;
        const { data } = await sb.from("user_saved_cards").select("*").eq("user_id", uid).order("created_at", { ascending: false });
        if (data) setCards(data);
    };

    const handleAddCard = async () => {
        const sb = getSupabase(); const uid = await getUserId();
        if (!sb || !uid || cardNum.length < 4) return;
        const last4 = cardNum.replace(/\s/g, "").slice(-4);
        const brand = cardNum.startsWith("4") ? "Visa" : cardNum.startsWith("5") ? "Mastercard" : "Card";
        const [mm, yy] = expiry.split("/");
        await sb.from("user_saved_cards").insert({
            user_id: uid, card_holder_name: holderName, card_brand: brand,
            card_last4: last4, expiry_month: parseInt(mm) || 0, expiry_year: parseInt("20" + (yy || "00")),
            is_default: cards.length === 0,
        });
        setCardNum(""); setExpiry(""); setCvv(""); setHolderName("");
        setSaved(true); setTimeout(() => { setSaved(false); setShowAdd(false); }, 1500);
        await loadCards();
    };

    const deleteCard = async (id: string) => {
        const sb = getSupabase();
        if (!sb) return;
        await sb.from("user_saved_cards").delete().eq("id", id);
        await loadCards();
    };

    const brandEmoji: Record<string, string> = { Visa: "💳", Mastercard: "💳", Card: "💳" };

    return (
        <PanelWrap borderColor="rgba(34,197,94,0.15)" gradientColors="linear-gradient(90deg, #22C55E, #16A34A)">
            <div className="p-4">
                {cards.length === 0 && !showAdd && (
                    <p className="text-gray-400 text-sm text-center py-3">No saved cards yet</p>
                )}
                {cards.map(c => (
                    <div key={c.id} className="flex items-center gap-3 py-3 border-b border-gray-100 last:border-0">
                        <div className="w-10 h-10 rounded-xl flex items-center justify-center text-lg"
                            style={{ backgroundColor: "#22C55E18" }}>{brandEmoji[c.card_brand] || "💳"}</div>
                        <div className="flex-1">
                            <p className="text-sm font-semibold text-gray-800">{c.card_brand} •••• {c.card_last4}</p>
                            <p className="text-xs text-gray-400">Expires {c.expiry_month}/{c.expiry_year}</p>
                        </div>
                        {c.is_default && <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded-full font-semibold">Default</span>}
                        <motion.button whileTap={{ scale: 0.9 }} onClick={() => deleteCard(c.id)} className="text-red-400 hover:text-red-600">
                            <Trash2 size={15} />
                        </motion.button>
                    </div>
                ))}
                {showAdd ? (
                    <div className="space-y-3 mt-3">
                        <FloatInput label="Cardholder Name" value={holderName} onChange={setHolderName} icon={User} iconColor="#22C55E" />
                        <FloatInput label="Card Number" value={cardNum} onChange={setCardNum} icon={CreditCard} iconColor="#22C55E" placeholder="4242 4242 4242 4242" />
                        <div className="flex gap-3">
                            <div className="flex-1">
                                <FloatInput label="Expiry (MM/YY)" value={expiry} onChange={setExpiry} icon={CreditCard} iconColor="#22C55E" placeholder="12/28" />
                            </div>
                            <div className="flex-1">
                                <FloatInput label="CVV" value={cvv} onChange={v => setCvv(v.slice(0, 4))} icon={Lock} iconColor="#22C55E" placeholder="•••" />
                            </div>
                        </div>
                        <div className="flex gap-2">
                            <SaveButton saved={saved} onClick={handleAddCard} label="Save Card" gradient="linear-gradient(135deg, #22C55E, #16A34A)" />
                            <motion.button whileTap={{ scale: 0.97 }} onClick={() => setShowAdd(false)}
                                className="py-3.5 px-6 rounded-2xl font-bold text-gray-500 border-2 border-gray-100">Cancel</motion.button>
                        </div>
                        <p className="text-xs text-gray-400 text-center mt-1">🔒 Card info is stored securely via Supabase RLS</p>
                    </div>
                ) : (
                    <motion.button whileTap={{ scale: 0.97 }} onClick={() => setShowAdd(true)}
                        className="w-full mt-3 py-3 rounded-2xl border-2 border-dashed border-gray-200 text-gray-500 font-semibold text-sm flex items-center justify-center gap-2 hover:border-green-300 hover:text-green-600 transition-colors">
                        <Plus size={16} /> Add New Card
                    </motion.button>
                )}
            </div>
        </PanelWrap>
    );
}

/* ═══════════════════════════════════════════════════════════════════════════
   3. SUBSCRIPTION PANEL
   ═══════════════════════════════════════════════════════════════════════════ */
const PLANS = [
    {
        name: "Free", price: "$0", period: "/forever", color: "#6B7280", emoji: "🆓",
        features: ["3 free scans", "Basic dish info", "Community support"],
        missing: ["Unlimited scans", "AI details", "Priority support"]
    },
    {
        name: "Pro", price: "$9.99", period: "/month", color: "#3B5BDB", emoji: "⚡",
        features: ["Unlimited scans", "Name, Price, Category", "Recommendations", "Email support"],
        missing: ["Ingredients & Allergens", "Similar dishes"]
    },
    {
        name: "Max", price: "$19.99", period: "/month", color: "#7C3AED", emoji: "👑",
        features: ["Everything in Pro", "Full Ingredients", "Allergen warnings", "Similar dishes", "Priority support"],
        missing: []
    },
];

export function SubscriptionPanel() {
    const [currentPlan, setCurrentPlan] = useState("free");
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        (async () => {
            const sb = getSupabase(); const uid = await getUserId();
            if (!sb || !uid) return;
            const { data } = await sb.from("user_subscriptions").select("plan_name, status")
                .eq("user_id", uid).eq("status", "active").maybeSingle();
            if (data?.plan_name) setCurrentPlan(data.plan_name.toLowerCase());
        })();
    }, []);

    const handleSelectPlan = async (planName: string) => {
        const sb = getSupabase(); const uid = await getUserId();
        if (!sb || !uid) return;
        setLoading(true);
        await sb.from("user_subscriptions").upsert({
            user_id: uid, plan_name: planName, status: "active", billing_cycle: "monthly",
        }, { onConflict: "user_id" });
        setCurrentPlan(planName.toLowerCase());
        setLoading(false);
    };

    return (
        <PanelWrap borderColor="rgba(245,158,11,0.15)" gradientColors="linear-gradient(90deg, #F59E0B, #7C3AED, #3B5BDB)">
            <div className="p-4 space-y-3">
                {PLANS.map(plan => {
                    const isCurrent = currentPlan === plan.name.toLowerCase();
                    return (
                        <motion.div key={plan.name} whileTap={{ scale: 0.98 }}
                            className="rounded-2xl p-4 cursor-pointer transition-all relative overflow-hidden"
                            style={{
                                border: isCurrent ? `2px solid ${plan.color}` : "2px solid #E5E7EB",
                                backgroundColor: isCurrent ? plan.color + "08" : "#FAFAFA",
                            }}
                            onClick={() => !isCurrent && !loading && handleSelectPlan(plan.name)}
                        >
                            {isCurrent && (
                                <span className="absolute top-2 right-3 text-xs px-2.5 py-0.5 rounded-full font-bold text-white"
                                    style={{ backgroundColor: plan.color }}>Current</span>
                            )}
                            <div className="flex items-center gap-2 mb-2">
                                <span className="text-xl">{plan.emoji}</span>
                                <span className="font-bold text-gray-900">{plan.name}</span>
                                <span className="font-bold ml-auto" style={{ color: plan.color }}>{plan.price}<span className="text-xs text-gray-400 font-normal">{plan.period}</span></span>
                            </div>
                            <div className="space-y-1">
                                {plan.features.map(f => (
                                    <p key={f} className="text-xs text-gray-600 flex items-center gap-1.5">
                                        <span className="text-green-500">✓</span> {f}
                                    </p>
                                ))}
                                {plan.missing.map(f => (
                                    <p key={f} className="text-xs text-gray-300 flex items-center gap-1.5">
                                        <span className="text-gray-300">✗</span> {f}
                                    </p>
                                ))}
                            </div>
                        </motion.div>
                    );
                })}
            </div>
        </PanelWrap>
    );
}

/* ═══════════════════════════════════════════════════════════════════════════
   4. RECENT SCANS PANEL
   ═══════════════════════════════════════════════════════════════════════════ */
export function RecentScansPanel() {
    const [scans, setScans] = useState<any[]>([]);

    useEffect(() => {
        (async () => {
            const sb = getSupabase(); const uid = await getUserId();
            if (!sb || !uid) return;
            const { data } = await sb.from("user_recent_scans").select("*")
                .eq("user_id", uid).order("scanned_at", { ascending: false }).limit(10);
            if (data) setScans(data);
        })();
    }, []);

    const statusColor: Record<string, string> = {
        completed: "#22C55E", processing: "#F59E0B", failed: "#EF4444", queued: "#6B7280",
    };

    return (
        <PanelWrap borderColor="rgba(139,92,246,0.15)" gradientColors="linear-gradient(90deg, #8B5CF6, #6D28D9)">
            <div className="p-4">
                {scans.length === 0 ? (
                    <div className="text-center py-6">
                        <span className="text-3xl block mb-2">📸</span>
                        <p className="text-gray-400 text-sm">No scans yet. Go scan a menu!</p>
                    </div>
                ) : scans.map(s => (
                    <div key={s.id} className="flex items-center gap-3 py-3 border-b border-gray-100 last:border-0">
                        <div className="w-9 h-9 rounded-xl flex items-center justify-center text-base" style={{ backgroundColor: "#8B5CF618" }}>📸</div>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold text-gray-800 truncate">{s.image_name || "Menu Scan"}</p>
                            <p className="text-xs text-gray-400">{new Date(s.scanned_at).toLocaleDateString()} • {s.dish_count || 0} dishes{s.processing_time_ms ? ` • ${s.processing_time_ms}ms` : ""}</p>
                        </div>
                        <span className="text-xs px-2 py-0.5 rounded-full font-semibold"
                            style={{ backgroundColor: (statusColor[s.processing_status] || "#6B7280") + "18", color: statusColor[s.processing_status] || "#6B7280" }}>
                            {s.processing_status || "completed"}
                        </span>
                    </div>
                ))}
            </div>
        </PanelWrap>
    );
}

/* ═══════════════════════════════════════════════════════════════════════════
   5. NOTIFICATIONS PANEL
   ═══════════════════════════════════════════════════════════════════════════ */
export function NotificationsPanel() {
    const [push, setPush] = useState(true);
    const [emailNotif, setEmailNotif] = useState(true);
    const [marketing, setMarketing] = useState(false);
    const [saved, setSaved] = useState(false);

    useEffect(() => {
        (async () => {
            const sb = getSupabase(); const uid = await getUserId();
            if (!sb || !uid) return;
            const { data } = await sb.from("user_profile_preferences").select("*").eq("user_id", uid).maybeSingle();
            if (data) {
                setPush(data.notification_push_enabled ?? true);
                setEmailNotif(data.notification_email_enabled ?? true);
                setMarketing(data.marketing_opt_in ?? false);
            }
        })();
    }, []);

    const handleSave = async () => {
        const sb = getSupabase(); const uid = await getUserId();
        if (sb && uid) {
            await sb.from("user_profile_preferences").upsert({
                user_id: uid, notification_push_enabled: push,
                notification_email_enabled: emailNotif, marketing_opt_in: marketing,
            }, { onConflict: "user_id" });
        }
        setSaved(true); setTimeout(() => setSaved(false), 2000);
    };

    return (
        <PanelWrap borderColor="rgba(236,72,153,0.15)" gradientColors="linear-gradient(90deg, #EC4899, #F43F5E)">
            <div className="p-4 space-y-4">
                {[
                    { label: "Push Notifications", desc: "Receive mobile alerts for scan results", enabled: push, toggle: () => setPush(!push), icon: "🔔", color: "#EC4899" },
                    { label: "Email Notifications", desc: "Get scan summaries via email", enabled: emailNotif, toggle: () => setEmailNotif(!emailNotif), icon: "📧", color: "#8B5CF6" },
                    { label: "Marketing Emails", desc: "Tips, offers, and product updates", enabled: marketing, toggle: () => setMarketing(!marketing), icon: "📢", color: "#F59E0B" },
                ].map(item => (
                    <div key={item.label} className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-xl flex items-center justify-center text-base" style={{ backgroundColor: item.color + "12" }}>{item.icon}</div>
                        <div className="flex-1">
                            <p className="text-sm font-semibold text-gray-800">{item.label}</p>
                            <p className="text-xs text-gray-400">{item.desc}</p>
                        </div>
                        <Toggle enabled={item.enabled} onToggle={item.toggle} color={item.color} />
                    </div>
                ))}
            </div>
            <div className="px-4 pb-4">
                <SaveButton saved={saved} onClick={handleSave} label="Save Preferences" gradient="linear-gradient(135deg, #EC4899, #F43F5E)" />
            </div>
        </PanelWrap>
    );
}

/* ═══════════════════════════════════════════════════════════════════════════
   6. PRIVACY & SECURITY PANEL
   ═══════════════════════════════════════════════════════════════════════════ */
export function PrivacySecurityPanel() {
    const [visibility, setVisibility] = useState("private");
    const [analytics, setAnalytics] = useState(true);
    const [marketingOpt, setMarketingOpt] = useState(false);
    const [saved, setSaved] = useState(false);

    useEffect(() => {
        (async () => {
            const sb = getSupabase(); const uid = await getUserId();
            if (!sb || !uid) return;
            const { data } = await sb.from("user_profile_preferences").select("*").eq("user_id", uid).maybeSingle();
            if (data) {
                setVisibility(data.privacy_profile_visibility || "private");
                setAnalytics(data.analytics_opt_in ?? true);
                setMarketingOpt(data.marketing_opt_in ?? false);
            }
        })();
    }, []);

    const handleSave = async () => {
        const sb = getSupabase(); const uid = await getUserId();
        if (sb && uid) {
            await sb.from("user_profile_preferences").upsert({
                user_id: uid, privacy_profile_visibility: visibility,
                analytics_opt_in: analytics, marketing_opt_in: marketingOpt,
            }, { onConflict: "user_id" });
        }
        setSaved(true); setTimeout(() => setSaved(false), 2000);
    };

    const visOptions = [
        { value: "public", label: "Public", icon: "🌍", desc: "Anyone can see your profile" },
        { value: "friends", label: "Friends", icon: "👥", desc: "Only friends can see" },
        { value: "private", label: "Private", icon: "🔒", desc: "Only you can see" },
    ];

    return (
        <PanelWrap borderColor="rgba(6,182,212,0.15)" gradientColors="linear-gradient(90deg, #06B6D4, #0891B2)">
            <div className="p-4 space-y-4">
                <div>
                    <p className="text-xs font-bold text-gray-400 mb-2 uppercase tracking-wider">Profile Visibility</p>
                    <div className="space-y-1.5">
                        {visOptions.map(opt => (
                            <motion.button key={opt.value} whileTap={{ scale: 0.97 }} onClick={() => setVisibility(opt.value)}
                                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all"
                                style={{
                                    backgroundColor: visibility === opt.value ? "#06B6D412" : "#F9FAFB",
                                    border: visibility === opt.value ? "1.5px solid #06B6D440" : "1.5px solid transparent",
                                }}>
                                <span className="text-base">{opt.icon}</span>
                                <div className="flex-1 text-left">
                                    <p className="text-sm font-semibold" style={{ color: visibility === opt.value ? "#06B6D4" : "#374151" }}>{opt.label}</p>
                                    <p className="text-xs text-gray-400">{opt.desc}</p>
                                </div>
                                {visibility === opt.value && <Check size={16} className="text-cyan-500" />}
                            </motion.button>
                        ))}
                    </div>
                </div>
                <div className="space-y-3 pt-2">
                    <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-xl flex items-center justify-center text-base" style={{ backgroundColor: "#06B6D412" }}>📊</div>
                        <div className="flex-1">
                            <p className="text-sm font-semibold text-gray-800">Analytics</p>
                            <p className="text-xs text-gray-400">Help us improve with usage data</p>
                        </div>
                        <Toggle enabled={analytics} onToggle={() => setAnalytics(!analytics)} color="#06B6D4" />
                    </div>
                </div>
            </div>
            <div className="px-4 pb-4">
                <SaveButton saved={saved} onClick={handleSave} label="Save Settings" gradient="linear-gradient(135deg, #06B6D4, #0891B2)" />
            </div>
        </PanelWrap>
    );
}

/* ═══════════════════════════════════════════════════════════════════════════
   7. PASSWORD PANEL
   ═══════════════════════════════════════════════════════════════════════════ */
export function PasswordPanel() {
    const [current, setCurrent] = useState("");
    const [newPw, setNewPw] = useState("");
    const [confirm, setConfirm] = useState("");
    const [saved, setSaved] = useState(false);

    const handleSave = async () => {
        if (newPw !== confirm) return;
        const sb = getSupabase();
        if (sb) {
            await sb.auth.updateUser({ password: newPw });
        }
        setSaved(true); setTimeout(() => setSaved(false), 2000);
        setCurrent(""); setNewPw(""); setConfirm("");
    };

    return (
        <PanelWrap borderColor="rgba(107,114,128,0.15)" gradientColors="linear-gradient(90deg, #6B7280, #374151)">
            <div className="p-4 space-y-3">
                <FloatInput label="Current Password" value={current} onChange={setCurrent} type="password" icon={KeyRound} iconColor="#6B7280" />
                <FloatInput label="New Password" value={newPw} onChange={setNewPw} type="password" icon={Lock} iconColor="#3B5BDB" />
                <FloatInput label="Confirm Password" value={confirm} onChange={setConfirm} type="password" icon={Shield} iconColor="#22C55E" />
            </div>
            <div className="px-4 pb-4">
                <SaveButton saved={saved} onClick={handleSave} label="Update Password" gradient="linear-gradient(135deg, #6B7280, #374151)" />
            </div>
        </PanelWrap>
    );
}
