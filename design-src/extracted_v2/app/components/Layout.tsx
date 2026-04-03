import { Outlet, NavLink, useLocation } from "react-router";
import { motion, AnimatePresence } from "motion/react";
import { useState, useEffect, useRef } from "react";

const TAB_ORDER = ["/", "/health", "/scan", "/profile"];

// ── DISCOVER: Map pin with pulse ──────────────────────────────────
function DiscoverIcon({ active }: { active: boolean }) {
  return (
    <motion.div className="relative w-7 h-7 flex items-center justify-center">
      <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
        {/* Pin body */}
        <motion.path
          d="M14 2c-4.4 0-8 3.6-8 8 0 5.5 8 16 8 16s8-10.5 8-16c0-4.4-3.6-8-8-8z"
          fill={active ? "#3B5BDB" : "none"}
          stroke={active ? "#3B5BDB" : "#AAAAAA"}
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          animate={active ? { fill: ["rgba(59,91,219,0)", "#3B5BDB"] } : {}}
          transition={{ duration: 0.35 }}
        />
        {/* Inner circle */}
        <motion.circle
          cx="14" cy="10" r="2.5"
          fill={active ? "white" : "#CCCCCC"}
          animate={active ? { scale: [1, 1.3, 1] } : {}}
          transition={{ duration: 0.5, delay: 0.1 }}
          style={{ transformOrigin: "14px 10px" }}
        />
        {/* Pulse rings */}
        {active && (
          <>
            <motion.circle
              cx="14" cy="10" r="5"
              stroke="#3B5BDB"
              strokeWidth="1.5"
              fill="none"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1.6, opacity: [0, 0.6, 0] }}
              transition={{ duration: 1.2, repeat: Infinity, ease: "easeOut" }}
              style={{ transformOrigin: "14px 10px" }}
            />
            <motion.circle
              cx="14" cy="10" r="5"
              stroke="#3B5BDB"
              strokeWidth="1.5"
              fill="none"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1.6, opacity: [0, 0.6, 0] }}
              transition={{ duration: 1.2, repeat: Infinity, ease: "easeOut", delay: 0.4 }}
              style={{ transformOrigin: "14px 10px" }}
            />
          </>
        )}
      </svg>
    </motion.div>
  );
}

// ── HEALTH+: Heartbeat pulse ────────────────────────────────────────────────
function HealthIcon({ active }: { active: boolean }) {
  return (
    <motion.div
      animate={active ? { scale: [1, 1.18, 0.93, 1.1, 1] } : {}}
      transition={{ duration: 0.55, times: [0, 0.2, 0.5, 0.7, 1] }}
      className="w-7 h-7 flex items-center justify-center"
    >
      <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
        <motion.path
          d="M14 24s-9-5-9-12a6 6 0 0 1 9-5.2A6 6 0 0 1 23 12c0 7-9 12-9 12z"
          fill={active ? "#3B5BDB" : "none"}
          stroke={active ? "#3B5BDB" : "#AAAAAA"}
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          animate={active ? { fill: ["rgba(59,91,219,0)", "#3B5BDB"] } : {}}
          transition={{ duration: 0.35 }}
        />
        {active && (
          <motion.path
            d="M8 14h2.5l1.5-2.5 2 5 1.5-2.5H18"
            stroke="white"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 1 }}
            transition={{ duration: 0.45, delay: 0.18 }}
          />
        )}
      </svg>
    </motion.div>
  );
}

