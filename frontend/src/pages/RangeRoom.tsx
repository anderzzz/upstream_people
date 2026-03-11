/**
 * Range Room — explore PLO's 270K starting hands.
 *
 * Will host: UMAP scatter plots of hand embeddings, bucket selectors,
 * equity distribution histograms, blocker diagrams.
 *
 * This is where D3.js shines.
 */

import { color, font } from "../theme/tokens.ts";

export function RangeRoom() {
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
        Range Room
      </h1>

      <div style={{ display: "flex", gap: "1rem" }}>
        {/* Left: hand space visualization */}
        <div
          style={{
            flex: 2,
            background: color.bg.surface,
            borderRadius: 8,
            border: `1px solid ${color.bg.elevated}`,
            padding: "1.25rem",
            minHeight: 500,
          }}
        >
          <h2 style={sectionHeader}>Hand Embedding Space</h2>
          <div
            style={{
              height: 400,
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
              D3 UMAP scatter — mount point
            </span>
          </div>
        </div>

        {/* Right: controls & distributions */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div
            style={{
              background: color.bg.surface,
              borderRadius: 8,
              border: `1px solid ${color.bg.elevated}`,
              padding: "1.25rem",
            }}
          >
            <h2 style={sectionHeader}>Hand Buckets</h2>
            <p style={{ fontSize: "0.8rem", color: color.text.muted }}>
              Rundowns, double-suited, paired, Broadway, trips...
              <br />
              Bucket selector will go here.
            </p>
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
            <h2 style={sectionHeader}>Equity Distribution</h2>
            <div
              style={{
                height: 200,
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
                D3 histogram
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
