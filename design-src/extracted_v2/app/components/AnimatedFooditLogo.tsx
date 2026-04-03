import { motion } from "motion/react";
import fooditLogo from "figma:asset/7706f14051e931be36c72984482e711413e57601.png";

/**
 * Displays the Foodit logo with the two tomato 'oo' spinning clockwise.
 *
 * Tuning guide (if logo asset dimensions differ):
 *   LOGO_H  — displayed height in px
 *   LOGO_W  — displayed width (auto-calculated from asset ratio 1007:540)
 *   OVERLAY — diameter of the spinning shine circle (should ≈ tomato diameter)
 *   Left/Right cx — horizontal center of each tomato (% of LOGO_W)
 */

const LOGO_H = 64;
const LOGO_W = Math.round(LOGO_H * (1007 / 540)); // ≈ 119 px
const OVERLAY = 26; // px — shine circle diameter

// Approximate tomato centers as fraction of displayed dimensions
const TOMATOES = [
  { cx: LOGO_W * 0.285, cy: LOGO_H * 0.50, delay: 0 },    // left  'o'
  { cx: LOGO_W * 0.465, cy: LOGO_H * 0.50, delay: 0.45 },  // right 'o'
];

function TomatoShine({ cx, cy, delay }: { cx: number; cy: number; delay: number }) {
  return (
    <motion.div
      style={{
        position: "absolute",
        width: OVERLAY,
        height: OVERLAY,
        borderRadius: "50%",
        left: Math.round(cx - OVERLAY / 2),
        top: Math.round(cy - OVERLAY / 2),
        background:
          "conic-gradient(transparent 0deg, rgba(255,255,255,0.60) 75deg, transparent 150deg, transparent 360deg)",
        pointerEvents: "none",
      }}
      animate={{ rotate: [0, 360] }}
      transition={{
        duration: 2.2,
        repeat: Infinity,
        ease: "linear",
        delay,
      }}
    />
  );
}

export function AnimatedFooditLogo() {
  return (
    <div style={{ position: "relative", width: LOGO_W, height: LOGO_H, flexShrink: 0 }}>
      {/* Logo image — Figma exports with transparent background */}
      <img
        src={fooditLogo}
        alt="Foodit"
        draggable={false}
        style={{
          width: LOGO_W,
          height: LOGO_H,
          display: "block",
          userSelect: "none",
        }}
      />

      {/* Clockwise spinning shine on each tomato 'o' */}
      {TOMATOES.map((t, i) => (
        <TomatoShine key={i} cx={t.cx} cy={t.cy} delay={t.delay} />
      ))}
    </div>
  );
}
