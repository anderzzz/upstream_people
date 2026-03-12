/**
 * Lobby — the landing page. Sleek, dark, robotic.
 */

import { Link } from "react-router-dom";
import { color, font, shadow, transition } from "../theme/tokens.ts";
import { Card } from "../components/shared/Card.tsx";

const rooms = [
  {
    to: "/table",
    title: "The Table",
    desc: "Play PLO against AI opponents. Pot-limit. No mercy.",
    icon: "\u2660",
    accentColor: color.accent.gold,
  },
  {
    to: "/lab",
    title: "The Lab",
    desc: "Analyze hands. Study spots. Train your reads.",
    icon: "\u2394",
    accentColor: color.accent.cyan,
  },
  {
    to: "/ranges",
    title: "Range Room",
    desc: "Explore 270K starting hands. Blockers. Equity distributions.",
    icon: "\u25A6",
    accentColor: color.accent.emerald,
  },
  {
    to: "/strategy",
    title: "Strategy Map",
    desc: "Game trees. Nash equilibria. Watch the solver think.",
    icon: "\u2261",
    accentColor: color.accent.silver,
  },
];

export function Lobby() {
  return (
    <div style={styles.page}>
      {/* Hero */}
      <div style={styles.hero}>
        <div style={styles.heroInner}>
          {/* Decorative line */}
          <div style={styles.decorLine} />

          <h1 style={styles.title}>UPSTREAM PEOPLE</h1>
          <p style={styles.subtitle}>
            Pot-Limit Omaha <span style={styles.dot}>&middot;</span> Analysis Engine
          </p>

          {/* Display cards with staggered deal animation */}
          <div style={styles.cardRow}>
            <Card card="As" scale={0.9} animated dealDelay={100} />
            <Card card="Kh" scale={0.9} animated dealDelay={200} />
            <Card card="Qd" scale={0.9} animated dealDelay={300} />
            <Card card="Jc" scale={0.9} animated dealDelay={400} />
          </div>

          <div style={styles.decorLine} />
        </div>
      </div>

      {/* Room grid */}
      <div style={styles.grid}>
        {rooms.map((room) => (
          <Link
            key={room.to}
            to={room.to}
            style={styles.roomCard}
            onMouseEnter={(e) => {
              const el = e.currentTarget;
              el.style.borderColor = room.accentColor;
              el.style.background = color.bg.elevated;
              el.style.transform = "translateY(-2px)";
              el.style.boxShadow = shadow.glow(room.accentColor);
            }}
            onMouseLeave={(e) => {
              const el = e.currentTarget;
              el.style.borderColor = color.bg.border;
              el.style.background = color.gradient.panel;
              el.style.transform = "translateY(0)";
              el.style.boxShadow = "none";
            }}
          >
            <div style={styles.roomHeader}>
              <span style={{ ...styles.roomIcon, color: room.accentColor }}>
                {room.icon}
              </span>
              <h2 style={styles.roomTitle}>{room.title}</h2>
            </div>
            <p style={styles.roomDesc}>{room.desc}</p>
            <span style={{ ...styles.roomArrow, color: room.accentColor }}>
              &rarr;
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    padding: "2.5rem 2rem",
    maxWidth: 880,
    margin: "0 auto",
    animation: "fadeIn 0.4s ease",
  },

  hero: {
    marginBottom: "2.5rem",
    textAlign: "center",
  },

  heroInner: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "1rem",
  },

  decorLine: {
    width: 40,
    height: 1,
    background: `linear-gradient(90deg, transparent, ${color.text.dim}, transparent)`,
  },

  title: {
    fontFamily: font.mono,
    fontSize: "1.4rem",
    fontWeight: 300,
    color: color.text.primary,
    letterSpacing: "0.18em",
  },

  subtitle: {
    color: color.text.muted,
    fontSize: "0.8rem",
    letterSpacing: "0.04em",
  },

  dot: {
    color: color.accent.gold,
  },

  cardRow: {
    display: "flex",
    justifyContent: "center",
    gap: 10,
    marginTop: "0.5rem",
    marginBottom: "0.25rem",
  },

  grid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "0.75rem",
  },

  roomCard: {
    display: "flex",
    flexDirection: "column",
    padding: "1.25rem 1.5rem",
    background: color.gradient.panel,
    borderRadius: 10,
    border: `1px solid ${color.bg.border}`,
    textDecoration: "none",
    transition: transition.normal,
    position: "relative",
  },

  roomHeader: {
    display: "flex",
    alignItems: "center",
    gap: "0.6rem",
    marginBottom: "0.5rem",
  },

  roomIcon: {
    fontFamily: font.mono,
    fontSize: "1rem",
    opacity: 0.7,
  },

  roomTitle: {
    fontSize: "0.9rem",
    fontWeight: 600,
    color: color.text.primary,
  },

  roomDesc: {
    fontSize: "0.78rem",
    color: color.text.secondary,
    lineHeight: 1.5,
    flex: 1,
  },

  roomArrow: {
    fontSize: "0.85rem",
    opacity: 0.4,
    marginTop: "0.75rem",
    fontFamily: font.mono,
  },
};
