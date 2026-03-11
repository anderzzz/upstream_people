/**
 * Strategy Map — game trees, CFR convergence, Nash equilibria.
 *
 * Will host: interactive game tree (D3 hierarchical layout),
 * regret/EV time-series, strategy frequency charts, exploitability curves.
 *
 * The math nerd room.
 */

import { color, font } from "../theme/tokens.ts";

export function StrategyMap() {
  return (
    <div style={{ padding: "2rem", maxWidth: 1200, margin: "0 auto" }}>
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
        Strategy Map
      </h1>

      <div style={{ display: "flex", gap: "1rem" }}>
        {/* Left: game tree */}
        <div
          style={{
            flex: 3,
            background: color.bg.surface,
            borderRadius: 8,
            border: `1px solid ${color.bg.elevated}`,
            padding: "1.25rem",
            minHeight: 500,
          }}
        >
          <h2 style={sectionHeader}>Game Tree</h2>
          <div
            style={{
              height: 420,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              border: `1px dashed ${color.text.muted}`,
              borderRadius: 4,
            }}
          >
            <span
              style={{
                fontFamily: font.mono,
                fontSize: "0.75rem",
                color: color.text.muted,
              }}
            >
              D3 tree layout — zoomable, collapsible nodes
            </span>
          </div>
        </div>

        {/* Right: strategy & convergence */}
        <div style={{ flex: 2, display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div
            style={{
              background: color.bg.surface,
              borderRadius: 8,
              border: `1px solid ${color.bg.elevated}`,
              padding: "1.25rem",
            }}
          >
            <h2 style={sectionHeader}>Strategy at Node</h2>
            <div style={{ display: "flex", gap: 8 }}>
              {[
                { label: "Fold", pct: 23, color: color.action.fold },
                { label: "Call", pct: 45, color: color.action.call },
                { label: "Raise", pct: 32, color: color.action.raise },
              ].map((a) => (
                <div
                  key={a.label}
                  style={{
                    flex: a.pct,
                    background: a.color,
                    borderRadius: 4,
                    padding: "0.5rem",
                    textAlign: "center",
                  }}
                >
                  <div
                    style={{
                      fontFamily: font.mono,
                      fontSize: "0.7rem",
                      fontWeight: 600,
                      color: color.text.primary,
                    }}
                  >
                    {a.pct}%
                  </div>
                  <div
                    style={{
                      fontSize: "0.65rem",
                      color: color.text.primary,
                      opacity: 0.8,
                    }}
                  >
                    {a.label}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div
            style={{
              background: color.bg.surface,
              borderRadius: 8,
              border: `1px solid ${color.bg.elevated}`,
              padding: "1.25rem",
              flex: 1,
            }}
          >
            <h2 style={sectionHeader}>Convergence</h2>
            <div
              style={{
                height: 180,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                border: `1px dashed ${color.text.muted}`,
                borderRadius: 4,
              }}
            >
              <span
                style={{
                  fontFamily: font.mono,
                  fontSize: "0.75rem",
                  color: color.text.muted,
                }}
              >
                Exploitability curve — D3 line chart
              </span>
            </div>
          </div>

          <div
            style={{
              background: color.bg.surface,
              borderRadius: 8,
              border: `1px solid ${color.bg.elevated}`,
              padding: "1.25rem",
            }}
          >
            <h2 style={sectionHeader}>EV by Action</h2>
            <div
              style={{
                height: 120,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                border: `1px dashed ${color.text.muted}`,
                borderRadius: 4,
              }}
            >
              <span
                style={{
                  fontFamily: font.mono,
                  fontSize: "0.75rem",
                  color: color.text.muted,
                }}
              >
                EV bar chart
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

const sectionHeader = {
  fontFamily: font.mono,
  fontSize: "0.7rem",
  fontWeight: 600,
  color: color.text.secondary,
  letterSpacing: "0.06em",
  textTransform: "uppercase" as const,
  marginBottom: "0.75rem",
};
