/**
 * Card — a single playing card.
 *
 * Face: cool brushed-steel parchment, crisp suit colors.
 * Back: FR4 circuit board — dark green substrate, copper traces & vias.
 */

import { CSSProperties, useMemo } from "react";
import { color, font, size, shadow, transition } from "../../theme/tokens.ts";

const SUIT_SYMBOLS: Record<string, string> = {
  s: "\u2660",
  h: "\u2665",
  d: "\u2666",
  c: "\u2663",
};

const SUIT_COLORS: Record<string, string> = {
  s: color.suit.spades,
  h: color.suit.hearts,
  d: color.suit.diamonds,
  c: color.suit.clubs,
};

// Pip positions as [x%, y%] — x: 0=left, 50=center, 100=right; y: 0=top, 100=bottom
// Positions are within the pip area (excluding corner indicators)
const PIP_LAYOUTS: Record<string, [number, number][]> = {
  A: [[50, 50]],
  "2": [[50, 18], [50, 82]],
  "3": [[50, 18], [50, 50], [50, 82]],
  "4": [[30, 18], [70, 18], [30, 82], [70, 82]],
  "5": [[30, 18], [70, 18], [50, 50], [30, 82], [70, 82]],
  "6": [[30, 18], [70, 18], [30, 50], [70, 50], [30, 82], [70, 82]],
  "7": [[30, 18], [70, 18], [50, 34], [30, 50], [70, 50], [30, 82], [70, 82]],
  "8": [[30, 18], [70, 18], [50, 34], [30, 50], [70, 50], [50, 66], [30, 82], [70, 82]],
  "9": [[30, 16], [70, 16], [30, 38], [70, 38], [50, 50], [30, 62], [70, 62], [30, 84], [70, 84]],
  T: [[30, 16], [70, 16], [50, 30], [30, 38], [70, 38], [30, 62], [70, 62], [50, 70], [30, 84], [70, 84]],
};

// ─── PCB color palette ────────────────────────────────────────
const pcb = {
  fr4:       "#0a2818",   // dark FR4 substrate
  fr4Light:  "#0d3320",   // slightly lighter for depth
  mask:      "#0c2e1c",   // solder mask green
  copper:    "#7a5430",   // copper trace
  copperDim: "#5c3e24",   // oxidized / recessed copper
  copperPad: "#8a6038",   // solder pad — brighter
  silk:      "#1a5038",   // silkscreen (subtle markings)
  drill:     "#061a0e",   // drill hole — darkest
} as const;

interface CardProps {
  /** Card string like "As", "Td", "2c" */
  card?: string;
  /** Face-down card */
  faceDown?: boolean;
  /** Scale factor (1 = default 62x88) */
  scale?: number;
  /** Animation delay for staggered deals (ms) */
  dealDelay?: number;
  /** Whether to show the deal animation */
  animated?: boolean;
  /** Reveal animation (board cards flipping) */
  reveal?: boolean;
  /** Glow color for highlighting (e.g. winning hand) */
  glow?: string;
}

