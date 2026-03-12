/**
 * The Table — live PLO game room.
 *
 * Robotic Noir aesthetic: dark felt, metallic accents, clean geometry.
 * Currently renders with mock data to settle the visual design.
 */

import { useState } from "react";
import { color, font, shadow, transition, size } from "../theme/tokens.ts";
import { Card } from "../components/shared/Card.tsx";

// ─── Mock game state for visual development ────────────────────

interface MockPlayer {
  name: string;
  stack: number;
  chipsInPot: number;
  isFolded: boolean;
  isAllIn: boolean;
  isDealer: boolean;
  cards?: string[];
  seatAngle: number; // degrees around the table ellipse
}

const MOCK_PLAYERS: MockPlayer[] = [
  { name: "Bot Alpha", stack: 2450, chipsInPot: 150, isFolded: false, isAllIn: false, isDealer: false, seatAngle: 220 },
  { name: "Bot Beta", stack: 1800, chipsInPot: 0, isFolded: true, isAllIn: false, isDealer: false, seatAngle: 270 },
  { name: "Bot Gamma", stack: 3200, chipsInPot: 300, isFolded: false, isAllIn: false, isDealer: true, seatAngle: 320 },
];

const MOCK_BOARD = ["Td", "9s", "2h"];
const MOCK_HERO_CARDS = ["As", "Kh", "Qd", "Jc"];
const MOCK_POT = 1250;
const MOCK_HERO_STACK = 2800;
const MOCK_TO_CALL = 150;
const MOCK_POT_LIMIT = 1750;

// ─── Main Component ────────────────────────────────────────────

export function TableRoom() {
  const [selectedAction, setSelectedAction] = useState<string | null>(null);
  const [raiseAmount, setRaiseAmount] = useState(MOCK_POT_LIMIT / 2);

  return (
    <div style={styles.page}>
      {/* Phase banner */}
      <div style={styles.phaseBanner}>
        <span style={styles.phaseLabel}>FLOP</span>
        <span style={styles.phaseDivider}>|</span>
        <span style={styles.blindsLabel}>Blinds 25/50</span>
      </div>

      {/* Table area */}
      <div style={styles.tableArea}>
        {/* The felt */}
        <div style={styles.felt}>
          {/* Felt inner border */}
          <div style={styles.feltInner}>
            {/* Rail / edge highlight */}
            <div style={styles.feltRail} />

            {/* Community cards */}
            <div style={styles.boardSection}>
              <div style={styles.boardCards}>
                {MOCK_BOARD.map((card, i) => (
                  <Card key={card} card={card} scale={1.05} animated dealDelay={i * 120} />
                ))}
                {/* Remaining board slots */}
                {[...Array(5 - MOCK_BOARD.length)].map((_, i) => (
                  <div key={`empty-${i}`} style={styles.emptyBoardSlot} />
                ))}
              </div>
            </div>

            {/* Pot */}
            <div style={styles.potDisplay}>
              <ChipStack amount={MOCK_POT} />
            </div>

            {/* Opponent seats */}
            {MOCK_PLAYERS.map((player) => (
              <OpponentSeat key={player.name} player={player} />
            ))}
          </div>
        </div>
      </div>

      {/* Hero section — bottom of screen */}
      <div style={styles.heroSection}>
        {/* Hero info bar */}
        <div style={styles.heroInfo}>
          <div style={styles.heroNameBlock}>
            <span style={styles.heroName}>You</span>
            <span style={styles.heroStack}>${MOCK_HERO_STACK.toLocaleString()}</span>
          </div>
        </div>

        {/* Hero cards */}
        <div style={styles.heroCards}>
          {MOCK_HERO_CARDS.map((card, i) => (
            <Card key={card} card={card} scale={1.15} animated dealDelay={600 + i * 100} />
          ))}
        </div>

        {/* Action panel */}
        <ActionPanel
          toCall={MOCK_TO_CALL}
          potLimit={MOCK_POT_LIMIT}
          pot={MOCK_POT}
          raiseAmount={raiseAmount}
          onRaiseChange={setRaiseAmount}
          selectedAction={selectedAction}
          onAction={setSelectedAction}
        />
      </div>
    </div>
  );
}

