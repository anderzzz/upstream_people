/**
 * The Lab — hand analysis and learning room.
 * Emerald Void: each tool has a bioluminescent accent, concave panels.
 */

import { color, font, shadow, transition } from "../theme/tokens.ts";

const tools = [
  {
    title: "Scenario Builder",
    desc: "Set up any hand, board, and position. Explore what-ifs.",
    icon: "\u2692",
    accent: color.emerald.bright,
  },
  {
    title: "Hand Analyzer",
    desc: "Paste a hand — get properties, equity, EV breakdown.",
    icon: "\u2263",
    accent: color.gold.core,
  },
  {
    title: "Equity Trainer",
    desc: "Guess your equity. Get scored. Build intuition.",
    icon: "\u25CE",
    accent: color.emerald.core,
  },
  {
    title: "The Analyst",
    desc: "Ask questions about spots. LLM-powered guide with engine tools.",
    icon: "\u2318",
    accent: color.accent.silver,
  },
];

export function Lab() {
  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <h1 style={styles.title}>The Lab</h1>
        <p style={styles.subtitle}>Analysis tools and training environments</p>
      </div>

      <div style={styles.grid}>
        {tools.map((tool) => (
          <div
            key={tool.title}
            style={styles.panel}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = `${tool.accent}50`;
              e.currentTarget.style.boxShadow = shadow.panelActive(tool.accent);
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = color.bg.border;
              e.currentTarget.style.boxShadow = shadow.inset;
            }}
          >
            <div style={styles.panelHeader}>
              <span
                style={{
                  ...styles.panelIcon,
                  color: tool.accent,
                  filter: `drop-shadow(0 0 4px ${tool.accent}40)`,
                }}
              >
                {tool.icon}
              </span>
              <h2 style={styles.panelTitle}>{tool.title}</h2>
            </div>
            <p style={styles.panelDesc}>{tool.desc}</p>
            <div style={styles.panelPlaceholder}>
              <span style={styles.placeholderText}>Coming soon</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    padding: "2rem",
    maxWidth: 1000,
    margin: "0 auto",
    animation: "fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1)",
  },
  header: {
    marginBottom: "1.5rem",
  },
  title: {
    fontFamily: font.mono,
    fontSize: "0.9rem",
    fontWeight: 600,
    color: color.emerald.bright,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
    marginBottom: "0.3rem",
  },
  subtitle: {
    fontSize: "0.78rem",
    color: color.text.muted,
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "0.75rem",
  },
  panel: {
    background: color.gradient.panel,
    borderRadius: 8,
    border: `1px solid ${color.bg.border}`,
    padding: "1.25rem",
    display: "flex",
    flexDirection: "column",
    transition: transition.normal,
    cursor: "default",
    boxShadow: shadow.inset,
  },
  panelHeader: {
    display: "flex",
    alignItems: "center",
    gap: "0.5rem",
    marginBottom: "0.5rem",
  },
  panelIcon: {
    fontSize: "0.9rem",
    opacity: 0.8,
  },
  panelTitle: {
    fontFamily: font.mono,
    fontSize: "0.72rem",
    fontWeight: 600,
    color: color.text.primary,
    letterSpacing: "0.06em",
    textTransform: "uppercase",
  },
  panelDesc: {
    fontSize: "0.78rem",
    color: color.text.secondary,
    lineHeight: 1.5,
    marginBottom: "1rem",
  },
  panelPlaceholder: {
    flex: 1,
    minHeight: 120,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 5,
    border: `1px dashed ${color.bg.borderMid}`,
    background: `${color.bg.abyss}80`,
    boxShadow: shadow.insetDeep,
  },
  placeholderText: {
    fontFamily: font.mono,
    fontSize: "0.65rem",
    color: color.text.dim,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
  },
};
