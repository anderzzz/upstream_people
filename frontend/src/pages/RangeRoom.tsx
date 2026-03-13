/**
 * Range Room — explore PLO's 270K starting hands.
 * Emerald Void: concave panels, bioluminescent accents, deep insets.
 */

import { color, font, shadow, transition } from "../theme/tokens.ts";

export function RangeRoom() {
  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <h1 style={styles.title}>Range Room</h1>
        <p style={styles.subtitle}>270K starting hands. Embeddings. Equity distributions.</p>
      </div>

      <div style={styles.layout}>
        {/* Left: hand space visualization */}
        <div style={styles.mainPanel}>
          <h2 style={styles.sectionHeader}>Hand Embedding Space</h2>
          <div style={styles.vizPlaceholder}>
            <div style={styles.placeholderInner}>
              <span style={styles.placeholderIcon}>{"\u25A6"}</span>
              <span style={styles.placeholderText}>D3 UMAP scatter</span>
              <span style={styles.placeholderSub}>Interactive hand clustering visualization</span>
            </div>
          </div>
        </div>

        {/* Right: controls & distributions */}
        <div style={styles.sidebar}>
          <SidePanel title="Hand Buckets" accent={color.emerald.core}>
            <p style={styles.panelDesc}>
              Rundowns, double-suited, paired, Broadway, trips...
            </p>
            <div style={styles.bucketGrid}>
              {["Rundowns", "Double-suited", "Paired", "Broadway", "Trips", "Disconnected"].map((b) => (
                <div key={b} style={styles.bucketTag}>{b}</div>
              ))}
            </div>
          </SidePanel>

          <SidePanel title="Equity Distribution" accent={color.gold.core} flex>
            <div style={styles.histPlaceholder}>
              <span style={styles.placeholderText}>D3 histogram</span>
            </div>
          </SidePanel>
        </div>
      </div>
    </div>
  );
}

function SidePanel({
  title,
  accent,
  flex,
  children,
}: {
  title: string;
  accent: string;
  flex?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div
      style={{
        ...styles.sidePanel,
        ...(flex ? { flex: 1 } : {}),
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = `${accent}50`;
        e.currentTarget.style.boxShadow = shadow.panelActive(accent);
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = color.bg.border;
        e.currentTarget.style.boxShadow = shadow.inset;
      }}
    >
      <h2 style={styles.sectionHeader}>{title}</h2>
      {children}
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
    color: color.emerald.core,
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
    flex: 2,
    background: color.gradient.panel,
    borderRadius: 8,
    border: `1px solid ${color.bg.border}`,
    padding: "1.25rem",
    boxShadow: shadow.inset,
  },
  sidebar: {
    flex: 1,
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
  vizPlaceholder: {
    height: 400,
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
  panelDesc: {
    fontSize: "0.78rem",
    color: color.text.secondary,
    lineHeight: 1.5,
    marginBottom: "0.75rem",
  },
  bucketGrid: {
    display: "flex",
    flexWrap: "wrap",
    gap: 4,
  },
  bucketTag: {
    fontFamily: font.mono,
    fontSize: "0.6rem",
    color: color.text.secondary,
    background: color.bg.base,
    border: `1px solid ${color.bg.border}`,
    borderRadius: 4,
    padding: "3px 8px",
    letterSpacing: "0.03em",
    boxShadow: shadow.inset,
  },
  histPlaceholder: {
    height: 160,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 5,
    border: `1px dashed ${color.bg.borderMid}`,
    background: `${color.bg.abyss}80`,
    boxShadow: shadow.insetDeep,
  },
};