export function Card({
  card,
  faceDown = false,
  scale = 1,
  dealDelay = 0,
  animated = false,
  reveal = false,
  glow,
}: CardProps) {
  const w = size.card.width * scale;
  const h = size.card.height * scale;
  const r = size.radius.md * scale;

  const baseStyle: CSSProperties = useMemo(() => ({
    width: w,
    height: h,
    borderRadius: r,
    position: "relative",
    userSelect: "none",
    flexShrink: 0,
    transition: transition.normal,
    ...(animated ? {
      animation: `cardDeal 0.5s cubic-bezier(0.22, 1, 0.36, 1) forwards`,
      animationDelay: `${dealDelay}ms`,
      opacity: 0,
    } : {}),
    ...(reveal ? {
      animation: `cardReveal 0.5s cubic-bezier(0.22, 1, 0.36, 1) forwards`,
      animationDelay: `${dealDelay}ms`,
    } : {}),
    ...(glow ? {
      boxShadow: `${shadow.card}, 0 0 14px ${glow}50, 0 0 4px ${glow}30`,
    } : {}),
  }), [w, h, r, animated, reveal, dealDelay, glow]);

  if (faceDown || !card) {
    return <CardBack style={baseStyle} scale={scale} w={w} h={h} />;
  }

  const rank = card.slice(0, -1);
  const suit = card.slice(-1);
  const suitColor = SUIT_COLORS[suit] ?? color.text.primary;
  const suitSymbol = SUIT_SYMBOLS[suit] ?? "?";

  return (
    <div className="perspective-container" style={baseStyle}>
      {/* Card face — cool brushed steel */}
      <div
        style={{
          width: "100%",
          height: "100%",
          borderRadius: r,
          background: "linear-gradient(170deg, #eaeaef 0%, #e0e0e8 40%, #d4d4dc 100%)",
          border: "1px solid #a8a8b0",
          boxShadow: glow
            ? `${shadow.card}, 0 0 14px ${glow}50`
            : `${shadow.card}, inset 0 1px 3px rgba(0,0,0,0.08)`,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          position: "relative",
        }}
      >
        {/* Top-left corner */}
        <div
          style={{
            position: "absolute",
            top: 3 * scale,
            left: 4 * scale,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            lineHeight: 1,
          }}
        >
          <span
            style={{
              fontFamily: font.mono,
              fontSize: 13 * scale,
              fontWeight: 700,
              color: suitColor,
            }}
          >
            {rank}
          </span>
          <span style={{ fontSize: 10 * scale, color: suitColor, marginTop: -1 * scale }}>
            {suitSymbol}
          </span>
        </div>

        {/* Center area — pips or face card letter */}
        <div
          style={{
            position: "absolute",
            top: 18 * scale,
            bottom: 18 * scale,
            left: 4 * scale,
            right: 4 * scale,
          }}
        >
          {PIP_LAYOUTS[rank] ? (
            // Number cards + Ace: show suit pips at defined positions
            PIP_LAYOUTS[rank].map(([x, y], i) => (
              <span
                key={i}
                style={{
                  position: "absolute",
                  left: `${x}%`,
                  top: `${y}%`,
                  transform: `translate(-50%, -50%)${y > 50 ? " rotate(180deg)" : ""}`,
                  fontSize: (rank === "A" ? 28 : PIP_LAYOUTS[rank].length > 6 ? 10 : 13) * scale,
                  color: suitColor,
                  opacity: rank === "A" ? 0.85 : 0.75,
                  lineHeight: 1,
                  filter: rank === "A" ? "drop-shadow(0 1px 2px rgba(0,0,0,0.12))" : undefined,
                }}
              >
                {suitSymbol}
              </span>
            ))
          ) : (
            // Face cards (J, Q, K): large rank letter in center
            <div
              style={{
                width: "100%",
                height: "100%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <span
                style={{
                  fontFamily: font.mono,
                  fontSize: 28 * scale,
                  fontWeight: 700,
                  color: suitColor,
                  opacity: 0.7,
                  filter: "drop-shadow(0 1px 2px rgba(0,0,0,0.1))",
                }}
              >
                {rank}
              </span>
            </div>
          )}
        </div>

        {/* Bottom-right corner (inverted) */}
        <div
          style={{
            position: "absolute",
            bottom: 3 * scale,
            right: 4 * scale,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            lineHeight: 1,
            transform: "rotate(180deg)",
          }}
        >
          <span
            style={{
              fontFamily: font.mono,
              fontSize: 13 * scale,
              fontWeight: 700,
              color: suitColor,
            }}
          >
            {rank}
          </span>
          <span style={{ fontSize: 10 * scale, color: suitColor, marginTop: -1 * scale }}>
            {suitSymbol}
          </span>
        </div>

        {/* Inner highlight — cool steel with emerald whisper on top edge */}
        <div
          style={{
            position: "absolute",
            inset: 1,
            borderRadius: r - 1,
            borderTop: "1px solid rgba(80, 255, 176, 0.06)",
            borderLeft: "1px solid rgba(255,255,255,0.2)",
            borderRight: "1px solid rgba(255,255,255,0.1)",
            borderBottom: "1px solid rgba(255,255,255,0.08)",
            pointerEvents: "none",
          }}
        />
      </div>
    </div>
  );
}

// ─── Card Back — FR4 PCB with copper traces ───────────────────

function CardBack({ style, scale, w, h }: {
  style: CSSProperties;
  scale: number;
  w: number;
  h: number;
}) {
  const r = size.radius.md * scale;

  // Viewbox matches card pixel size so strokes scale naturally
  const vw = 62;
  const vh = 88;
  // Trace thickness at 1x scale
  const t = 0.8;
  const tThin = 0.5;
  // Pad/via sizes
  const padR = 1.6;
  const viaR = 1.0;
  const drillR = 0.5;
  // Inset for the board edge copper border
  const edge = 4;

  return (
    <div className="perspective-container" style={style}>
      <div
        style={{
          width: "100%",
          height: "100%",
          borderRadius: r,
          background: `linear-gradient(175deg, ${pcb.fr4Light} 0%, ${pcb.fr4} 60%, #071e10 100%)`,
          border: `1px solid ${pcb.copperDim}50`,
          boxShadow: `${shadow.card}, inset 0 0 16px rgba(0,0,0,0.3)`,
          position: "relative",
          overflow: "hidden",
        }}
      >
        <svg
          viewBox={`0 0 ${vw} ${vh}`}
          width={w}
          height={h}
          style={{ position: "absolute", inset: 0 }}
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* ── Board edge — copper border trace ── */}
          <rect
            x={edge} y={edge}
            width={vw - edge * 2} height={vh - edge * 2}
            rx={2} ry={2}
            fill="none"
            stroke={pcb.copperDim}
            strokeWidth={t}
            opacity={0.7}
          />

          {/* ── Horizontal traces ── */}
          {/* Top region */}
          <line x1={edge} y1={14} x2={22} y2={14} stroke={pcb.copper} strokeWidth={t} opacity={0.6} />
          <line x1={28} y1={14} x2={vw - edge} y2={14} stroke={pcb.copper} strokeWidth={tThin} opacity={0.5} />

          <line x1={edge} y1={20} x2={16} y2={20} stroke={pcb.copperDim} strokeWidth={tThin} opacity={0.5} />
          <line x1={40} y1={20} x2={vw - edge} y2={20} stroke={pcb.copperDim} strokeWidth={tThin} opacity={0.45} />

          {/* Center region — bus lines */}
          <line x1={edge} y1={38} x2={vw - edge} y2={38} stroke={pcb.copper} strokeWidth={t} opacity={0.55} />
          <line x1={10} y1={44} x2={52} y2={44} stroke={pcb.copperDim} strokeWidth={tThin} opacity={0.4} />
          <line x1={edge} y1={50} x2={vw - edge} y2={50} stroke={pcb.copper} strokeWidth={t} opacity={0.55} />

          {/* Bottom region */}
          <line x1={edge} y1={66} x2={20} y2={66} stroke={pcb.copperDim} strokeWidth={tThin} opacity={0.5} />
          <line x1={34} y1={66} x2={vw - edge} y2={66} stroke={pcb.copper} strokeWidth={tThin} opacity={0.45} />

          <line x1={edge} y1={74} x2={vw - edge} y2={74} stroke={pcb.copperDim} strokeWidth={tThin} opacity={0.4} />

          {/* ── Vertical traces ── */}
          <line x1={14} y1={edge} x2={14} y2={38} stroke={pcb.copper} strokeWidth={t} opacity={0.55} />
          <line x1={14} y1={50} x2={14} y2={vh - edge} stroke={pcb.copperDim} strokeWidth={tThin} opacity={0.4} />

          <line x1={25} y1={14} x2={25} y2={38} stroke={pcb.copperDim} strokeWidth={tThin} opacity={0.45} />
          <line x1={25} y1={50} x2={25} y2={74} stroke={pcb.copperDim} strokeWidth={tThin} opacity={0.4} />

          <line x1={37} y1={14} x2={37} y2={38} stroke={pcb.copperDim} strokeWidth={tThin} opacity={0.45} />
          <line x1={37} y1={50} x2={37} y2={66} stroke={pcb.copper} strokeWidth={tThin} opacity={0.5} />

          <line x1={48} y1={edge} x2={48} y2={38} stroke={pcb.copper} strokeWidth={t} opacity={0.55} />
          <line x1={48} y1={50} x2={48} y2={vh - edge} stroke={pcb.copperDim} strokeWidth={tThin} opacity={0.4} />

          {/* ── Solder pads — rectangular, at intersections ── */}
          <rect x={14 - padR} y={14 - padR} width={padR * 2} height={padR * 2} rx={0.4} fill={pcb.copperPad} opacity={0.6} />
          <rect x={14 - padR} y={38 - padR} width={padR * 2} height={padR * 2} rx={0.4} fill={pcb.copperPad} opacity={0.6} />
          <rect x={14 - padR} y={50 - padR} width={padR * 2} height={padR * 2} rx={0.4} fill={pcb.copperPad} opacity={0.55} />
          <rect x={48 - padR} y={38 - padR} width={padR * 2} height={padR * 2} rx={0.4} fill={pcb.copperPad} opacity={0.6} />
          <rect x={48 - padR} y={50 - padR} width={padR * 2} height={padR * 2} rx={0.4} fill={pcb.copperPad} opacity={0.55} />
          <rect x={48 - padR} y={14 - padR} width={padR * 2} height={padR * 2} rx={0.4} fill={pcb.copperPad} opacity={0.55} />
          <rect x={48 - padR} y={74 - padR} width={padR * 2} height={padR * 2} rx={0.4} fill={pcb.copperPad} opacity={0.5} />
          <rect x={14 - padR} y={74 - padR} width={padR * 2} height={padR * 2} rx={0.4} fill={pcb.copperPad} opacity={0.5} />

          {/* ── Vias — circular, copper ring with dark drill hole ── */}
          {/* Top-left cluster */}
          <circle cx={25} cy={14} r={viaR} fill={pcb.copperPad} opacity={0.55} />
          <circle cx={25} cy={14} r={drillR} fill={pcb.drill} />

          <circle cx={25} cy={26} r={viaR} fill={pcb.copperPad} opacity={0.5} />
          <circle cx={25} cy={26} r={drillR} fill={pcb.drill} />

          {/* Center cluster — main IC area */}
          <circle cx={31} cy={38} r={viaR * 1.2} fill={pcb.copperPad} opacity={0.6} />
          <circle cx={31} cy={38} r={drillR * 1.1} fill={pcb.drill} />

          <circle cx={31} cy={44} r={viaR} fill={pcb.copperPad} opacity={0.5} />
          <circle cx={31} cy={44} r={drillR} fill={pcb.drill} />

          <circle cx={31} cy={50} r={viaR * 1.2} fill={pcb.copperPad} opacity={0.6} />
          <circle cx={31} cy={50} r={drillR * 1.1} fill={pcb.drill} />

          {/* Right side */}
          <circle cx={37} cy={38} r={viaR} fill={pcb.copperPad} opacity={0.5} />
          <circle cx={37} cy={38} r={drillR} fill={pcb.drill} />

          {/* Bottom cluster */}
          <circle cx={25} cy={66} r={viaR} fill={pcb.copperPad} opacity={0.5} />
          <circle cx={25} cy={66} r={drillR} fill={pcb.drill} />

          <circle cx={37} cy={74} r={viaR} fill={pcb.copperPad} opacity={0.5} />
          <circle cx={37} cy={74} r={drillR} fill={pcb.drill} />

          {/* Scattered small vias */}
          <circle cx={20} cy={44} r={viaR * 0.8} fill={pcb.copperDim} opacity={0.4} />
          <circle cx={20} cy={44} r={drillR * 0.8} fill={pcb.drill} />

          <circle cx={42} cy={44} r={viaR * 0.8} fill={pcb.copperDim} opacity={0.4} />
          <circle cx={42} cy={44} r={drillR * 0.8} fill={pcb.drill} />

          <circle cx={42} cy={26} r={viaR * 0.8} fill={pcb.copperDim} opacity={0.4} />
          <circle cx={42} cy={26} r={drillR * 0.8} fill={pcb.drill} />

          <circle cx={20} cy={60} r={viaR * 0.8} fill={pcb.copperDim} opacity={0.4} />
          <circle cx={20} cy={60} r={drillR * 0.8} fill={pcb.drill} />

          <circle cx={42} cy={60} r={viaR * 0.8} fill={pcb.copperDim} opacity={0.4} />
          <circle cx={42} cy={60} r={drillR * 0.8} fill={pcb.drill} />

          {/* ── Center IC footprint — the "chip" ── */}
          <rect
            x={26} y={40}
            width={10} height={8}
            rx={0.5}
            fill="none"
            stroke={pcb.copper}
            strokeWidth={0.6}
            opacity={0.5}
          />
          {/* IC pins — small pads along left/right edges */}
          {[41, 43, 45, 47].map((py) => (
            <g key={`ic-${py}`}>
              <rect x={24.5} y={py - 0.4} width={1.5} height={0.8} rx={0.2} fill={pcb.copperPad} opacity={0.5} />
              <rect x={36} y={py - 0.4} width={1.5} height={0.8} rx={0.2} fill={pcb.copperPad} opacity={0.5} />
            </g>
          ))}

          {/* ── Silkscreen — subtle "UP" text ── */}
          <text
            x={31} y={44.8}
            textAnchor="middle"
            fontFamily="monospace"
            fontSize={3.2}
            fontWeight={700}
            fill={pcb.silk}
            opacity={0.5}
            letterSpacing={0.5}
          >
            UP
          </text>
        </svg>
      </div>
    </div>
  );
}