// ─── Opponent Seat ─────────────────────────────────────────────

function OpponentSeat({ player }: { player: MockPlayer }) {
  // Position seats around the top of the felt ellipse
  const tableW = 720;
  const tableH = 380;
  const cx = tableW / 2;
  const cy = tableH / 2;
  const rx = tableW / 2 - 20;
  const ry = tableH / 2 - 20;

  const rad = (player.seatAngle * Math.PI) / 180;
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
        opacity: player.isFolded ? 0.4 : 1,
        transition: transition.normal,
      }}
    >
      {/* Face-down cards */}
      <div style={{ display: "flex", gap: 2 }}>
        {player.isFolded ? null : (
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
          border: `1px solid ${player.isDealer ? color.accent.gold : color.bg.border}`,
          borderRadius: 6,
          padding: "3px 8px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          minWidth: 80,
          boxShadow: player.isDealer ? shadow.glow(color.accent.gold) : shadow.sm,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <span
            style={{
              fontFamily: font.mono,
              fontSize: "0.65rem",
              fontWeight: 600,
              color: player.isFolded ? color.text.muted : color.text.primary,
            }}
          >
            {player.name}
          </span>
          {player.isDealer && (
            <span
              style={{
                fontSize: "0.5rem",
                fontFamily: font.mono,
                fontWeight: 700,
                color: color.bg.base,
                background: color.accent.gold,
                borderRadius: 3,
                padding: "0 3px",
                lineHeight: "14px",
              }}
            >
              D
            </span>
          )}
        </div>
        <span
          style={{
            fontFamily: font.mono,
            fontSize: "0.6rem",
            color: color.text.secondary,
          }}
        >
          ${player.stack.toLocaleString()}
        </span>
      </div>

      {/* Chips in pot indicator */}
      {player.chipsInPot > 0 && !player.isFolded && (
        <span
          style={{
            fontFamily: font.mono,
            fontSize: "0.55rem",
            color: color.accent.gold,
            opacity: 0.8,
          }}
        >
          ${player.chipsInPot}
        </span>
      )}

      {/* Status badges */}
      {player.isFolded && (
        <span style={{ fontFamily: font.mono, fontSize: "0.55rem", color: color.text.muted }}>
          FOLD
        </span>
      )}
      {player.isAllIn && (
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
      {/* Chip icon row */}
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
  raiseAmount: number;
  onRaiseChange: (v: number) => void;
  selectedAction: string | null;
  onAction: (a: string) => void;
}

function ActionPanel({
  toCall,
  potLimit,
  pot,
  raiseAmount,
  onRaiseChange,
  onAction,
}: ActionPanelProps) {
  const minRaise = toCall * 2;

  return (
    <div style={styles.actionPanel}>
      {/* Info line */}
      <div style={styles.actionInfo}>
        <span style={styles.actionInfoItem}>
          To call: <span style={styles.actionInfoValue}>${toCall}</span>
        </span>
        <span style={styles.actionInfoDivider}>|</span>
        <span style={styles.actionInfoItem}>
          Pot limit: <span style={styles.actionInfoValue}>${potLimit.toLocaleString()}</span>
        </span>
      </div>

      {/* Buttons */}
      <div style={styles.actionButtons}>
        <ActionButton
          label="Fold"
          color={color.action.fold}
          hoverColor={color.action.foldHover}
          onClick={() => onAction("fold")}
        />
        <ActionButton
          label={`Call $${toCall}`}
          color={color.action.call}
          hoverColor={color.action.callHover}
          onClick={() => onAction("call")}
        />
        <ActionButton
          label={`Raise $${raiseAmount}`}
          color={color.action.raise}
          hoverColor={color.action.raiseHover}
          primary
          onClick={() => onAction("raise")}
        />
      </div>

      {/* Raise slider */}
      <div style={styles.sliderSection}>
        <span style={styles.sliderLabel}>${minRaise}</span>
        <div style={styles.sliderTrack}>
          <input
            type="range"
            min={minRaise}
            max={potLimit}
            value={raiseAmount}
            onChange={(e) => onRaiseChange(Number(e.target.value))}
            style={styles.slider}
          />
          {/* Visual fill */}
          <div
            style={{
              ...styles.sliderFill,
              width: `${((raiseAmount - minRaise) / (potLimit - minRaise)) * 100}%`,
            }}
          />
        </div>
        <span style={styles.sliderLabel}>${potLimit.toLocaleString()}</span>

        {/* Quick-size buttons */}
        <div style={styles.quickSizes}>
          {[
            { label: "1/3", mult: 1 / 3 },
            { label: "1/2", mult: 1 / 2 },
            { label: "2/3", mult: 2 / 3 },
            { label: "POT", mult: 1 },
          ].map((s) => (
            <button
              key={s.label}
              onClick={() => onRaiseChange(Math.max(minRaise, Math.min(potLimit, Math.round(pot * s.mult))))}
              style={styles.quickSizeBtn}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = color.accent.gold;
                e.currentTarget.style.color = color.text.primary;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = color.bg.borderLight;
                e.currentTarget.style.color = color.text.secondary;
              }}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>
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
        textTransform: "uppercase",
        color: primary ? "#0e0e11" : color.text.primary,
        background: primary
          ? `linear-gradient(180deg, ${btnColor} 0%, ${hoverColor} 100%)`
          : "transparent",
        border: primary ? "none" : `1px solid ${btnColor}`,
        borderRadius: 8,
        cursor: "pointer",
        transition: transition.fast,
        boxShadow: primary ? shadow.glow(btnColor) : "none",
      }}
      onMouseEnter={(e) => {
        if (!primary) {
          e.currentTarget.style.background = `${btnColor}30`;
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

// ─── Styles ────────────────────────────────────────────────────

const styles: Record<string, React.CSSProperties> = {
  page: {
    height: "100%",
    display: "flex",
    flexDirection: "column",
    background: color.gradient.felt,
    overflow: "hidden",
  },

  // Phase banner
  phaseBanner: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "0.75rem",
    padding: "0.4rem 0",
    background: `linear-gradient(180deg, ${color.bg.surface}cc 0%, transparent 100%)`,
  },
  phaseLabel: {
    fontFamily: font.mono,
    fontSize: "0.7rem",
    fontWeight: 700,
    color: color.accent.gold,
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

  // The felt
  felt: {
    width: 720,
    height: 380,
    borderRadius: "50%",
    background: color.gradient.feltSurface,
    border: `2px solid ${color.felt.accent}40`,
    position: "relative",
    boxShadow: `inset 0 0 60px rgba(0,0,0,0.3), 0 0 40px rgba(0,0,0,0.4)`,
  },

  feltInner: {
    position: "absolute",
    inset: 6,
    borderRadius: "50%",
    border: `1px solid ${color.felt.accent}20`,
  },

  feltRail: {
    position: "absolute",
    inset: -3,
    borderRadius: "50%",
    border: `3px solid ${color.felt.accent}15`,
  },

  // Board
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
    border: `1px dashed ${color.felt.accent}30`,
    background: `${color.felt.deep}40`,
  },

  // Pot
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
    border: "1px solid rgba(255,255,255,0.15)",
  },

  potAmount: {
    fontFamily: font.mono,
    fontSize: "0.85rem",
    fontWeight: 700,
    color: color.accent.gold,
    textShadow: "0 0 8px rgba(212,168,75,0.3)",
  },

  // Hero section
  heroSection: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "0.6rem",
    padding: "0.5rem 2rem 1rem",
    background: `linear-gradient(180deg, transparent 0%, ${color.bg.base}cc 30%, ${color.bg.base} 100%)`,
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
    color: color.accent.gold,
  },

  heroCards: {
    display: "flex",
    gap: 8,
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
    color: color.text.secondary,
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

  // Slider
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
  },

  sliderFill: {
    position: "absolute",
    left: 0,
    top: 0,
    height: "100%",
    background: `linear-gradient(90deg, ${color.accent.goldMuted}, ${color.accent.gold})`,
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
    border: `1px solid ${color.bg.borderLight}`,
    borderRadius: 4,
    padding: "2px 10px",
    cursor: "pointer",
    transition: transition.fast,
    letterSpacing: "0.04em",
  },
};
