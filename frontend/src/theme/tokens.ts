/**
 * Design tokens — Emerald Void.
 *
 * Monolithic intelligence. Obsidian surfaces. Bioluminescent emerald.
 * The machine deals your hand. It doesn't blink.
 *
 * Color hierarchy:
 *   Emerald  → the system, the AI, the interface (borders, glows, status)
 *   Gold     → the money, the stakes, the human element (pots, stacks, profit)
 *   Obsidian → the void, depth, negative space (surfaces, backgrounds)
 */

// ─── Emerald spectrum ─────────────────────────────────────────
const emerald = {
  neon:    "#00FF9D",   // vivid — sparingly, for active glows
  bright:  "#50FFB0",   // bright — primary UI accent
  core:    "#3ddc84",   // saturated — icons, labels
  mid:     "#2a9d5e",   // medium — hover states, secondary
  dim:     "#1a6b3e",   // muted — subtle accents
  deep:    "#0d3a20",   // whisper — background tints
  trace:   "#072818",   // barely there — surface undertones
} as const;

// ─── Gold spectrum ────────────────────────────────────────────
const gold = {
  bright:  "#e8c060",
  core:    "#d4a84b",
  muted:   "#8a7030",
  dim:     "#5a4820",
} as const;

export const color = {
  // Backgrounds — layered obsidian depth
  bg: {
    abyss:     "#050506",   // deepest — behind everything
    base:      "#0A0A0B",   // primary surface
    surface:   "#111113",   // panels, cards — lifted
    elevated:  "#18181c",   // hover, modals — another step up
    border:    "#1e1e26",   // subtle edges — barely visible
    borderMid: "#2a2a34",   // medium edges — interactive
    borderLight: "#3a3a46", // hover edges
    overlay:   "rgba(5, 5, 6, 0.85)",
  },

  // Gradients — the monolithic soul
  gradient: {
    // Page background — deep radial void with emerald whisper
    page: `radial-gradient(ellipse at 50% 0%, ${emerald.trace} 0%, #0A0A0B 50%, #050506 100%)`,
    // Panel surface — concave metallic
    panel: "linear-gradient(180deg, #131316 0%, #0e0e11 100%)",
    // Panel surface on hover — slightly lifted
    panelHover: "linear-gradient(180deg, #171719 0%, #111114 100%)",
    // Nav bar — subtle emerald underglow
    nav: `linear-gradient(180deg, #0f0f12 0%, #0A0A0B 100%)`,
    // Table felt — deep obsidian with emerald undertone
    felt: `radial-gradient(ellipse at 50% 40%, ${emerald.trace} 0%, #0A0A0B 60%)`,
    // Felt surface — the playing field
    feltSurface: `radial-gradient(ellipse at 50% 50%, #0f1f16 0%, #0a1510 50%, #060e0a 100%)`,
    // Card face — warm parchment
    cardFace: "linear-gradient(170deg, #f2f0eb 0%, #e8e5de 40%, #ddd9d0 100%)",
    // Card back — dark machine with emerald thread
    cardBack: `linear-gradient(135deg, #0e0e14 0%, #14141c 50%, #0e0e14 100%)`,
    // Gold shimmer — for money elements
    gold: `linear-gradient(135deg, ${gold.muted} 0%, ${gold.core} 50%, ${gold.muted} 100%)`,
    // Emerald shimmer — for UI elements
    emerald: `linear-gradient(135deg, ${emerald.dim} 0%, ${emerald.core} 50%, ${emerald.dim} 100%)`,
    // Rim border — the signature look (used via border-image or pseudo-elements)
    rimBorder: `linear-gradient(180deg, transparent 0%, ${emerald.dim} 50%, transparent 100%)`,
    // Horizontal rim
    rimBorderH: `linear-gradient(90deg, transparent 0%, ${emerald.dim} 50%, transparent 100%)`,
  },

  // The felt — deep obsidian-green
  felt: {
    deep:   "#040a07",
    base:   "#081410",
    light:  "#0f2018",
    accent: "#1a3828",
  },

  // Text — silver-grey family, slightly cooler
  text: {
    primary:   "#d0d0dc",
    secondary: "#707088",
    muted:     "#484860",
    dim:       "#2a2a3a",
  },

  // Emerald — the machine accent
  emerald,

  // Gold — the money accent
  gold,

  // Accents — legacy-compatible aliases
  accent: {
    silver:       "#a0a0a8",
    gold:         gold.core,
    goldMuted:    gold.muted,
    goldBright:   gold.bright,
    cyan:         emerald.bright,      // cyan → emerald bright (system accent)
    cyanMuted:    emerald.mid,
    emerald:      emerald.core,
    emeraldMuted: emerald.mid,
  },

  // Semantic action colors — desaturated, metallic
  action: {
    fold:      "#5a2a34",
    foldHover: "#6d3340",
    call:      "#2a5a3a",
    callHover: "#347048",
    raise:     gold.core,
    raiseHover: gold.bright,
    check:     "#3a3a50",
    checkHover: "#4a4a60",
    allIn:     "#903838",
    allInHover: "#a84040",
  },

  // Card suit colors
  suit: {
    spades:   "#2a2a34",
    hearts:   "#c43838",
    diamonds: "#3870c4",
    clubs:    "#2a8a50",
  },

  // Chips — metallic sheen
  chip: {
    white: "#c0c0c8",
    red:   "#a03838",
    blue:  "#3858a0",
    black: "#282830",
    green: "#287048",
  },

  // Status — emerald-forward
  status: {
    online:   emerald.bright,
    folded:   "#484860",
    allIn:    "#b84848",
    thinking: emerald.core,
    winner:   gold.core,
  },
} as const;