// ── SCAN: QR corner-bracket frame with sweep line ──────────────────────────
function ScanIcon({ active }: { active: boolean }) {
  const color = active ? "#3B5BDB" : "#AAAAAA";
  const sw = 2.2;
  const r = 3;
  return (
    <div className="relative w-7 h-7 flex items-center justify-center">
      <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
        {/* Top-left bracket */}
        <path d={`M4 ${4 + r} Q4 4 ${4 + r} 4 L9 4`} stroke={color} strokeWidth={sw} strokeLinecap="round" fill="none" />
        <path d={`M4 ${4 + r} L4 9`} stroke={color} strokeWidth={sw} strokeLinecap="round" />
        {/* Top-right bracket */}
        <path d={`M${28 - 4 - r} 4 Q${28 - 4} 4 ${28 - 4} ${4 + r} L${28 - 4} 9`} stroke={color} strokeWidth={sw} strokeLinecap="round" fill="none" />
        <path d={`M${28 - 9} 4 L${28 - 4 - r} 4`} stroke={color} strokeWidth={sw} strokeLinecap="round" />
        {/* Bottom-left bracket */}
        <path d={`M4 ${28 - 9} L4 ${28 - 4 - r} Q4 ${28 - 4} ${4 + r} ${28 - 4}`} stroke={color} strokeWidth={sw} strokeLinecap="round" fill="none" />
        <path d={`M${4 + r} ${28 - 4} L9 ${28 - 4}`} stroke={color} strokeWidth={sw} strokeLinecap="round" />
        {/* Bottom-right bracket */}
        <path d={`M${28 - 9} ${28 - 4} L${28 - 4 - r} ${28 - 4} Q${28 - 4} ${28 - 4} ${28 - 4} ${28 - 4 - r} L${28 - 4} ${28 - 9}`} stroke={color} strokeWidth={sw} strokeLinecap="round" fill="none" />

        {/* Sweep line */}
        {active && (
          <motion.line
            x1="5" x2="23"
            y1="14" y2="14"
            stroke={active ? "#3B5BDB" : "transparent"}
            strokeWidth="1.5"
            strokeLinecap="round"
            initial={{ opacity: 0 }}
            animate={{ y1: [6, 22, 6], y2: [6, 22, 6], opacity: [0, 1, 1, 1, 0] }}
            transition={{ duration: 1.6, repeat: Infinity, ease: "easeInOut" }}
          />
        )}
        {/* Center dot grid (QR-style) */}
        {[
          [12, 12], [14, 12], [16, 12],
          [12, 14], [16, 14],
          [12, 16], [14, 16], [16, 16],
        ].map(([x, y], i) => (
          <motion.rect
            key={i}
            x={x - 0.8} y={y - 0.8} width="1.6" height="1.6" rx="0.4"
            fill={color}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: active ? i * 0.04 : 0, duration: 0.3 }}
          />
        ))}
      </svg>
    </div>
  );
}

// ── PROFILE: User avatar with notification dot ──────────────────────────────────────
function ProfileIcon({ active }: { active: boolean }) {
  return (
    <motion.div
      animate={active ? { y: [0, -4, 1, 0] } : {}}
      transition={{ duration: 0.45, ease: "easeOut" }}
      className="w-7 h-7 flex items-center justify-center"
    >
      <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
        {/* Head */}
        <motion.circle
          cx="14" cy="9" r="5"
          fill={active ? "rgba(59,91,219,0.15)" : "none"}
          stroke={active ? "#3B5BDB" : "#AAAAAA"}
          strokeWidth="1.8"
          animate={active ? { scale: [1, 1.1, 1] } : {}}
          transition={{ duration: 0.4 }}
          style={{ transformOrigin: "14px 9px" }}
        />
        {/* Body/shoulders */}
        <motion.path
          d="M4 25c0-5.5 4.5-10 10-10s10 4.5 10 10"
          stroke={active ? "#3B5BDB" : "#AAAAAA"}
          strokeWidth="1.8"
          strokeLinecap="round"
          fill={active ? "rgba(59,91,219,0.15)" : "none"}
          animate={active ? { pathLength: [0, 1] } : {}}
          transition={{ duration: 0.5, delay: 0.1 }}
        />
        {/* Notification dot */}
        {active && (
          <motion.circle
            cx="21" cy="6" r="3"
            fill="#EF4444"
            stroke="white"
            strokeWidth="1.5"
            initial={{ scale: 0 }}
            animate={{ scale: [0, 1.2, 1] }}
            transition={{ duration: 0.4, delay: 0.2 }}
          />
        )}
      </svg>
    </motion.div>
  );
}

