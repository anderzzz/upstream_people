/**
 * Strategy Map — game trees, CFR convergence, Nash equilibria.
 * Emerald Void: deep concave panels, emerald data bars, gold for EV.
 */

import { color, font, shadow, transition } from "../theme/tokens.ts";

export function StrategyMap() {
  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <h1 style={styles.title}>Strategy Map</h1>
        <p style={styles.subtitle}>Game trees. Nash equilibria. Solver convergence.</p>
      </div>

      <div style={styles.layout}>
        {/* Left: game tree */}
        <div style={styles.mainPanel}>
          <h2 style={styles.sectionHeader}>Game Tree</h2>
          <div style={styles.treePlaceholder}>
            <div style={styles.placeholderInner}>
              <span style={styles.placeholderIcon}>{"\u2261"}</span>
              <span style={styles.placeholderText}>D3 tree layout</span>
              <span style={styles.placeholderSub}>Zoomable, collapsible decision nodes</span>
            </div>
          </div>
        </div>

        {/* Right: strategy & convergence */}
        <div style={styles.sidebar}>
          {/* Strategy at node */}
          <div style={styles.sidePanel}>
            <h2 style={styles.sectionHeader}>Strategy at Node</h2>
            <div style={styles.strategyBars}>
              {[
                { label: "Fold", pct: 23, barColor: color.action.fold },
                { label: "Call", pct: 45, barColor: color.action.call },
                { label: "Raise", pct: 32, barColor: color.action.raise },
              ].map((a) => (
                <div key={a.label} style={styles.barRow}>
                  <span style={styles.barLabel}>{a.label}</span>
                  <div style={styles.barTrack}>
                    <div
                      style={{
                        ...styles.barFill,
                        width: `${a.pct}%`,
                        background: a.barColor,
                      }}
                    />
                  </div>
                  <span style={styles.barPct}>{a.pct}%</span>
                </div>
              ))}
            </div>
          </div>

          {/* Convergence */}
          <div style={{ ...styles.sidePanel, flex: 1 }}>
            <h2 style={styles.sectionHeader}>Convergence</h2>
            <div style={styles.chartPlaceholder}>
              <span style={styles.placeholderText}>Exploitability curve</span>
            </div>
          </div>

          {/* EV */}
          <div style={styles.sidePanel}>
            <h2 style={styles.sectionHeader}>EV by Action</h2>
            <div style={styles.evBars}>
              {[
                { label: "Fold", ev: 0, barColor: color.action.fold },
                { label: "Call", ev: 42, barColor: color.action.call },
                { label: "Raise", ev: 78, barColor: color.action.raise },
              ].map((a) => (
                <div key={a.label} style={styles.evRow}>
                  <span style={styles.barLabel}>{a.label}</span>
                  <div style={styles.barTrack}>
                    <div
                      style={{
                        ...styles.barFill,
                        width: `${(a.ev / 100) * 100}%`,
                        background: `linear-gradient(90deg, ${a.barColor}60, ${a.barColor})`,
                      }}
                    />
                  </div>
                  <span style={styles.evValue}>{a.ev > 0 ? "+" : ""}{a.ev}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    padding: "2rem",
    maxWidth: 1100,
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
    color: color.accent.silver,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
    marginBottom: "0.3rem",
  },
  subtitle: {
    fontSize: "0.78rem",
    color: color.text.muted,
  },
  layout: {
    display: "flex",
    gap: "0.75rem",
  },
  mainPanel: {
    flex: 3,
    background: color.gradient.panel,
    borderRadius: 8,
    border: `1px solid ${color.bg.border}`,
    padding: "1.25rem",
    boxShadow: shadow.inset,
  },
  sidebar: {
    flex: 2,
    display: "flex",
    flexDirection: "column",
    gap: "0.75rem",
  },
  sidePanel: {
    background: color.gradient.panel,
    borderRadius: 8,
    border: `1px solid ${color.bg.border}`,
    padding: "1.25rem",
    transition: transition.normal,
    boxShadow: shadow.inset,
  },
  sectionHeader: {
    fontFamily: font.mono,
    fontSize: "0.68rem",
    fontWeight: 600,
    color: color.text.secondary,
    letterSpacing: "0.06em",
    textTransform: "uppercase",
    marginBottom: "0.75rem",
  },
  treePlaceholder: {
    height: 420,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 6,
    border: `1px dashed ${color.bg.borderMid}`,
    background: `${color.bg.abyss}80`,
    boxShadow: shadow.insetDeep,
  },
  placeholderInner: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "0.5rem",
  },
  placeholderIcon: {
    fontSize: "1.5rem",
    color: color.emerald.dim,
    opacity: 0.5,
    filter: `drop-shadow(0 0 6px ${color.emerald.deep})`,
  },
  placeholderText: {
    fontFamily: font.mono,
    fontSize: "0.65rem",
    color: color.text.dim,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
  },
  placeholderSub: {
    fontSize: "0.7rem",
    color: color.text.dim,
    opacity: 0.6,
  },
  chartPlaceholder: {
    height: 140,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 5,
    border: `1px dashed ${color.bg.borderMid}`,
    background: `${color.bg.abyss}80`,
    boxShadow: shadow.insetDeep,
  },

  // Strategy bars
  strategyBars: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  barRow: {
    display: "flex",
    alignItems: "center",
    gap: 8,
  },
  barLabel: {
    fontFamily: font.mono,
    fontSize: "0.62rem",
    color: color.text.secondary,
    width: 36,
    textTransform: "uppercase",
    letterSpacing: "0.04em",
  },
  barTrack: {
    flex: 1,
    height: 6,
    background: color.bg.base,
    borderRadius: 3,
    overflow: "hidden",
    boxShadow: shadow.inset,
  },
  barFill: {
    height: "100%",
    borderRadius: 3,
    transition: "width 0.5s cubic-bezier(0.16, 1, 0.3, 1)",
  },
  barPct: {
    fontFamily: font.mono,
    fontSize: "0.62rem",
    color: color.text.muted,
    width: 30,
    textAlign: "right",
  },

  // EV bars
  evBars: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  evRow: {
    display: "flex",
    alignItems: "center",
    gap: 8,
  },
  evValue: {
    fontFamily: font.mono,
    fontSize: "0.62rem",
    color: color.gold.core,
    width: 30,
    textAlign: "right",
  },
};
