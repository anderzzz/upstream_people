/**
 * The Lab — hand analysis and learning room.
 *
 * Will host: scenario builder, equity trainers, LLM-guided analysis.
 */

import { color, font } from "../theme/tokens.ts";

export function Lab() {
  return (
    <div style={{ padding: "2rem", maxWidth: 1100, margin: "0 auto" }}>
      <h1
        style={{
          fontFamily: font.mono,
          fontSize: "1rem",
          fontWeight: 500,
          color: color.accent.emerald,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          marginBottom: "1.5rem",
        }}
      >
        The Lab
      </h1>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "1rem",
        }}
      >
        <Panel title="Scenario Builder" height={300}>
          Set up any hand, board, and position. Explore what-ifs.
        </Panel>
        <Panel title="Hand Analyzer" height={300}>
          Paste a hand — get properties, equity, EV breakdown.
        </Panel>
        <Panel title="Equity Trainer" height={200}>
          Guess your equity. Get scored. Build intuition.
        </Panel>
        <Panel title="The Analyst" height={200}>
          Ask questions about spots. LLM-powered guide with engine tools.
        </Panel>
      </div>
    </div>
  );
}

function Panel({
  title,
  height,
  children,
}: {
  title: string;
  height: number;
  children: React.ReactNode;
}) {
  return (
    <div
      style={{
        background: color.bg.surface,
        borderRadius: 8,
        border: `1px solid ${color.bg.elevated}`,
        padding: "1.25rem",
        minHeight: height,
      }}
    >
      <h2
        style={{
          fontFamily: font.mono,
          fontSize: "0.75rem",
          fontWeight: 600,
          color: color.text.secondary,
          letterSpacing: "0.06em",
          textTransform: "uppercase",
          marginBottom: "0.75rem",
        }}
      >
        {title}
      </h2>
      <p style={{ fontSize: "0.85rem", color: color.text.muted }}>
        {children}
      </p>
    </div>
  );
}
