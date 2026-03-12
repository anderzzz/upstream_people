/**
 * Design tokens — Robotic Noir.
 *
 * Hyper-sleek dark grey. Brushed steel gradients. Precise geometry.
 * The machine deals your hand. It doesn't blink.
 */

export const color = {
  // Backgrounds — dark grey gradient spectrum
  bg: {
    base: "#0e0e11",         // deepest void
    surface: "#161619",      // panels, cards
    elevated: "#1e1e23",     // hover, modals
    border: "#2a2a32",       // subtle edges
    borderLight: "#3a3a44",  // hover edges
    overlay: "rgba(0, 0, 0, 0.7)",
  },

  // Gradients — the robotic soul
  gradient: {
    // Page background — subtle diagonal
    page: "linear-gradient(160deg, #0e0e11 0%, #121218 40%, #0e0e11 100%)",
    // Panel surface — brushed steel hint
    panel: "linear-gradient(180deg, #18181d 0%, #141417 100%)",
    // Nav bar
    nav: "linear-gradient(180deg, #141417 0%, #111114 100%)",
    // Table felt — deep charcoal with a whisper of green
    felt: "radial-gradient(ellipse at 50% 45%, #1a2420 0%, #141a17 30%, #0e0e11 70%)",
    // Felt surface
    feltSurface: "radial-gradient(ellipse at 50% 50%, #1e2e26 0%, #162019 60%, #0e1510 100%)",
    // Card face
    cardFace: "linear-gradient(170deg, #f2f0eb 0%, #e8e5de 40%, #ddd9d0 100%)",
    // Card back — machine pattern
    cardBack: "linear-gradient(135deg, #1a1a20 0%, #22222a 50%, #1a1a20 100%)",
    // Action button base
    button: "linear-gradient(180deg, #1e1e24 0%, #18181e 100%)",
    // Gold shimmer
    gold: "linear-gradient(135deg, #c49a3c 0%, #d4aa4b 50%, #c49a3c 100%)",
  },

  // The felt — barely-green charcoal (restrained, not emerald)
  felt: {
    deep: "#0c1610",
    base: "#142018",
    light: "#1e3028",
    accent: "#2a4838",
  },

  // Text — silver-grey family
  text: {
    primary: "#d8d8e0",
    secondary: "#808098",
    muted: "#505068",
    dim: "#383848",
  },

  // Accents — precise, mechanical
  accent: {
    silver: "#b0b0b8",
    gold: "#d4a84b",
    goldMuted: "#8a7030",
    goldBright: "#e8c060",
    cyan: "#4ac8d4",        // secondary accent — robotic
    cyanMuted: "#2a8a94",
    emerald: "#3ddc84",
    emeraldMuted: "#2a9d5e",
  },

  // Semantic action colors — desaturated, sleek
  action: {
    fold: "#6a3a44",
    foldHover: "#7d4450",
    call: "#3a6a4a",
    callHover: "#448055",
    raise: "#c49a3c",
    raiseHover: "#d4aa4b",
    check: "#4a4a60",
    checkHover: "#5a5a70",
    allIn: "#a04040",
    allInHover: "#b84848",
  },

  // Card suit colors — crisp against card face
  suit: {
    spades: "#2a2a34",       // near-black on light card
    hearts: "#c43838",
    diamonds: "#3870c4",
    clubs: "#2a8a50",
  },

  // Chips — metallic sheen
  chip: {
    white: "#d0d0d0",
    red: "#b04040",
    blue: "#4060b0",
    black: "#303038",
    green: "#308050",
  },

  // Status
  status: {
    online: "#3ddc84",
    folded: "#505068",
    allIn: "#c05050",
    thinking: "#d4a84b",
    winner: "#d4a84b",
  },
} as const;

export const font = {
  body: "'Inter', system-ui, -apple-system, sans-serif",
  mono: "'JetBrains Mono', 'Fira Code', monospace",
} as const;

export const size = {
  card: { width: 62, height: 88 },
  radius: { xs: 3, sm: 5, md: 8, lg: 12, xl: 16 },
} as const;

export const shadow = {
  sm: "0 1px 3px rgba(0,0,0,0.4)",
  md: "0 4px 12px rgba(0,0,0,0.5)",
  lg: "0 8px 24px rgba(0,0,0,0.6)",
  card: "0 2px 8px rgba(0,0,0,0.5), 0 1px 2px rgba(0,0,0,0.3)",
  cardHover: "0 6px 20px rgba(0,0,0,0.6), 0 2px 6px rgba(0,0,0,0.4)",
  glow: (c: string) => `0 0 12px ${c}40, 0 0 4px ${c}20`,
  glowStrong: (c: string) => `0 0 20px ${c}60, 0 0 8px ${c}30`,
} as const;

export const transition = {
  fast: "all 0.12s ease",
  normal: "all 0.2s ease",
  slow: "all 0.35s ease",
  spring: "all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)",
} as const;
