/**
 * Card — a single playing card with depth, texture, and animation.
 *
 * Designed for the Robotic Noir aesthetic: cream parchment face,
 * dark machine-patterned back, crisp suit colors, subtle shadows.
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
      animation: `cardDeal 0.45s cubic-bezier(0.34, 1.56, 0.64, 1) forwards`,
      animationDelay: `${dealDelay}ms`,
      opacity: 0,
    } : {}),
    ...(reveal ? {
      animation: `cardReveal 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) forwards`,
      animationDelay: `${dealDelay}ms`,
    } : {}),
    ...(glow ? {
      boxShadow: `${shadow.card}, 0 0 14px ${glow}50, 0 0 4px ${glow}30`,
    } : {}),
  }), [w, h, r, animated, reveal, dealDelay, glow]);

  if (faceDown || !card) {
    return <CardBack style={baseStyle} scale={scale} />;
  }

  const rank = card.slice(0, -1);
  const suit = card.slice(-1);
  const suitColor = SUIT_COLORS[suit] ?? color.text.primary;
  const suitSymbol = SUIT_SYMBOLS[suit] ?? "?";
  return (
    <div
      className="perspective-container"
      style={baseStyle}
    >
      {/* Card face */}
      <div
        style={{
          width: "100%",
          height: "100%",
          borderRadius: r,
          background: "linear-gradient(170deg, #f2f0eb 0%, #e8e5de 40%, #ddd9d0 100%)",
          border: `1px solid #c8c4bc`,
          boxShadow: glow
            ? `${shadow.card}, 0 0 14px ${glow}50`
            : shadow.card,
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

        {/* Center suit — large */}
        <div
          style={{
            flex: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <span
            style={{
              fontSize: 28 * scale,
              color: suitColor,
              opacity: 0.85,
              filter: `drop-shadow(0 1px 2px rgba(0,0,0,0.1))`,
            }}
          >
            {suitSymbol}
          </span>
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

        {/* Subtle inner border for depth */}
        <div
          style={{
            position: "absolute",
            inset: 1,
            borderRadius: r - 1,
            border: "1px solid rgba(255,255,255,0.3)",
            pointerEvents: "none",
          }}
        />
      </div>
    </div>
  );
}

/** Card back — geometric machine pattern */
function CardBack({ style, scale }: { style: CSSProperties; scale: number }) {
  const r = size.radius.md * scale;

  return (
    <div className="perspective-container" style={style}>
      <div
        style={{
          width: "100%",
          height: "100%",
          borderRadius: r,
          background: color.gradient.cardBack,
          border: `1px solid ${color.bg.borderLight}`,
          boxShadow: shadow.card,
          position: "relative",
          overflow: "hidden",
        }}
      >
        {/* Geometric pattern — concentric border */}
        <div
          style={{
            position: "absolute",
            inset: 4 * scale,
            borderRadius: (r - 3) * scale,
            border: `1.5px solid ${color.bg.borderLight}`,
          }}
        />
        <div
          style={{
            position: "absolute",
            inset: 7 * scale,
            borderRadius: (r - 5) * scale,
            border: `0.5px solid ${color.bg.border}`,
          }}
        />

        {/* Center diamond pattern */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <div
            style={{
              width: 16 * scale,
              height: 16 * scale,
              border: `1.5px solid ${color.text.dim}`,
              transform: "rotate(45deg)",
            }}
          />
        </div>

        {/* Subtle diagonal lines — machine texture */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            opacity: 0.04,
            background: `repeating-linear-gradient(
              45deg,
              transparent,
              transparent 3px,
              ${color.text.muted} 3px,
              ${color.text.muted} 3.5px
            )`,
            borderRadius: r,
          }}
        />
      </div>
    </div>
  );
}
