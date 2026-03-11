/**
 * The Table — live PLO game room.
 *
 * Will eventually host a PixiJS canvas for the felt, cards, chips.
 * For now: placeholder layout proving the route and theme work.
 */

import { color, font } from "../theme/tokens.ts";
import { Card } from "../components/shared/Card.tsx";

export function TableRoom() {
  return (
    <div
      style={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        background: `radial-gradient(ellipse at center, ${color.felt.base} 0%, ${color.bg.base} 70%)`,
      }}
    >
      {/* The felt area — where PixiJS canvas will mount */}
      <div
        style={{
          width: 720,
          height: 420,
          borderRadius: 210,
          background: `radial-gradient(ellipse at center, ${color.felt.light}22 0%, ${color.felt.deep} 100%)`,
          border: `2px solid ${color.felt.light}44`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: "1.5rem",
          position: "relative",
        }}
      >
        <span
          style={{
            fontFamily: font.mono,
            fontSize: "0.7rem",
            color: color.text.muted,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
          }}
        >
          Community Cards
        </span>
        <div style={{ display: "flex", gap: 8 }}>
          <Card card="Td" />
          <Card card="9s" />
          <Card card="2h" />
          <Card faceDown />
          <Card faceDown />
        </div>

        {/* Pot display */}
        <div
          style={{
            fontFamily: font.mono,
            fontSize: "1.1rem",
            fontWeight: 600,
            color: color.accent.gold,
          }}
        >
          Pot: 1,250
        </div>
      </div>

      {/* Player's hole cards */}
      <div
        style={{
          marginTop: "2rem",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "0.5rem",
        }}
      >
        <div style={{ display: "flex", gap: 6 }}>
          <Card card="As" scale={1.1} />
          <Card card="Kh" scale={1.1} />
          <Card card="Qd" scale={1.1} />
          <Card card="Jc" scale={1.1} />
        </div>
        <span
          style={{
            fontFamily: font.mono,
            fontSize: "0.7rem",
            color: color.text.muted,
          }}
        >
          Your Hand
        </span>
      </div>
    </div>
  );
}
