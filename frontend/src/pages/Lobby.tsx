/**
 * Lobby — the landing page. Entry point to all rooms.
 */

import { Link } from "react-router-dom";
import { color, font } from "../theme/tokens.ts";
import { Card } from "../components/shared/Card.tsx";

const rooms = [
  {
    to: "/table",
    title: "The Table",
    desc: "Play PLO against AI opponents. Pot-limit. No mercy.",
  },
  {
    to: "/lab",
    title: "The Lab",
    desc: "Analyze hands. Study spots. Train your reads.",
  },
  {
    to: "/ranges",
    title: "Range Room",
    desc: "Explore 270K starting hands. Blockers. Equity distributions.",
  },
  {
    to: "/strategy",
    title: "Strategy Map",
    desc: "Game trees. Nash equilibria. Watch the solver think.",
  },
];

export function Lobby() {
  return (
    <div style={{ padding: "3rem", maxWidth: 900, margin: "0 auto" }}>
      <div style={{ marginBottom: "3rem", textAlign: "center" }}>
        <h1
          style={{
            fontFamily: font.mono,
            fontSize: "1.5rem",
            fontWeight: 300,
            color: color.text.primary,
            letterSpacing: "0.12em",
            marginBottom: "0.5rem",
          }}
        >
          UPSTREAM PEOPLE
        </h1>
        <p style={{ color: color.text.muted, fontSize: "0.85rem" }}>
          Pot-Limit Omaha &middot; Analysis Engine
        </p>
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            gap: 8,
            marginTop: "1.5rem",
          }}
        >
          <Card card="As" scale={0.8} />
          <Card card="Kh" scale={0.8} />
          <Card card="Qd" scale={0.8} />
          <Card card="Jc" scale={0.8} />
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "1rem",
        }}
      >
        {rooms.map((room) => (
          <Link
            key={room.to}
            to={room.to}
            style={{
              display: "block",
              padding: "1.5rem",
              background: color.bg.surface,
              borderRadius: 8,
              border: `1px solid ${color.bg.elevated}`,
              textDecoration: "none",
              transition: "border-color 0.15s, background 0.15s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = color.accent.gold;
              e.currentTarget.style.background = color.bg.elevated;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = color.bg.elevated;
              e.currentTarget.style.background = color.bg.surface;
            }}
          >
            <h2
              style={{
                fontSize: "1rem",
                fontWeight: 600,
                color: color.text.primary,
                marginBottom: "0.4rem",
              }}
            >
              {room.title}
            </h2>
            <p style={{ fontSize: "0.8rem", color: color.text.secondary }}>
              {room.desc}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}