// ── LAYOUT ─────────────────────────────────────────────────────────────────
const tabs = [
  { path: "/", label: "Discover", icon: DiscoverIcon },
  { path: "/health", label: "Health+", icon: HealthIcon },
  { path: "/scan", label: "Scan", icon: ScanIcon },
  { path: "/profile", label: "Profile", icon: ProfileIcon },
];

export function Layout() {
  const location = useLocation();
  const prevIndexRef = useRef(TAB_ORDER.indexOf(location.pathname));
  const [dir, setDir] = useState(0); // -1 = slide left, 1 = slide right

  const currentIndex = TAB_ORDER.indexOf(location.pathname);

  useEffect(() => {
    const prev = prevIndexRef.current;
    const curr = TAB_ORDER.indexOf(location.pathname);
    setDir(curr > prev ? 1 : -1);
    prevIndexRef.current = curr;
  }, [location.pathname]);

  const isActive = (path: string) => {
    if (path === "/") return location.pathname === "/";
    return location.pathname.startsWith(path);
  };

  const variants = {
    initial: (d: number) => ({ x: d > 0 ? "100%" : "-100%", opacity: 0 }),
    animate: { x: 0, opacity: 1 },
    exit: (d: number) => ({ x: d > 0 ? "-100%" : "100%", opacity: 0 }),
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-200">
      <div
        className="relative flex flex-col bg-gray-50 overflow-hidden shadow-2xl"
        style={{ width: "430px", height: "100dvh", maxHeight: "932px" }}
      >
        {/* Main content with directional slide */}
        <div className="flex-1 overflow-y-auto overflow-x-hidden pb-20">
          <AnimatePresence mode="wait" custom={dir}>
            <motion.div
              key={location.pathname}
              custom={dir}
              variants={variants}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={{ duration: 0.3, ease: [0.32, 0.72, 0, 1] }}
              className="h-full"
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Bottom Navigation */}
        <div
          className="absolute bottom-0 left-0 right-0 bg-white border-t border-gray-100 shadow-[0_-4px_20px_rgba(0,0,0,0.06)]"
          style={{ paddingBottom: "env(safe-area-inset-bottom, 0px)" }}
        >
          {/* Active indicator pill that slides */}
          <div className="relative flex items-center justify-around px-1 pt-2 pb-2.5">
            {tabs.map((tab) => {
              const active = isActive(tab.path);
              const Icon = tab.icon;
              return (
                <NavLink
                  key={tab.path}
                  to={tab.path}
                  end={tab.path === "/"}
                  className="flex flex-col items-center gap-0.5 px-4 py-1 relative z-10"
                >
                  {/* Active pill bg */}
                  {active && (
                    <motion.div
                      layoutId="navPill"
                      className="absolute inset-0 rounded-2xl"
                      style={{ backgroundColor: "rgba(59,91,219,0.07)" }}
                      transition={{ type: "spring", stiffness: 400, damping: 30 }}
                    />
                  )}
                  <Icon active={active} />
                  <motion.span
                    animate={{
                      color: active ? "#3B5BDB" : "#999999",
                      fontWeight: active ? 700 : 500,
                    }}
                    transition={{ duration: 0.2 }}
                    className="text-xs"
                    style={{ fontSize: "10px" }}
                  >
                    {tab.label}
                  </motion.span>
                  {/* Dot indicator */}
                  {active && (
                    <motion.div
                      layoutId="navDot"
                      className="absolute -bottom-0.5 w-4 h-0.5 rounded-full bg-blue-600"
                      transition={{ type: "spring", stiffness: 500, damping: 35 }}
                    />
                  )}
                </NavLink>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}