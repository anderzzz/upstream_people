/**
 * Design tokens — the Dark Room palette.
 *
 * Think: private high-stakes room. Matte surfaces, silver accents,
 * deep emerald felt. A robotic dealer pours your drink.
 */

export const color = {
  // Backgrounds — near-black with cool undertones
  bg: {
    base: "#121215",       // deepest background
    surface: "#1a1a1f",    // cards, panels
    elevated: "#252530",   // modals, popovers, hover states
    overlay: "rgba(0, 0, 0, 0.6)",
  },

  // The felt — deep emerald, never bright
  felt: {
    deep: "#0d2818",
    base: "#1a3a2a",
    light: "#2a5040",
  },

  // Text — silver family
  text: {
    primary: "#e0e0e8",
    secondary: "#8888a0",
    muted: "#555568",
  },

  // Accents
  accent: {
    silver: "#c0c0c8",
    gold: "#d4a84b",
    goldMuted: "#a07830",
    emerald: "#3ddc84",
    emeraldMuted: "#2a9d5e",
  },

  // Semantic
  action: {
    fold: "#8b4050",
    call: "#4a7a5a",
    raise: "#d4a84b",
    check: "#6a6a80",
    allIn: "#c05050",
  },

  // Card colors
  suit: {
    spades: "#e0e0e8",
    hearts: "#d45050",
    diamonds: "#5090d4",
    clubs: "#50b878",
  },

  // Chips
  chip: {
    white: "#d8d8d8",
    red: "#b04040",
    blue: "#4060b0",
    black: "#303038",
    green: "#308050",
  },
} as const;

export const font = {
  body: "'Inter', system-ui, -apple-system, sans-serif",
  mono: "'JetBrains Mono', 'Fira Code', monospace",
} as const;

export const size = {
  card: { width: 64, height: 90 },
  radius: { sm: 4, md: 8, lg: 12 },
} as const;
