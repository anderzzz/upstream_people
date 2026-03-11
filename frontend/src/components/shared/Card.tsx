/**
 * Card component — renders a single playing card.
 *
 * For now, pure CSS. When we move to PixiJS for the table canvas,
 * this component stays useful for UI outside the canvas (hand history,
 * range displays, analysis panels).
 */

import { color, font, size } from "../../theme/tokens.ts";

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
  /** Scale factor (1 = default 64x90) */
  scale?: number;
}

export function Card({ card, faceDown = false, scale = 1 }: CardProps) {
  const w = size.card.width * scale;
  const h = size.card.height * scale;

  if (faceDown || !card) {
    return (
      <div
        style={{
          width: w,
          height: h,
          borderRadius: size.radius.md * scale,
          background: `linear-gradient(135deg, ${color.felt.deep} 0%, ${color.felt.base} 50%, ${color.felt.deep} 100%)`,
          border: `1px solid ${color.bg.elevated}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <span
          style={{
            fontFamily: font.mono,
            fontSize: 12 * scale,
            color: color.felt.light,
            opacity: 0.5,
          }}
        >
          UP
        </span>
      </div>
    );
  }

  const rank = card.slice(0, -1);
  const suit = card.slice(-1);
  const suitColor = SUIT_COLORS[suit] ?? color.text.primary;
  const suitSymbol = SUIT_SYMBOLS[suit] ?? "?";

  return (
    <div
      style={{
        width: w,
        height: h,
        borderRadius: size.radius.md * scale,
        background: "#f0f0f0",
        border: `1px solid ${color.bg.elevated}`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 2 * scale,
        boxShadow: "0 2px 8px rgba(0,0,0,0.4)",
        userSelect: "none",
      }}
    >
      <span
        style={{
          fontFamily: font.mono,
          fontSize: 20 * scale,
          fontWeight: 700,
          color: suitColor,
          lineHeight: 1,
        }}
      >
        {rank}
      </span>
      <span
        style={{
          fontSize: 16 * scale,
          color: suitColor,
          lineHeight: 1,
        }}
      >
        {suitSymbol}
      </span>
    </div>
  );
}
