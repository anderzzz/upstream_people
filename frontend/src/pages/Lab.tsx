/**
 * The Lab — hand analysis dashboard.
 *
 * Text-first card input, progressive disclosure of results:
 *   1. Starting hand profile (always, with 4 cards)
 *   2. Post-flop analysis (when board has 3+ cards)
 *   3. Equity by next card heatmap (flop/turn)
 *   4. Action EV (when pot/bet info provided)
 */

import { useState, useCallback, useMemo } from "react";
import { Card } from "../components/shared/Card.tsx";
import { color, font, shadow, transition } from "../theme/tokens.ts";
import {
  useEquity,
  useHandProperties,
  useStartingHand,
  useActionEV,
  useEquityMap,
  type EquityMapCard,
} from "../hooks/useAnalysis.ts";

// ─── Card parsing (mirrors backend) ─────────────────────────
const RANKS = "23456789TJQKA";
const SUITS = "cdhs";

function isValidCard(s: string): boolean {
  if (s.length !== 2) return false;
  return RANKS.includes(s.charAt(0).toUpperCase()) && SUITS.includes(s.charAt(1).toLowerCase());
}

function parseCardInput(raw: string): string[] {
  const s = raw.trim();
  if (!s) return [];
  // Try space-separated
  if (s.includes(" ")) {
    return s.split(/\s+/).map((t) => {
      if (t.length < 2) return t;
      return t.charAt(0).toUpperCase() + t.slice(1).toLowerCase();
    });
  }
  // Try consecutive 2-char
  if (s.length % 2 === 0 && s.length >= 2) {
    const cards: string[] = [];
    for (let i = 0; i < s.length; i += 2) {
      cards.push(s.charAt(i).toUpperCase() + s.charAt(i + 1).toLowerCase());
    }
    return cards;
  }
  return [];
}

function validateCards(cards: string[]): string | null {
  for (const c of cards) {
    if (!isValidCard(c)) return `Invalid card: "${c}"`;
  }
  const unique = new Set(cards.map((c) => c.toUpperCase()));
  if (unique.size !== cards.length) return "Duplicate cards";
  return null;
}

// ─── Main component ─────────────────────────────────────────

