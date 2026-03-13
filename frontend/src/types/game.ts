/** Wire protocol types for the WebSocket game connection. */

export interface PlayerInfo {
  seat: number;
  name: string;
  stack: number;
  is_human: boolean;
}

export interface OpponentInfo {
  seat: number;
  stack: number;
  chips_in_pot: number;
  is_folded: boolean;
  is_all_in: boolean;
  name: string;
  hole_cards: string[] | null;
}

export interface LegalAction {
  action_type: string; // "fold" | "check" | "call" | "bet" | "raise"
  player_seat: number;
  amount: number;
  is_all_in: boolean;
}

export interface ActionView {
  my_seat: number;
  my_hole_cards: string[];
  my_stack: number;
  my_chips_in_pot: number;
  board: string[];
  pot_total: number;
  current_bet: number;
  min_raise: number;
  pot_limit_max: number;
  opponents: OpponentInfo[];
  button_position: number;
  blind_level: { small_blind: number; big_blind: number; ante: number };
  hand_phase: string;
  legal_actions: LegalAction[];
}

export interface HandResultInfo {
  hand_number: number;
  net_profit: Record<string, number>;
  went_to_showdown: boolean;
  winning_seat: number | null;
  board: string[];
  showdown_hands: Record<string, string[]>;
}

export interface StandingInfo {
  name: string;
  stack: number;
}

export interface SessionConfig {
  opponents: number;
  bot_type: string;
  stack: number;
  blinds: string;
}

// ── Game state for useReducer ──

export type GameStatus = "lobby" | "starting" | "playing" | "between_hands" | "session_over";

export interface GameState {
  status: GameStatus;
  // Session
  players: PlayerInfo[];
  blinds: { small_blind: number; big_blind: number } | null;
  // Current hand
  handNumber: number;
  button: number;
  yourSeat: number;
  heroCards: string[];
  board: string[];
  phase: string;
  pot: number;
  heroStack: number;
  // Opponents (from latest view)
  opponents: OpponentInfo[];
  // Action state
  awaitingAction: boolean;
  toCall: number;
  minRaise: number;
  potLimit: number;
  legalActions: LegalAction[];
  // Result
  handResult: HandResultInfo | null;
  standings: StandingInfo[];
  // Meta
  sessionOverReason: string | null;
  error: string | null;
}

export const INITIAL_STATE: GameState = {
  status: "lobby",
  players: [],
  blinds: null,
  handNumber: 0,
  button: 0,
  yourSeat: 0,
  heroCards: [],
  board: [],
  phase: "",
  pot: 0,
  heroStack: 0,
  opponents: [],
  awaitingAction: false,
  toCall: 0,
  minRaise: 0,
  potLimit: 0,
  legalActions: [],
  handResult: null,
  standings: [],
  sessionOverReason: null,
  error: null,
};
