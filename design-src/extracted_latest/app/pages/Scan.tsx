import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Camera, Image, Zap, RotateCcw, Star, AlertTriangle, Check } from "lucide-react";

const FEATURES = [
  { icon: "🔍", title: "Instant Analysis", desc: "Get nutritional info in seconds" },
  { icon: "⚠️", title: "Allergy Alerts", desc: "Auto-detect your allergens" },
  { icon: "💡", title: "Smart Tips", desc: "Personalized health guidance" },
];

export function Scan() {
  const [mode, setMode] = useState<"idle" | "scanning" | "result">("idle");

  const startScan = () => {
    setMode("scanning");
    setTimeout(() => setMode("result"), 2500);
  };

  const reset = () => setMode("idle");

  return (
    <div className="flex flex-col min-h-full bg-gray-50">
      {/* Header */}
      <div
        className="relative px-5 pt-7 pb-5 overflow-hidden"
        style={{ backgroundColor: "#7C3AED" }}
      >
        <div className="absolute -top-8 -right-8 w-32 h-32 rounded-full bg-white/10" />
        <div className="absolute top-4 -right-4 w-20 h-20 rounded-full bg-white/5" />
        <div className="absolute -bottom-6 -left-6 w-24 h-24 rounded-full bg-white/10" />

        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <h1 className="text-white mb-1" style={{ fontWeight: 800, fontSize: "22px" }}>Menu Scan</h1>
          <p className="text-white/80 text-xs">Capture menus, enrich dishes, and explore details instantly</p>
        </motion.div>
      </div>

      <div className="px-4 -mt-3 space-y-4 pb-24">
        <AnimatePresence mode="wait">

          {/* IDLE STATE */}
          {mode === "idle" && (
            <motion.div
              key="idle"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              {/* Main Scan Area */}
              <div className="bg-white rounded-3xl shadow-sm overflow-hidden">
                {/* Camera viewfinder area */}
                <div
                  className="relative mx-4 mt-4 rounded-2xl overflow-hidden flex items-center justify-center"
                  style={{
                    height: "220px",
                    background: "linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%)",
                  }}
                >
                  {/* Corner brackets */}
                  {[
                    "top-3 left-3 border-t-2 border-l-2",
                    "top-3 right-3 border-t-2 border-r-2",
                    "bottom-3 left-3 border-b-2 border-l-2",
                    "bottom-3 right-3 border-b-2 border-r-2",
                  ].map((cls, i) => (
                    <motion.div
                      key={i}
                      className={`absolute w-7 h-7 rounded ${cls} border-blue-400`}
                      animate={{ opacity: [0.4, 1, 0.4] }}
                      transition={{ duration: 2, repeat: Infinity, delay: i * 0.2 }}
                    />
                  ))}

                  {/* Scan line */}
                  <motion.div
                    className="absolute left-4 right-4 h-0.5 bg-gradient-to-r from-transparent via-cyan-400 to-transparent"
                    animate={{ y: [-70, 70, -70] }}
                    transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                  />
                  {/* Glow under scan line */}
                  <motion.div
                    className="absolute left-4 right-4 h-8 bg-gradient-to-b from-cyan-400/20 to-transparent"
                    animate={{ y: [-70, 70, -70] }}
                    transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                  />

                  <motion.div
                    animate={{ scale: [1, 1.04, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="flex flex-col items-center gap-2"
                  >
                    <p className="text-white/60 text-xs text-center">Point camera at a menu</p>
                  </motion.div>
                </div>

                {/* Buttons */}
                <div className="flex gap-3 p-4">
                  <motion.button
                    whileTap={{ scale: 0.95 }}
                    onClick={startScan}
                    className="flex-1 flex items-center justify-center gap-2 py-3.5 rounded-2xl font-semibold text-white relative overflow-hidden"
                    style={{ background: "linear-gradient(135deg, #3B5BDB, #2563EB)" }}
                  >
                    <motion.div
                      className="absolute inset-0 bg-gradient-to-r from-transparent via-white/15 to-transparent"
                      animate={{ x: ["-100%", "200%"] }}
                      transition={{ duration: 2, repeat: Infinity, ease: "linear", repeatDelay: 0.5 }}
                    />
                    <Camera size={18} />
                    <span>Capture</span>
                  </motion.button>
                  <motion.button
                    whileTap={{ scale: 0.95 }}
                    className="flex-1 flex items-center justify-center gap-2 py-3.5 rounded-2xl font-semibold border-2 border-gray-100 text-gray-700 bg-white"
                  >
                    <Image size={18} className="text-blue-500" />
                    <span>Gallery</span>
                  </motion.button>
                </div>
              </div>

              {/* Feature Pills */}
              <div className="flex gap-3 mt-1">
                {FEATURES.map((f, i) => (
                  <motion.div
                    key={f.title}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 + i * 0.08 }}
                    className="flex-1 bg-white rounded-2xl p-3 shadow-sm text-center"
                  >
                    <div className="text-xl mb-1">{f.icon}</div>
                    <p className="text-xs font-semibold text-gray-800">{f.title}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{f.desc}</p>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {/* SCANNING STATE */}
          {mode === "scanning" && (
            <motion.div
              key="scanning"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center py-16"
            >
              <div className="relative w-32 h-32 mb-6">
                {[0, 1, 2].map(i => (
                  <motion.div
                    key={i}
                    className="absolute inset-0 rounded-full border-2 border-blue-400"
                    animate={{ scale: [1, 2], opacity: [0.8, 0] }}
                    transition={{ duration: 2, delay: i * 0.6, repeat: Infinity }}
                  />
                ))}
                <div className="w-full h-full rounded-full bg-blue-600 flex items-center justify-center">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  >
                    <Zap size={40} className="text-white" />
                  </motion.div>
                </div>
              </div>
              <motion.h2
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className="font-bold text-gray-800 text-lg"
              >
                Analyzing Menu...
              </motion.h2>
              <p className="text-gray-500 text-sm mt-2">Detecting dishes & nutrition data</p>

              {["Reading menu text...", "Identifying dishes...", "Checking allergens..."].map((step, i) => (
                <motion.div
                  key={step}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.6 }}
                  className="flex items-center gap-2 mt-3"
                >
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: i * 0.6 + 0.3 }}
                    className="w-5 h-5 rounded-full bg-green-500 flex items-center justify-center"
                  >
                    <Check size={11} className="text-white" />
                  </motion.div>
                  <span className="text-sm text-gray-600">{step}</span>
                </motion.div>
              ))}
            </motion.div>
          )}

          {/* RESULT STATE */}
          {mode === "result" && (
            <motion.div
              key="result"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              <div className="bg-white rounded-3xl shadow-sm overflow-hidden">
                {/* Result header */}
                <div className="p-4 border-b border-gray-50">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <span className="text-2xl">🍕</span>
                      <div>
                        <h3 className="font-bold text-gray-900">Margherita Pizza</h3>
                        <p className="text-xs text-gray-500">Napoli Express • Wood-fire</p>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <div className="text-xs font-bold text-green-600 bg-green-50 px-2 py-0.5 rounded-full">72 / 100</div>
                      <div className="flex gap-0.5">
                        {[1,2,3,4].map(s => <Star key={s} size={10} className="text-amber-400 fill-amber-400" />)}
                        <Star size={10} className="text-gray-300" />
                      </div>
                    </div>
                  </div>

                  {/* Nutrition grid */}
                  <div className="grid grid-cols-4 gap-2 mt-3">
                    {[
                      { label: "Calories", value: "285", color: "#3B5BDB" },
                      { label: "Protein", value: "12g", color: "#22C55E" },
                      { label: "Carbs", value: "38g", color: "#F59E0B" },
                      { label: "Fat", value: "9g", color: "#EF4444" },
                    ].map((n, i) => (
                      <motion.div
                        key={n.label}
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ delay: i * 0.06 }}
                        className="bg-gray-50 rounded-xl p-2 text-center"
                      >
                        <div className="font-bold text-sm" style={{ color: n.color }}>{n.value}</div>
                        <div className="text-xs text-gray-400">{n.label}</div>
                      </motion.div>
                    ))}
                  </div>
                </div>

                {/* Allergen Alert */}
                <div className="p-4 border-b border-gray-50">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertTriangle size={15} className="text-orange-500" />
                    <span className="text-sm font-semibold text-gray-700">Allergen Alert</span>
                  </div>
                  <div className="flex gap-2 flex-wrap">
                    {["🧀 Dairy", "🌾 Gluten"].map(a => (
                      <span key={a} className="px-3 py-1.5 bg-orange-50 text-orange-600 rounded-xl text-xs font-semibold">
                        {a}
                      </span>
                    ))}
                    <span className="px-3 py-1.5 bg-green-50 text-green-600 rounded-xl text-xs font-semibold">
                      ✓ No nuts
                    </span>
                  </div>
                </div>

                {/* AI Tip */}
                <div className="p-4">
                  <div className="flex items-start gap-2 bg-blue-50 rounded-xl p-3">
                    <span className="text-base">🤖</span>
                    <div>
                      <p className="text-xs font-semibold text-blue-800">AI Health Tip</p>
                      <p className="text-xs text-blue-700 mt-0.5">
                        This dish is a good source of lycopene from tomatoes. Consider adding a side salad for extra fiber!
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex gap-3 mt-3">
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  onClick={reset}
                  className="flex-1 flex items-center justify-center gap-2 py-3.5 rounded-2xl font-semibold border-2 border-gray-100 text-gray-700 bg-white"
                >
                  <RotateCcw size={16} />
                  Scan Again
                </motion.button>
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  className="flex-1 flex items-center justify-center gap-2 py-3.5 rounded-2xl font-semibold text-white"
                  style={{ background: "linear-gradient(135deg, #3B5BDB, #2563EB)" }}
                >
                  Save Scan
                </motion.button>
              </div>
            </motion.div>
          )}

        </AnimatePresence>
      </div>
    </div>
  );
}