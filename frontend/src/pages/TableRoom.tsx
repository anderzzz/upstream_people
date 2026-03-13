/**
 * The Table — live PLO game room.
 *
 * Emerald Void aesthetic: obsidian felt, emerald rim lighting,
 * gold for the money, deep concave panels. The AI sits at the table.
 */

import { useState } from "react";
import { color, font, shadow, transition, size } from "../theme/tokens.ts";
import { Card } from "../components/shared/Card.tsx";
import { useGameSocket } from "../hooks/useGameSocket.ts";
import type { OpponentInfo, SessionConfig, StandingInfo, HandResultInfo } from "../types/game.ts";

// ─── Main Component ────────────────────────────────────────────

export function TableRoom() {
  const { state, startSession, sendAction, nextHand, quit } = useGameSocket();
  const [raiseAmount, setRaiseAmount] = useState(0);

  // ── Lobby screen ──
  if (state.status === "lobby" || state.status === "starting") {
    return <Lobby onStart={startSession} status={state.status} error={state.error} />;
  }

  // Derive display values
  const hasRaise = state.legalActions.some(
    (a) => a.action_type === "raise" || a.action_type === "bet",
  );
  const hasCheck = state.legalActions.some((a) => a.action_type === "check");
  const hasCall = state.legalActions.some((a) => a.action_type === "call");

  // Compute raise bounds from legal actions
  const raiseActions = state.legalActions.filter(
    (a) => a.action_type === "raise" || a.action_type === "bet",
  );
  const minRaiseAmount = raiseActions.length > 0
    ? Math.min(...raiseActions.map((a) => a.amount))
    : 0;
  const maxRaiseAmount = raiseActions.length > 0
    ? Math.max(...raiseActions.map((a) => a.amount))
    : 0;

  // Ensure raiseAmount is within bounds
  const effectiveRaise = Math.max(minRaiseAmount, Math.min(maxRaiseAmount, raiseAmount || minRaiseAmount));

  const blindsLabel = state.blinds
    ? `${state.blinds.small_blind}/${state.blinds.big_blind}`
    : "";

  // Compute opponent seat angles dynamically
  const opponentsWithAngles = state.opponents.map((opp, i) => {
    const startAngle = 200;
    const endAngle = 340;
    const step = state.opponents.length > 1
      ? (endAngle - startAngle) / (state.opponents.length - 1)
      : 0;
    const angle = state.opponents.length === 1 ? 270 : startAngle + step * i;
    return { ...opp, seatAngle: angle };
  });

  return (
    <div style={styles.page}>
      {/* Phase banner */}
      <div style={styles.phaseBanner}>
        <span style={styles.phaseLabel}>{state.phase || "WAITING"}</span>
        <span style={styles.phaseDivider}>|</span>
        <span style={styles.blindsLabel}>Blinds {blindsLabel}</span>
        <span style={styles.phaseDivider}>|</span>
        <span style={styles.blindsLabel}>Hand #{state.handNumber}</span>
      </div>

      {/* Table area */}
      <div style={styles.tableArea}>
        <div style={styles.felt}>
          <div style={styles.feltInner}>
            <div style={styles.feltRail} />

            {/* Emerald rim glow on felt edge */}
            <div style={styles.feltRimGlow} />

            {/* Community cards */}
            <div style={styles.boardSection}>
              <div style={styles.boardCards}>
                {state.board.map((card, i) => (
                  <Card key={`${card}-${i}`} card={card} scale={1.05} animated dealDelay={i * 120} />
                ))}
                {[...Array(Math.max(0, 5 - state.board.length))].map((_, i) => (
                  <div key={`empty-${i}`} style={styles.emptyBoardSlot} />
                ))}
              </div>
            </div>

            {/* Pot */}
            <div style={styles.potDisplay}>
              <ChipStack amount={state.pot} />
            </div>

            {/* Opponent seats */}
            {opponentsWithAngles.map((opp) => (
              <OpponentSeat
                key={opp.seat}
                opponent={opp}
                seatAngle={opp.seatAngle}
                isDealer={opp.seat === state.button}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Hero section */}
      <div style={styles.heroSection}>
        <div style={styles.heroInfo}>
          <div style={styles.heroNameBlock}>
            <span style={styles.heroName}>You</span>
            <span style={styles.heroStack}>${state.heroStack.toLocaleString()}</span>
            {state.yourSeat === state.button && (
              <span style={styles.dealerBadge}>D</span>
            )}
          </div>
        </div>

        {/* Hero cards */}
        <div style={styles.heroCards}>
          {state.heroCards.map((card, i) => (
            <Card key={`${card}-${i}`} card={card} scale={1.15} animated dealDelay={600 + i * 100} />
          ))}
        </div>

        {/* Action panel — only when it's our turn */}
        {state.awaitingAction && (
          <ActionPanel
            toCall={state.toCall}
            potLimit={maxRaiseAmount}
            pot={state.pot}
            minRaise={minRaiseAmount}
            maxRaise={maxRaiseAmount}
            raiseAmount={effectiveRaise}
            onRaiseChange={setRaiseAmount}
            hasCheck={hasCheck}
            hasCall={hasCall}
            hasRaise={hasRaise}
            onAction={(action, amount) => sendAction(action, amount)}
          />
        )}

        {/* Waiting indicator */}
        {state.status === "playing" && !state.awaitingAction && !state.handResult && (
          <div style={styles.waitingLabel}>Waiting for opponents...</div>
        )}
      </div>

      {/* Hand result overlay */}
      {state.status === "between_hands" && state.handResult && (
        <HandResultOverlay
          result={state.handResult}
          standings={state.standings}
          yourSeat={state.yourSeat}
          onNextHand={nextHand}
          onQuit={quit}
        />
      )}

      {/* Session over overlay */}
      {state.status === "session_over" && (
        <div style={styles.overlay}>
          <div style={styles.overlayPanel}>
            <h2 style={styles.overlayTitle}>Session Over</h2>
            <p style={styles.overlayText}>{state.sessionOverReason}</p>
            <StandingsTable standings={state.standings} />
          </div>
        </div>
      )}

      {/* Error display */}
      {state.error && (
        <div style={styles.errorBanner}>{state.error}</div>
      )}
    </div>
  );
}

// ─── Lobby ────────────────────────────────────────────────────

function Lobby({
  onStart,
  status,
  error,
}: {
  onStart: (config: SessionConfig) => void;
  status: string;
  error: string | null;
}) {
  const [opponents, setOpponents] = useState(2);
  const [botType, setBotType] = useState("heuristic");
  const [stack, setStack] = useState(1000);
  const [blinds, setBlinds] = useState("5/10");

  return (
    <div style={styles.lobbyPage}>
      <div style={styles.lobbyPanel}>
        <h1 style={styles.lobbyTitle}>PLO TABLE</h1>

        <div style={styles.lobbyField}>
          <label style={styles.lobbyLabel}>Opponents</label>
          <select
            value={opponents}
            onChange={(e) => setOpponents(Number(e.target.value))}
            style={styles.lobbyInput}
          >
            {[1, 2, 3, 4, 5].map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>

        <div style={styles.lobbyField}>
          <label style={styles.lobbyLabel}>Bot Type</label>
          <select
            value={botType}
            onChange={(e) => setBotType(e.target.value)}
            style={styles.lobbyInput}
          >
            <option value="heuristic">Heuristic (TAG)</option>
            <option value="random">Random</option>
            <option value="calling">Calling Station</option>
          </select>
        </div>

        <div style={styles.lobbyField}>
          <label style={styles.lobbyLabel}>Stack</label>
          <input
            type="number"
            value={stack}
            onChange={(e) => setStack(Number(e.target.value))}
            style={styles.lobbyInput}
          />
        </div>

        <div style={styles.lobbyField}>
          <label style={styles.lobbyLabel}>Blinds (SB/BB)</label>
          <input
            value={blinds}
            onChange={(e) => setBlinds(e.target.value)}
            style={styles.lobbyInput}
          />
        </div>

        <button
          onClick={() => onStart({ opponents, bot_type: botType, stack, blinds })}
          disabled={status === "starting"}
          style={styles.lobbyStartBtn}
          onMouseEnter={(e) => {
            e.currentTarget.style.boxShadow = shadow.glowStrong(color.emerald.core);
            e.currentTarget.style.transform = "translateY(-1px)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.boxShadow = shadow.glow(color.emerald.core);
            e.currentTarget.style.transform = "translateY(0)";
          }}
        >
          {status === "starting" ? "Starting..." : "Start Game"}
        </button>

        {error && <p style={styles.lobbyError}>{error}</p>}
      </div>
    </div>
  );
}

// ─── Opponent Seat ─────────────────────────────────────────────

function OpponentSeat({
  opponent,
  seatAngle,
  isDealer,
}: {
  opponent: OpponentInfo;
  seatAngle: number;
  isDealer: boolean;
}) {
  const tableW = 720;
  const tableH = 380;
  const cx = tableW / 2;
  const cy = tableH / 2;
  const rx = tableW / 2 - 20;
  const ry = tableH / 2 - 20;

  const rad = (seatAngle * Math.PI) / 180;
  const x = cx + rx * Math.cos(rad);
  const y = cy + ry * Math.sin(rad);

  return (
    <div
      style={{
        position: "absolute",
        left: x - 52,
        top: y - 34,
        width: 104,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 3,
        opacity: opponent.is_folded ? 0.35 : 1,
        transition: transition.normal,
      }}
    >
      {/* Face-down cards (or showdown cards) */}
      <div style={{ display: "flex", gap: 2 }}>
        {opponent.is_folded ? null : opponent.hole_cards ? (
          opponent.hole_cards.map((card, i) => (
            <Card key={`${card}-${i}`} card={card} scale={0.45} />
          ))
        ) : (
          <>
            <Card faceDown scale={0.45} />
            <Card faceDown scale={0.45} />
            <Card faceDown scale={0.45} />
            <Card faceDown scale={0.45} />
          </>
        )}
      </div>

      {/* Name plate */}
      <div
        style={{
          background: color.gradient.panel,
          border: `1px solid ${isDealer ? color.gold.muted : color.bg.border}`,
          borderRadius: 5,
          padding: "3px 8px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          minWidth: 80,
          boxShadow: isDealer
            ? `${shadow.inset}, ${shadow.glow(color.gold.core)}`
            : shadow.inset,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <span
            style={{
              fontFamily: font.mono,
              fontSize: "0.65rem",
              fontWeight: 600,
              color: opponent.is_folded ? color.text.muted : color.text.primary,
            }}
          >
            {opponent.name}
          </span>
          {isDealer && (
            <span style={styles.dealerBadge}>D</span>
          )}
        </div>
        <span
          style={{
            fontFamily: font.mono,
            fontSize: "0.6rem",
            color: color.gold.muted,
          }}
        >
          ${opponent.stack.toLocaleString()}
        </span>
      </div>

      {/* Chips in pot */}
      {opponent.chips_in_pot > 0 && !opponent.is_folded && (
        <span
          style={{
            fontFamily: font.mono,
            fontSize: "0.55rem",
            color: color.gold.core,
            opacity: 0.8,
          }}
        >
          ${opponent.chips_in_pot}
        </span>
      )}

      {/* Status badges */}
      {opponent.is_folded && (
        <span style={{ fontFamily: font.mono, fontSize: "0.55rem", color: color.text.muted }}>
          FOLD
        </span>
      )}
      {opponent.is_all_in && (
        <span style={{ fontFamily: font.mono, fontSize: "0.55rem", color: color.status.allIn, fontWeight: 700 }}>
          ALL-IN
        </span>
      )}
    </div>
  );
}

// ─── Chip Stack Display ────────────────────────────────────────

function ChipStack({ amount }: { amount: number }) {
  return (
    <div style={styles.chipStack}>
      <div style={styles.chipIcons}>
        <div style={{ ...styles.chipDot, background: color.chip.black }} />
        <div style={{ ...styles.chipDot, background: color.chip.red }} />
        <div style={{ ...styles.chipDot, background: color.chip.blue }} />
      </div>
      <span style={styles.potAmount}>${amount.toLocaleString()}</span>
    </div>
  );
}

// ─── Action Panel ──────────────────────────────────────────────

interface ActionPanelProps {
  toCall: number;
  potLimit: number;
  pot: number;
  minRaise: number;
  maxRaise: number;
  raiseAmount: number;
  onRaiseChange: (v: number) => void;
  hasCheck: boolean;
  hasCall: boolean;
  hasRaise: boolean;
  onAction: (action: string, amount?: number) => void;
}

function ActionPanel({
  toCall,
  potLimit,
  pot,
  minRaise,
  maxRaise,
  raiseAmount,
  onRaiseChange,
  hasCheck,
  hasCall,
  hasRaise,
  onAction,
}: ActionPanelProps) {
  const isRaise = toCall > 0;
  const raiseLabel = isRaise ? "Raise" : "Bet";

  return (
    <div style={styles.actionPanel}>
      {/* Info line */}
      <div style={styles.actionInfo}>
        {toCall > 0 && (
          <>
            <span style={styles.actionInfoItem}>
              To call: <span style={styles.actionInfoValue}>${toCall}</span>
            </span>
            <span style={styles.actionInfoDivider}>|</span>
          </>
        )}
        <span style={styles.actionInfoItem}>
          Pot: <span style={styles.actionInfoValue}>${pot.toLocaleString()}</span>
        </span>
        {hasRaise && (
          <>
            <span style={styles.actionInfoDivider}>|</span>
            <span style={styles.actionInfoItem}>
              Pot limit: <span style={styles.actionInfoValue}>${potLimit.toLocaleString()}</span>
            </span>
          </>
        )}
      </div>

      {/* Buttons */}
      <div style={styles.actionButtons}>
        <ActionButton
          label="Fold"
          color={color.action.fold}
          hoverColor={color.action.foldHover}
          onClick={() => onAction("fold")}
        />
        {hasCheck && (
          <ActionButton
            label="Check"
            color={color.action.call}
            hoverColor={color.action.callHover}
            onClick={() => onAction("check")}
          />
        )}
        {hasCall && (
          <ActionButton
            label={`Call $${toCall}`}
            color={color.action.call}
            hoverColor={color.action.callHover}
            onClick={() => onAction("call")}
          />
        )}
        {hasRaise && (
          <ActionButton
            label={`${raiseLabel} $${raiseAmount}`}
            color={color.action.raise}
            hoverColor={color.action.raiseHover}
            primary
            onClick={() => onAction(isRaise ? "raise" : "bet", raiseAmount)}
          />
        )}
      </div>

      {/* Raise slider */}
      {hasRaise && maxRaise > minRaise && (
        <div style={styles.sliderSection}>
          <span style={styles.sliderLabel}>${minRaise}</span>
          <div style={styles.sliderTrack}>
            <input
              type="range"
              min={minRaise}
              max={maxRaise}
              value={raiseAmount}
              onChange={(e) => onRaiseChange(Number(e.target.value))}
              style={styles.slider}
            />
            <div
              style={{
                ...styles.sliderFill,
                width: `${((raiseAmount - minRaise) / (maxRaise - minRaise)) * 100}%`,
              }}
            />
          </div>
          <span style={styles.sliderLabel}>${maxRaise.toLocaleString()}</span>

          <div style={styles.quickSizes}>
            {[
              { label: "1/3", mult: 1 / 3 },
              { label: "1/2", mult: 1 / 2 },
              { label: "2/3", mult: 2 / 3 },
              { label: "POT", mult: 1 },
            ].map((s) => (
              <button
                key={s.label}
                onClick={() =>
                  onRaiseChange(
                    Math.max(minRaise, Math.min(maxRaise, Math.round(pot * s.mult))),
                  )
                }
                style={styles.quickSizeBtn}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = color.emerald.dim;
                  e.currentTarget.style.color = color.text.primary;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = color.bg.borderMid;
                  e.currentTarget.style.color = color.text.secondary;
                }}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Action Button ─────────────────────────────────────────────

function ActionButton({
  label,
  color: btnColor,
  hoverColor,
  primary = false,
  onClick,
}: {
  label: string;
  color: string;
  hoverColor: string;
  primary?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        flex: 1,
        padding: "0.55rem 1rem",
        fontFamily: font.mono,
        fontSize: "0.72rem",
        fontWeight: 600,
        letterSpacing: "0.04em",
        textTransform: "uppercase" as const,
        color: primary ? "#050506" : color.text.primary,
        background: primary
          ? `linear-gradient(180deg, ${btnColor} 0%, ${hoverColor} 100%)`
          : "transparent",
        border: primary ? "none" : `1px solid ${btnColor}`,
        borderRadius: 6,
        cursor: "pointer",
        transition: transition.fast,
        boxShadow: primary ? shadow.glow(btnColor) : "none",
      }}
      onMouseEnter={(e) => {
        if (!primary) {
          e.currentTarget.style.background = `${btnColor}25`;
          e.currentTarget.style.borderColor = hoverColor;
        } else {
          e.currentTarget.style.boxShadow = shadow.glowStrong(btnColor);
          e.currentTarget.style.transform = "translateY(-1px)";
        }
      }}
      onMouseLeave={(e) => {
        if (!primary) {
          e.currentTarget.style.background = "transparent";
          e.currentTarget.style.borderColor = btnColor;
        } else {
          e.currentTarget.style.boxShadow = shadow.glow(btnColor);
          e.currentTarget.style.transform = "translateY(0)";
        }
      }}
    >
      {label}
    </button>
  );
}

// ─── Hand Result Overlay ───────────────────────────────────────

function HandResultOverlay({
  result,
  standings,
  yourSeat,
  onNextHand,
  onQuit,
}: {
  result: HandResultInfo;
  standings: StandingInfo[];
  yourSeat: number;
  onNextHand: () => void;
  onQuit: () => void;
}) {
  const heroProfit = result.net_profit[String(yourSeat)] ?? 0;
  const isWin = heroProfit > 0;

  return (
    <div style={styles.overlay}>
      <div style={styles.overlayPanel}>
        <h2
          style={{
            ...styles.overlayTitle,
            color: isWin ? color.emerald.bright : heroProfit < 0 ? color.status.allIn : color.text.primary,
          }}
        >
          {isWin ? `+$${heroProfit}` : heroProfit < 0 ? `-$${Math.abs(heroProfit)}` : "Break Even"}
        </h2>

        {result.went_to_showdown && result.board.length > 0 && (
          <div style={{ display: "flex", gap: 4, justifyContent: "center", margin: "8px 0" }}>
            {result.board.map((card, i) => (
              <Card key={`${card}-${i}`} card={card} scale={0.7} />
            ))}
          </div>
        )}

        <StandingsTable standings={standings} />

        <div style={styles.overlayButtons}>
          <button onClick={onNextHand} style={styles.overlayBtn}>
            Next Hand
          </button>
          <button onClick={onQuit} style={styles.overlayBtnSecondary}>
            Quit
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Standings Table ───────────────────────────────────────────

function StandingsTable({ standings }: { standings: StandingInfo[] }) {
  return (
    <div style={styles.standingsTable}>
      {standings.map((s) => (
        <div key={s.name} style={styles.standingsRow}>
          <span style={styles.standingsName}>{s.name}</span>
          <span style={styles.standingsStack}>${s.stack.toLocaleString()}</span>
        </div>
      ))}
    </div>
  );
}

// ─── Styles ────────────────────────────────────────────────────

const styles: Record<string, React.CSSProperties> = {
  page: {
    height: "100%",
    display: "flex",
    flexDirection: "column",
    background: color.gradient.felt,
    overflow: "hidden",
    position: "relative",
  },

  // Phase banner
  phaseBanner: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "0.75rem",
    padding: "0.4rem 0",
    background: `linear-gradient(180deg, ${color.bg.base}dd 0%, transparent 100%)`,
  },
  phaseLabel: {
    fontFamily: font.mono,
    fontSize: "0.7rem",
    fontWeight: 700,
    color: color.emerald.core,
    letterSpacing: "0.12em",
  },
  phaseDivider: {
    color: color.text.dim,
    fontSize: "0.7rem",
  },
  blindsLabel: {
    fontFamily: font.mono,
    fontSize: "0.65rem",
    color: color.text.muted,
    letterSpacing: "0.06em",
  },

  // Table area
  tableArea: {
    flex: 1,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "0.5rem",
    minHeight: 0,
  },

  felt: {
    width: 720,
    height: 380,
    borderRadius: "50%",
    background: color.gradient.feltSurface,
    border: `2px solid ${color.felt.accent}30`,
    position: "relative",
    boxShadow: `inset 0 0 60px rgba(0,0,0,0.4), 0 0 50px rgba(0,0,0,0.5)`,
  },
  feltInner: {
    position: "absolute",
    inset: 6,
    borderRadius: "50%",
    border: `1px solid ${color.felt.accent}18`,
  },
  feltRail: {
    position: "absolute",
    inset: -3,
    borderRadius: "50%",
    border: `3px solid ${color.felt.accent}10`,
  },
  // Emerald rim glow around the felt edge
  feltRimGlow: {
    position: "absolute",
    inset: -1,
    borderRadius: "50%",
    boxShadow: `inset 0 0 30px ${color.emerald.deep}30, 0 0 20px ${color.emerald.deep}15`,
    pointerEvents: "none",
  },

  boardSection: {
    position: "absolute",
    top: "38%",
    left: "50%",
    transform: "translate(-50%, -50%)",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 8,
  },
  boardCards: {
    display: "flex",
    gap: 6,
    alignItems: "center",
  },
  emptyBoardSlot: {
    width: size.card.width * 1.05,
    height: size.card.height * 1.05,
    borderRadius: size.radius.md,
    border: `1px dashed ${color.felt.accent}25`,
    background: `${color.felt.deep}50`,
  },

  potDisplay: {
    position: "absolute",
    top: "60%",
    left: "50%",
    transform: "translate(-50%, -50%)",
  },
  chipStack: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 2,
  },
  chipIcons: {
    display: "flex",
    gap: 2,
  },
  chipDot: {
    width: 10,
    height: 10,
    borderRadius: "50%",
    border: "1px solid rgba(255,255,255,0.1)",
  },
  potAmount: {
    fontFamily: font.mono,
    fontSize: "0.85rem",
    fontWeight: 700,
    color: color.gold.core,
    textShadow: `0 0 8px ${color.gold.muted}50`,
  },

  // Hero section
  heroSection: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "0.6rem",
    padding: "0.5rem 2rem 1rem",
    background: `linear-gradient(180deg, transparent 0%, ${color.bg.abyss}cc 30%, ${color.bg.abyss} 100%)`,
  },
  heroInfo: {
    display: "flex",
    alignItems: "center",
    gap: "1rem",
  },
  heroNameBlock: {
    display: "flex",
    alignItems: "center",
    gap: "0.75rem",
  },
  heroName: {
    fontFamily: font.mono,
    fontSize: "0.75rem",
    fontWeight: 700,
    color: color.text.primary,
    letterSpacing: "0.06em",
    textTransform: "uppercase",
  },
  heroStack: {
    fontFamily: font.mono,
    fontSize: "0.75rem",
    fontWeight: 500,
    color: color.gold.core,
  },
  heroCards: {
    display: "flex",
    gap: 8,
  },
  dealerBadge: {
    fontSize: "0.5rem",
    fontFamily: font.mono,
    fontWeight: 700,
    color: color.bg.abyss,
    background: color.gold.core,
    borderRadius: 3,
    padding: "0 3px",
    lineHeight: "14px",
  },

  // Waiting
  waitingLabel: {
    fontFamily: font.mono,
    fontSize: "0.7rem",
    color: color.text.muted,
    letterSpacing: "0.04em",
    padding: "0.5rem",
  },

  // Action panel
  actionPanel: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "0.5rem",
    width: "100%",
    maxWidth: 520,
  },
  actionInfo: {
    display: "flex",
    alignItems: "center",
    gap: "0.6rem",
    fontFamily: font.mono,
    fontSize: "0.65rem",
  },
  actionInfoItem: {
    color: color.text.muted,
    letterSpacing: "0.04em",
  },
  actionInfoValue: {
    color: color.gold.muted,
    fontWeight: 600,
  },
  actionInfoDivider: {
    color: color.text.dim,
  },
  actionButtons: {
    display: "flex",
    gap: 8,
    width: "100%",
  },

  sliderSection: {
    display: "flex",
    alignItems: "center",
    gap: "0.5rem",
    width: "100%",
    flexWrap: "wrap",
  },
  sliderLabel: {
    fontFamily: font.mono,
    fontSize: "0.6rem",
    color: color.text.muted,
    minWidth: 40,
    textAlign: "center",
  },
  sliderTrack: {
    flex: 1,
    height: 4,
    background: color.bg.elevated,
    borderRadius: 2,
    position: "relative",
    overflow: "hidden",
    boxShadow: shadow.inset,
  },
  sliderFill: {
    position: "absolute",
    left: 0,
    top: 0,
    height: "100%",
    background: `linear-gradient(90deg, ${color.emerald.dim}, ${color.emerald.core})`,
    borderRadius: 2,
    pointerEvents: "none",
  },
  slider: {
    position: "absolute",
    inset: 0,
    width: "100%",
    height: "100%",
    opacity: 0,
    cursor: "pointer",
    margin: 0,
  },
  quickSizes: {
    display: "flex",
    gap: 4,
    width: "100%",
    justifyContent: "center",
    marginTop: 2,
  },
  quickSizeBtn: {
    fontFamily: font.mono,
    fontSize: "0.58rem",
    fontWeight: 600,
    color: color.text.secondary,
    background: "transparent",
    border: `1px solid ${color.bg.borderMid}`,
    borderRadius: 4,
    padding: "2px 10px",
    cursor: "pointer",
    transition: transition.fast,
    letterSpacing: "0.04em",
  },

  // Overlays
  overlay: {
    position: "absolute",
    inset: 0,
    background: color.bg.overlay,
    backdropFilter: "blur(8px)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 100,
  },
  overlayPanel: {
    background: color.gradient.panel,
    border: `1px solid ${color.bg.border}`,
    borderRadius: 10,
    padding: "1.5rem 2rem",
    minWidth: 300,
    textAlign: "center",
    boxShadow: `${shadow.lg}, ${shadow.glow(color.emerald.deep)}`,
  },
  overlayTitle: {
    fontFamily: font.mono,
    fontSize: "1.2rem",
    fontWeight: 700,
    letterSpacing: "0.06em",
    margin: "0 0 0.75rem",
  },
  overlayText: {
    fontFamily: font.mono,
    fontSize: "0.75rem",
    color: color.text.muted,
    margin: "0 0 1rem",
  },
  overlayButtons: {
    display: "flex",
    gap: 8,
    justifyContent: "center",
    marginTop: "1rem",
  },
  overlayBtn: {
    fontFamily: font.mono,
    fontSize: "0.72rem",
    fontWeight: 600,
    letterSpacing: "0.04em",
    textTransform: "uppercase",
    color: "#050506",
    background: `linear-gradient(180deg, ${color.emerald.core} 0%, ${color.emerald.mid} 100%)`,
    border: "none",
    borderRadius: 6,
    padding: "0.55rem 1.5rem",
    cursor: "pointer",
    boxShadow: shadow.glow(color.emerald.core),
    transition: transition.fast,
  },
  overlayBtnSecondary: {
    fontFamily: font.mono,
    fontSize: "0.72rem",
    fontWeight: 600,
    letterSpacing: "0.04em",
    textTransform: "uppercase",
    color: color.text.secondary,
    background: "transparent",
    border: `1px solid ${color.bg.borderMid}`,
    borderRadius: 6,
    padding: "0.55rem 1.5rem",
    cursor: "pointer",
    transition: transition.fast,
  },

  // Standings
  standingsTable: {
    display: "flex",
    flexDirection: "column",
    gap: 4,
    margin: "0.5rem 0",
  },
  standingsRow: {
    display: "flex",
    justifyContent: "space-between",
    fontFamily: font.mono,
    fontSize: "0.7rem",
    padding: "2px 8px",
  },
  standingsName: {
    color: color.text.secondary,
  },
  standingsStack: {
    color: color.gold.core,
    fontWeight: 600,
  },

  // Error
  errorBanner: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    background: "rgba(180,40,40,0.9)",
    color: "#fff",
    fontFamily: font.mono,
    fontSize: "0.7rem",
    padding: "0.5rem",
    textAlign: "center",
    zIndex: 200,
  },

  // Lobby
  lobbyPage: {
    height: "100%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: color.gradient.felt,
  },
  lobbyPanel: {
    background: color.gradient.panel,
    border: `1px solid ${color.bg.border}`,
    borderRadius: 10,
    padding: "2rem",
    minWidth: 320,
    display: "flex",
    flexDirection: "column",
    gap: "1rem",
    boxShadow: `${shadow.lg}, ${shadow.inset}`,
  },
  lobbyTitle: {
    fontFamily: font.mono,
    fontSize: "1.2rem",
    fontWeight: 700,
    color: color.emerald.bright,
    letterSpacing: "0.12em",
    textAlign: "center",
    margin: 0,
    textShadow: `0 0 20px ${color.emerald.dim}40`,
  },
  lobbyField: {
    display: "flex",
    flexDirection: "column",
    gap: "0.25rem",
  },
  lobbyLabel: {
    fontFamily: font.mono,
    fontSize: "0.65rem",
    fontWeight: 600,
    color: color.text.muted,
    letterSpacing: "0.06em",
    textTransform: "uppercase",
  },
  lobbyInput: {
    fontFamily: font.mono,
    fontSize: "0.75rem",
    color: color.text.primary,
    background: color.bg.base,
    border: `1px solid ${color.bg.border}`,
    borderRadius: 5,
    padding: "0.4rem 0.6rem",
    outline: "none",
    boxShadow: shadow.inset,
  },
  lobbyStartBtn: {
    fontFamily: font.mono,
    fontSize: "0.8rem",
    fontWeight: 700,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
    color: "#050506",
    background: `linear-gradient(180deg, ${color.emerald.core} 0%, ${color.emerald.mid} 100%)`,
    border: "none",
    borderRadius: 6,
    padding: "0.65rem 1.5rem",
    cursor: "pointer",
    boxShadow: shadow.glow(color.emerald.core),
    marginTop: "0.5rem",
    transition: transition.fast,
  },
  lobbyError: {
    fontFamily: font.mono,
    fontSize: "0.7rem",
    color: "#e44",
    textAlign: "center",
    margin: 0,
  },
};