export function Lab() {
  // Input state
  const [handInput, setHandInput] = useState("");
  const [boardInput, setBoardInput] = useState("");
  const [opponents, setOpponents] = useState(1);
  const [potSize, setPotSize] = useState("");
  const [betToCall, setBetToCall] = useState("");
  const [stackSize, setStackSize] = useState("");

  // Parse inputs
  const handCards = useMemo(() => parseCardInput(handInput), [handInput]);
  const boardCards = useMemo(() => parseCardInput(boardInput), [boardInput]);
  const handValid = handCards.length === 4 && !validateCards(handCards);
  const boardValid =
    boardCards.length === 0 ||
    ([3, 4, 5].includes(boardCards.length) && !validateCards(boardCards));
  const allCards = [...handCards, ...boardCards];
  const allUnique = new Set(allCards.map((c) => c.toUpperCase())).size === allCards.length;
  const handError = handCards.length > 0 ? validateCards(handCards) : null;
  const boardError = boardCards.length > 0 ? validateCards(boardCards) : null;
  const overlapError =
    handValid && boardValid && !allUnique ? "Hand and board share cards" : null;
  const inputReady = handValid && boardValid && allUnique;

  // Street detection
  const street =
    boardCards.length === 0
      ? "preflop"
      : boardCards.length === 3
        ? "flop"
        : boardCards.length === 4
          ? "turn"
          : "river";

  // API hooks
  const startingHand = useStartingHand();
  const equity = useEquity();
  const handProps = useHandProperties();
  const actionEv = useActionEV();
  const equityMap = useEquityMap();

  // Analyze
  const analyze = useCallback(() => {
    if (!inputReady) return;

    // Always fetch starting hand profile
    startingHand.execute({ hand: handCards });

    // Equity
    equity.execute({ hand: handCards, board: boardCards, opponents });

    // Hand properties (post-flop only)
    if (boardCards.length >= 3) {
      handProps.execute({ hand: handCards, board: boardCards });
    }

    // Equity map (flop/turn only)
    if (boardCards.length === 3 || boardCards.length === 4) {
      equityMap.execute({
        hand: handCards,
        board: boardCards,
        opponents,
        samples: 3000,
      });
    }

    // Action EV (if pot info provided)
    const pot = parseFloat(potSize);
    const bet = parseFloat(betToCall) || 0;
    const stack = parseFloat(stackSize) || 100;
    if (pot > 0) {
      actionEv.execute({
        hand: handCards,
        board: boardCards,
        pot,
        to_call: bet,
        stack,
        bb_size: 1,
        opponents,
      });
    }
  }, [inputReady, handCards, boardCards, opponents, potSize, betToCall, stackSize]);

  const anyLoading =
    startingHand.loading ||
    equity.loading ||
    handProps.loading ||
    actionEv.loading ||
    equityMap.loading;

  return (
    <div style={styles.page}>
      {/* Header */}
      <div style={styles.header}>
        <h1 style={styles.title}>The Lab</h1>
        <p style={styles.subtitle}>Hand analysis and equity computation</p>
      </div>

      <div style={styles.layout}>
        {/* ─── Left: Input Panel ─── */}
        <div style={styles.inputPanel}>
          {/* Hand input */}
          <div style={styles.inputGroup}>
            <label style={styles.label}>Hero Hand</label>
            <input
              type="text"
              style={styles.input}
              placeholder="As Ks Qh Jh"
              value={handInput}
              onChange={(e) => setHandInput(e.target.value)}
            />
            {handError && handCards.length === 4 && (
              <span style={styles.error}>{handError}</span>
            )}
            {handCards.length > 0 && handCards.length !== 4 && (
              <span style={styles.hint}>Need exactly 4 cards</span>
            )}
            {/* Card preview */}
            {handCards.length > 0 && (
              <div style={styles.cardRow}>
                {handCards.map((c, i) => (
                  <Card
                    key={i}
                    card={isValidCard(c) ? c : undefined}
                    scale={0.85}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Board input */}
          <div style={styles.inputGroup}>
            <label style={styles.label}>Board</label>
            <input
              type="text"
              style={styles.input}
              placeholder="Td 9s 2h  (0, 3, 4, or 5 cards)"
              value={boardInput}
              onChange={(e) => setBoardInput(e.target.value)}
            />
            {boardError && <span style={styles.error}>{boardError}</span>}
            {overlapError && <span style={styles.error}>{overlapError}</span>}
            {boardCards.length > 0 && (
              <div style={styles.cardRow}>
                {boardCards.map((c, i) => (
                  <Card key={i} card={isValidCard(c) ? c : undefined} scale={0.85} />
                ))}
              </div>
            )}
          </div>

          {/* Opponents slider */}
          <div style={styles.inputGroup}>
            <label style={styles.label}>
              Opponents: <span style={styles.sliderValue}>{opponents}</span>
            </label>
            <input
              type="range"
              min={1}
              max={5}
              value={opponents}
              onChange={(e) => setOpponents(parseInt(e.target.value))}
              style={styles.slider}
            />
          </div>

          {/* Pot/bet (optional) */}
          <div style={styles.inputGroup}>
            <label style={styles.label}>Action Context (optional)</label>
            <div style={styles.row}>
              <input
                type="text"
                style={{ ...styles.input, ...styles.smallInput }}
                placeholder="Pot"
                value={potSize}
                onChange={(e) => setPotSize(e.target.value)}
              />
              <input
                type="text"
                style={{ ...styles.input, ...styles.smallInput }}
                placeholder="To call"
                value={betToCall}
                onChange={(e) => setBetToCall(e.target.value)}
              />
              <input
                type="text"
                style={{ ...styles.input, ...styles.smallInput }}
                placeholder="Stack"
                value={stackSize}
                onChange={(e) => setStackSize(e.target.value)}
              />
            </div>
          </div>

          {/* Street indicator */}
          <div style={styles.streetBadge}>
            {street.toUpperCase()}
          </div>

          {/* Analyze button */}
          <button
            style={{
              ...styles.analyzeBtn,
              opacity: inputReady && !anyLoading ? 1 : 0.4,
              cursor: inputReady && !anyLoading ? "pointer" : "not-allowed",
            }}
            onClick={analyze}
            disabled={!inputReady || anyLoading}
          >
            {anyLoading ? "Computing..." : "Analyze"}
          </button>
        </div>

        {/* ─── Right: Results ─── */}
        <div style={styles.resultsPanel}>
          {/* Starting Hand Profile */}
          {startingHand.data && (
            <ResultSection title="Starting Hand" accent={color.emerald.bright}>
              <div style={styles.resultGrid}>
                <Stat label="Category" value={fmtEnum(startingHand.data.category)} />
                <Stat label="Suits" value={startingHand.data.suits_description} />
                <Stat
                  label="Est. Equity"
                  value={pct(startingHand.data.preflop_equity_estimate)}
                  highlight
                />
                {startingHand.data.has_ace && <Tag text="Has Ace" />}
                {startingHand.data.has_suited_ace && <Tag text="Suited Ace" accent={color.emerald.core} />}
                {startingHand.data.is_connected && <Tag text="Connected" accent={color.emerald.mid} />}
              </div>
              {/* Precomputed equities by opponent count */}
              {startingHand.data.precomputed_equities && (
                <div style={{ marginTop: 8 }}>
                  <span style={styles.miniLabel}>Equity vs N opponents (precomputed)</span>
                  <div style={styles.barRow}>
                    {Object.entries(startingHand.data.precomputed_equities).map(
                      ([n, eq]) => (
                        <div key={n} style={styles.barCol}>
                          <div
                            style={{
                              ...styles.bar,
                              height: `${eq.equity * 100}%`,
                              background:
                                parseInt(n) === opponents
                                  ? color.emerald.bright
                                  : color.emerald.dim,
                            }}
                          />
                          <span style={styles.barLabel}>{n}</span>
                        </div>
                      ),
                    )}
                  </div>
                </div>
              )}
            </ResultSection>
          )}

          {/* Equity */}
          {equity.data && (
            <ResultSection title="Equity" accent={color.gold.core}>
              <div style={styles.resultGrid}>
                <Stat label="Equity" value={pct(equity.data.equity)} highlight />
                <Stat label="Win" value={pct(equity.data.win)} />
                <Stat label="Tie" value={pct(equity.data.tie)} />
                <Stat label="Loss" value={pct(equity.data.loss)} />
                <Stat label="Samples" value={equity.data.samples.toLocaleString()} />
                {equity.data.confidence_interval && (
                  <Stat
                    label="95% CI"
                    value={`${pct(equity.data.confidence_interval[0])} - ${pct(equity.data.confidence_interval[1])}`}
                  />
                )}
              </div>
            </ResultSection>
          )}

          {/* Hand Properties */}
          {handProps.data && (
            <ResultSection title="Hand Properties" accent={color.emerald.core}>
              <div style={styles.resultGrid}>
                <Stat
                  label="Made Hand"
                  value={fmtEnum(handProps.data.made_hand)}
                  highlight
                />
                {handProps.data.is_nutted && <Tag text="Nutted" accent={color.gold.core} />}
                {handProps.data.draws.length > 0 && (
                  <Stat
                    label="Draws"
                    value={handProps.data.draws.map(fmtEnum).join(", ")}
                  />
                )}
                {handProps.data.total_outs > 0 && (
                  <>
                    <Stat label="Total Outs" value={String(handProps.data.total_outs)} />
                    <Stat
                      label="Nut Outs"
                      value={String(handProps.data.nut_draw_outs)}
                    />
                    <Stat
                      label="Draw Equity (2/4)"
                      value={pct(handProps.data.draw_equity_estimate)}
                    />
                  </>
                )}
              </div>
              {/* Blocker info */}
              {handProps.data.blocker_score > 0 && (
                <div style={{ marginTop: 6 }}>
                  <span style={styles.miniLabel}>Blockers</span>
                  <div style={styles.resultGrid}>
                    <Stat
                      label="Score"
                      value={handProps.data.blocker_score.toFixed(2)}
                    />
                    {handProps.data.blocks_nut_flush && (
                      <Tag text="Blocks Nut Flush" accent={color.emerald.core} />
                    )}
                    {handProps.data.blocks_nut_straight && (
                      <Tag text="Blocks Nut Straight" />
                    )}
                    {handProps.data.is_good_bluff_candidate && (
                      <Tag text="Good Bluff Candidate" accent={color.gold.core} />
                    )}
                  </div>
                </div>
              )}
            </ResultSection>
          )}

          {/* Action EV */}
          {actionEv.data && actionEv.data.length > 0 && (
            <ResultSection title="Action EV" accent={color.gold.bright}>
              <div style={styles.evTable}>
                {[...actionEv.data]
                  .sort((a, b) => b.ev - a.ev)
                  .map((a) => (
                    <div key={a.action} style={styles.evRow}>
                      <span style={styles.evAction}>{fmtEnum(a.action)}</span>
                      <span
                        style={{
                          ...styles.evValue,
                          color: a.ev > 0 ? color.emerald.bright : a.ev < 0 ? "#c44" : color.text.secondary,
                        }}
                      >
                        {a.ev > 0 ? "+" : ""}
                        {a.ev.toFixed(2)}
                      </span>
                      <span style={styles.evBB}>
                        ({a.ev_bb > 0 ? "+" : ""}
                        {a.ev_bb.toFixed(2)} bb)
                      </span>
                    </div>
                  ))}
              </div>
            </ResultSection>
          )}

          {/* Equity by Next Card Heatmap */}
          {equityMap.data && (
            <ResultSection title="Equity by Next Card" accent={color.emerald.neon}>
              <span style={styles.miniLabel}>
                Baseline: {pct(equityMap.data.baseline_equity)}
              </span>
              <EquityHeatmap
                cards={equityMap.data.cards}
                deadCards={new Set(allCards.map((c) => c.toUpperCase()))}
                baseline={equityMap.data.baseline_equity}
              />
            </ResultSection>
          )}

          {/* Loading / Error states */}
          {anyLoading && (
            <div style={styles.loadingBar}>
              <div style={styles.loadingPulse} />
            </div>
          )}
          {(startingHand.error || equity.error || handProps.error) && (
            <div style={styles.errorBox}>
              {startingHand.error || equity.error || handProps.error}
            </div>
          )}

          {/* Empty state */}
          {!startingHand.data && !equity.data && !anyLoading && (
            <div style={styles.emptyState}>
              <span style={styles.emptyIcon}>&#x2263;</span>
              <p style={styles.emptyText}>
                Enter a hand and click Analyze
              </p>
              <p style={styles.emptyHint}>
                e.g. As Ks Qh Jh
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Sub-components ──────────────────────────────────────────

function ResultSection({
  title,
  accent,
  children,
}: {
  title: string;
  accent: string;
  children: React.ReactNode;
}) {
  return (
    <div style={styles.section}>
      <div style={styles.sectionHeader}>
        <div
          style={{
            width: 3,
            height: 14,
            borderRadius: 1,
            background: accent,
            boxShadow: `0 0 6px ${accent}40`,
          }}
        />
        <h3 style={styles.sectionTitle}>{title}</h3>
      </div>
      {children}
    </div>
  );
}

function Stat({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div style={styles.stat}>
      <span style={styles.statLabel}>{label}</span>
      <span
        style={{
          ...styles.statValue,
          ...(highlight ? { color: color.emerald.bright, fontSize: "0.82rem" } : {}),
        }}
      >
        {value}
      </span>
    </div>
  );
}

function Tag({ text, accent }: { text: string; accent?: string }) {
  return (
    <span
      style={{
        ...styles.tag,
        borderColor: accent ? `${accent}40` : color.bg.borderMid,
        color: accent || color.text.secondary,
      }}
    >
      {text}
    </span>
  );
}

function EquityHeatmap({
  cards,
  deadCards,
  baseline,
}: {
  cards: EquityMapCard[];
  deadCards: Set<string>;
  baseline: number;
}) {
  // Build 13x4 grid (ranks x suits)
  const rankLabels = "A K Q J T 9 8 7 6 5 4 3 2".split(" ");
  const suitLabels = ["s", "h", "d", "c"];
  const suitSymbols: Record<string, string> = {
    s: "\u2660",
    h: "\u2665",
    d: "\u2666",
    c: "\u2663",
  };

  // Index cards by rank+suit string
  const cardMap = new Map<string, EquityMapCard>();
  for (const c of cards) {
    cardMap.set(c.card.toUpperCase(), c);
  }

  return (
    <div style={styles.heatmapGrid}>
      {/* Header row: suit symbols */}
      <div style={styles.heatmapCorner} />
      {suitLabels.map((s) => (
        <div key={s} style={styles.heatmapSuitHeader}>
          {suitSymbols[s]}
        </div>
      ))}

      {/* Data rows */}
      {rankLabels.map((rank) => (
        <>
          <div key={`label-${rank}`} style={styles.heatmapRankLabel}>
            {rank}
          </div>
          {suitLabels.map((suit) => {
            const key = `${rank}${suit}`.toUpperCase();
            const isDead = deadCards.has(key);
            const entry = cardMap.get(key);

            if (isDead) {
              return (
                <div key={key} style={styles.heatmapCellDead}>
                  &middot;
                </div>
              );
            }

            if (!entry) {
              return <div key={key} style={styles.heatmapCellDead} />;
            }

            const delta = entry.equity - baseline;
            const intensity = Math.min(Math.abs(delta) / 0.15, 1);
            const bg =
              delta > 0.005
                ? `rgba(80, 255, 176, ${0.1 + intensity * 0.5})`
                : delta < -0.005
                  ? `rgba(200, 60, 60, ${0.1 + intensity * 0.5})`
                  : `rgba(100, 100, 120, 0.15)`;

            return (
              <div
                key={key}
                style={{
                  ...styles.heatmapCell,
                  background: bg,
                }}
                title={`${entry.card}: ${pct(entry.equity)} (${delta > 0 ? "+" : ""}${pct(delta)})`}
              >
                <span style={styles.heatmapValue}>{pct(entry.equity)}</span>
              </div>
            );
          })}
        </>
      ))}
    </div>
  );
}

// ─── Helpers ─────────────────────────────────────────────────

function pct(v: number): string {
  return `${(v * 100).toFixed(1)}%`;
}

function fmtEnum(s: string): string {
  return s
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

// ─── Styles ──────────────────────────────────────────────────

const styles: Record<string, React.CSSProperties> = {
  page: {
    padding: "1.5rem 2rem",
    maxWidth: 1200,
    margin: "0 auto",
    animation: "fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1)",
  },
  header: { marginBottom: "1.25rem" },
  title: {
    fontFamily: font.mono,
    fontSize: "0.9rem",
    fontWeight: 600,
    color: color.emerald.bright,
    letterSpacing: "0.08em",
    textTransform: "uppercase" as const,
    marginBottom: "0.3rem",
  },
  subtitle: {
    fontSize: "0.78rem",
    color: color.text.muted,
  },
  layout: {
    display: "grid",
    gridTemplateColumns: "320px 1fr",
    gap: "1rem",
    alignItems: "start",
  },

  // Input panel
  inputPanel: {
    background: color.gradient.panel,
    borderRadius: 8,
    border: `1px solid ${color.bg.border}`,
    padding: "1rem",
    boxShadow: shadow.inset,
    display: "flex",
    flexDirection: "column" as const,
    gap: "0.75rem",
  },
  inputGroup: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "0.3rem",
  },
  label: {
    fontFamily: font.mono,
    fontSize: "0.65rem",
    fontWeight: 600,
    color: color.text.secondary,
    letterSpacing: "0.06em",
    textTransform: "uppercase" as const,
  },
  input: {
    background: color.bg.abyss,
    border: `1px solid ${color.bg.borderMid}`,
    borderRadius: 5,
    padding: "0.45rem 0.6rem",
    fontFamily: font.mono,
    fontSize: "0.8rem",
    color: color.text.primary,
    outline: "none",
    transition: transition.fast,
  },
  smallInput: {
    flex: 1,
    minWidth: 0,
  },
  row: {
    display: "flex",
    gap: "0.4rem",
  },
  cardRow: {
    display: "flex",
    gap: 4,
    marginTop: 4,
  },
  slider: {
    width: "100%",
    accentColor: color.emerald.core,
  },
  sliderValue: {
    color: color.emerald.bright,
    fontWeight: 700,
  },
  streetBadge: {
    fontFamily: font.mono,
    fontSize: "0.6rem",
    fontWeight: 700,
    color: color.emerald.core,
    letterSpacing: "0.1em",
    textAlign: "center" as const,
    padding: "0.25rem",
    borderRadius: 4,
    border: `1px solid ${color.emerald.deep}`,
    background: `${color.emerald.trace}80`,
  },
  analyzeBtn: {
    fontFamily: font.mono,
    fontSize: "0.72rem",
    fontWeight: 700,
    letterSpacing: "0.08em",
    textTransform: "uppercase" as const,
    color: color.bg.abyss,
    background: color.emerald.bright,
    border: "none",
    borderRadius: 5,
    padding: "0.55rem",
    transition: transition.fast,
    boxShadow: shadow.glow(color.emerald.bright),
  },
  error: {
    fontFamily: font.mono,
    fontSize: "0.62rem",
    color: "#c44",
  },
  hint: {
    fontFamily: font.mono,
    fontSize: "0.62rem",
    color: color.text.muted,
  },

  // Results panel
  resultsPanel: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "0.75rem",
    minHeight: 300,
  },
  section: {
    background: color.gradient.panel,
    borderRadius: 8,
    border: `1px solid ${color.bg.border}`,
    padding: "0.8rem 1rem",
    boxShadow: shadow.inset,
  },
  sectionHeader: {
    display: "flex",
    alignItems: "center",
    gap: "0.4rem",
    marginBottom: "0.5rem",
  },
  sectionTitle: {
    fontFamily: font.mono,
    fontSize: "0.65rem",
    fontWeight: 600,
    color: color.text.primary,
    letterSpacing: "0.06em",
    textTransform: "uppercase" as const,
  },
  resultGrid: {
    display: "flex",
    flexWrap: "wrap" as const,
    gap: "0.5rem 1rem",
    alignItems: "center",
  },
  stat: {
    display: "flex",
    flexDirection: "column" as const,
    gap: 1,
  },
  statLabel: {
    fontFamily: font.mono,
    fontSize: "0.58rem",
    color: color.text.muted,
    letterSpacing: "0.04em",
    textTransform: "uppercase" as const,
  },
  statValue: {
    fontFamily: font.mono,
    fontSize: "0.76rem",
    color: color.text.primary,
    fontWeight: 500,
  },
  tag: {
    fontFamily: font.mono,
    fontSize: "0.6rem",
    padding: "0.15rem 0.4rem",
    borderRadius: 3,
    border: `1px solid ${color.bg.borderMid}`,
    color: color.text.secondary,
    letterSpacing: "0.04em",
  },
  miniLabel: {
    fontFamily: font.mono,
    fontSize: "0.58rem",
    color: color.text.muted,
    letterSpacing: "0.04em",
    display: "block",
    marginBottom: 4,
  },

  // Bar chart for precomputed equities
  barRow: {
    display: "flex",
    gap: 6,
    alignItems: "flex-end",
    height: 50,
  },
  barCol: {
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "center",
    gap: 2,
    flex: 1,
  },
  bar: {
    width: "100%",
    borderRadius: "2px 2px 0 0",
    transition: transition.fast,
    minHeight: 2,
  },
  barLabel: {
    fontFamily: font.mono,
    fontSize: "0.55rem",
    color: color.text.muted,
  },

  // EV table
  evTable: {
    display: "flex",
    flexDirection: "column" as const,
    gap: 4,
  },
  evRow: {
    display: "flex",
    alignItems: "center",
    gap: "0.6rem",
    padding: "0.2rem 0",
    borderBottom: `1px solid ${color.bg.border}`,
  },
  evAction: {
    fontFamily: font.mono,
    fontSize: "0.7rem",
    color: color.text.primary,
    fontWeight: 500,
    minWidth: 80,
  },
  evValue: {
    fontFamily: font.mono,
    fontSize: "0.76rem",
    fontWeight: 600,
  },
  evBB: {
    fontFamily: font.mono,
    fontSize: "0.6rem",
    color: color.text.muted,
  },

  // Heatmap
  heatmapGrid: {
    display: "grid",
    gridTemplateColumns: "24px repeat(4, 1fr)",
    gap: 2,
    marginTop: 6,
  },
  heatmapCorner: {
    width: 24,
  },
  heatmapSuitHeader: {
    fontFamily: font.mono,
    fontSize: "0.7rem",
    color: color.text.secondary,
    textAlign: "center" as const,
    padding: "2px 0",
  },
  heatmapRankLabel: {
    fontFamily: font.mono,
    fontSize: "0.6rem",
    color: color.text.muted,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  heatmapCell: {
    borderRadius: 3,
    padding: "3px 2px",
    textAlign: "center" as const,
    cursor: "default",
    minHeight: 22,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    transition: transition.fast,
  },
  heatmapCellDead: {
    borderRadius: 3,
    padding: "3px 2px",
    textAlign: "center" as const,
    minHeight: 22,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: `${color.bg.abyss}80`,
    color: color.text.dim,
    fontFamily: font.mono,
    fontSize: "0.5rem",
  },
  heatmapValue: {
    fontFamily: font.mono,
    fontSize: "0.5rem",
    color: color.text.primary,
    fontWeight: 500,
  },

  // Loading
  loadingBar: {
    height: 3,
    borderRadius: 2,
    background: color.bg.border,
    overflow: "hidden",
  },
  loadingPulse: {
    width: "30%",
    height: "100%",
    background: color.emerald.core,
    borderRadius: 2,
    animation: "loadingSlide 1.2s ease-in-out infinite",
  },

  // Error
  errorBox: {
    fontFamily: font.mono,
    fontSize: "0.68rem",
    color: "#c44",
    padding: "0.5rem",
    borderRadius: 5,
    border: "1px solid #c4444440",
    background: "#c4444410",
  },

  // Empty
  emptyState: {
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "center",
    justifyContent: "center",
    minHeight: 300,
    gap: 8,
  },
  emptyIcon: {
    fontSize: "2rem",
    color: color.text.dim,
    opacity: 0.5,
  },
  emptyText: {
    fontFamily: font.mono,
    fontSize: "0.72rem",
    color: color.text.muted,
  },
  emptyHint: {
    fontFamily: font.mono,
    fontSize: "0.65rem",
    color: color.text.dim,
  },
};