export const font = {
  body: "'Inter', system-ui, -apple-system, sans-serif",
  mono: "'JetBrains Mono', 'Fira Code', monospace",
} as const;

export const size = {
  card: { width: 62, height: 88 },
  radius: { xs: 3, sm: 4, md: 6, lg: 10, xl: 14 },  // tightened: sharp but engineered
} as const;

export const shadow = {
  // Standard shadows — sharp, not fuzzy
  sm:   "0 1px 2px rgba(0,0,0,0.6)",
  md:   "0 2px 8px rgba(0,0,0,0.7)",
  lg:   "0 4px 16px rgba(0,0,0,0.8)",
  // Card shadows — deep and defined
  card: "0 2px 6px rgba(0,0,0,0.7), 0 0 1px rgba(0,0,0,0.5)",
  cardHover: "0 4px 14px rgba(0,0,0,0.8), 0 0 2px rgba(0,0,0,0.6)",
  // Inset — concave metallic surfaces
  inset:      "inset 0 1px 4px rgba(0,0,0,0.5)",
  insetDeep:  "inset 0 2px 10px rgba(0,0,0,0.6), inset 0 0 1px rgba(0,0,0,0.3)",
  // Bioluminescent glows — the signature effect
  glow: (c: string) => `0 0 10px ${c}30, 0 0 3px ${c}18`,
  glowStrong: (c: string) => `0 0 18px ${c}50, 0 0 6px ${c}28`,
  glowNeon: (c: string) => `0 0 24px ${c}60, 0 0 8px ${c}40, 0 0 2px ${c}80`,
  // Combined: inset + glow for "powered on" panels
  panelActive: (c: string) => `inset 0 1px 4px rgba(0,0,0,0.4), 0 0 12px ${c}30`,
} as const;

export const transition = {
  // Hydraulic — heavy, decelerating, precise
  fast:   "all 0.15s cubic-bezier(0.16, 1, 0.3, 1)",
  normal: "all 0.25s cubic-bezier(0.16, 1, 0.3, 1)",
  slow:   "all 0.4s cubic-bezier(0.16, 1, 0.3, 1)",
  // Settle — for elements arriving into position
  settle: "all 0.5s cubic-bezier(0.22, 1, 0.36, 1)",
  // Glow — for color/shadow transitions (slightly slower, smoother)
  glow:   "all 0.3s ease",
} as const;

// ─── Gradient border helper ─────────────────────────────────
// CSS can't do gradient borders directly on `border`.
// Use these as `background` on a wrapper with inner content offset by 1px,
// or apply via `border-image` (no border-radius support) or pseudo-elements.
// The recommended approach: a thin ::before pseudo with these as background.
export const gradientBorder = {
  // Vertical rim — left/right edges glow
  vertical:   `linear-gradient(180deg, transparent 0%, ${emerald.dim}80 30%, ${emerald.mid}60 50%, ${emerald.dim}80 70%, transparent 100%)`,
  // Horizontal rim — top/bottom edges glow
  horizontal: `linear-gradient(90deg, transparent 0%, ${emerald.dim}80 30%, ${emerald.mid}60 50%, ${emerald.dim}80 70%, transparent 100%)`,
  // Full frame — all edges, corners dimmer
  frame:      `linear-gradient(135deg, ${emerald.dim}40 0%, ${emerald.mid}50 25%, ${emerald.dim}40 50%, ${emerald.mid}50 75%, ${emerald.dim}40 100%)`,
  // Subtle — barely-there version for resting state
  subtle:     `linear-gradient(180deg, transparent 10%, ${emerald.deep}80 50%, transparent 90%)`,
} as const;
