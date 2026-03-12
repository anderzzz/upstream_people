/** Custom hook: manages WebSocket connection and game state via useReducer. */

import { useReducer, useCallback, useRef, useEffect } from "react";
import {
  GameState,
  INITIAL_STATE,
  SessionConfig,
  ActionView,
  HandResultInfo,
  StandingInfo,
  PlayerInfo,
} from "../types/game";

// ── Actions ──

type GameAction =
  | { type: "connected" }
  | { type: "session_started"; players: PlayerInfo[]; blinds: { small_blind: number; big_blind: number } }
  | { type: "hand_started"; hand_number: number; button: number; your_seat: number; players: { seat: number; name: string; stack: number }[] }
  | { type: "hole_cards"; cards: string[] }
  | { type: "action_request"; view: ActionView }
  | { type: "action_performed"; seat: number; player_name: string; action: string; amount: number; is_all_in: boolean }
  | { type: "board_dealt"; board: string[]; phase: string }
  | { type: "hand_result"; result: HandResultInfo }
  | { type: "standings"; standings: StandingInfo[] }
  | { type: "session_over"; reason: string }
  | { type: "error"; message: string }
  | { type: "action_sent" }
  | { type: "reset" };

function reducer(state: GameState, action: GameAction): GameState {
  switch (action.type) {
    case "connected":
      return { ...state, error: null };

    case "session_started":
      return {
        ...state,
        status: "starting",
        players: action.players,
        blinds: action.blinds,
        heroStack: action.players.find((p) => p.is_human)?.stack ?? 0,
      };

    case "hand_started": {
      // Update stacks from hand_started players list
      const opponents = action.players
        .filter((p) => p.seat !== action.your_seat)
        .map((p) => ({
          seat: p.seat,
          stack: p.stack,
          chips_in_pot: 0,
          is_folded: false,
          is_all_in: false,
          name: p.name,
          hole_cards: null,
        }));
      const heroInfo = action.players.find((p) => p.seat === action.your_seat);
      return {
        ...state,
        status: "playing",
        handNumber: action.hand_number,
        button: action.button,
        yourSeat: action.your_seat,
        heroCards: [],
        board: [],
        phase: "PREFLOP",
        pot: 0,
        heroStack: heroInfo?.stack ?? state.heroStack,
        opponents,
        awaitingAction: false,
        toCall: 0,
        minRaise: 0,
        potLimit: 0,
        legalActions: [],
        handResult: null,
        error: null,
      };
    }

    case "hole_cards":
      return { ...state, heroCards: action.cards };

    case "action_request": {
      const v = action.view;
      return {
        ...state,
        awaitingAction: true,
        board: v.board,
        pot: v.pot_total,
        heroStack: v.my_stack,
        heroCards: v.my_hole_cards,
        opponents: v.opponents,
        phase: v.hand_phase.replace("_BETTING", ""),
        toCall: Math.max(0, v.current_bet - v.my_chips_in_pot),
        minRaise: v.min_raise,
        potLimit: v.pot_limit_max,
        legalActions: v.legal_actions,
      };
    }

    case "action_performed": {
      // Update opponent state from action
      const opponents = state.opponents.map((opp) => {
        if (opp.seat !== action.seat) return opp;
        if (action.action === "fold") return { ...opp, is_folded: true };
        if (action.is_all_in) return { ...opp, is_all_in: true };
        return opp;
      });
      return { ...state, opponents };
    }

    case "board_dealt":
      return {
        ...state,
        board: action.board,
        phase: action.phase,
      };

    case "hand_result":
      return {
        ...state,
        status: "between_hands",
        awaitingAction: false,
        handResult: action.result,
        board: action.result.board.length > 0 ? action.result.board : state.board,
      };

    case "standings":
      return { ...state, standings: action.standings };

    case "session_over":
      return {
        ...state,
        status: "session_over",
        sessionOverReason: action.reason,
      };

    case "error":
      return { ...state, error: action.message };

    case "action_sent":
      return { ...state, awaitingAction: false };

    case "reset":
      return INITIAL_STATE;

    default:
      return state;
  }
}

// ── Hook ──

const WS_URL = "ws://localhost:8000/game/ws";

export function useGameSocket() {
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE);
  const wsRef = useRef<WebSocket | null>(null);

  // Connect on mount
  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      // Dispatch the message directly — types match
      dispatch(msg as GameAction);
    };

    ws.onerror = () => {
      dispatch({ type: "error", message: "WebSocket connection error" });
    };

    ws.onclose = () => {
      wsRef.current = null;
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, []);

  const sendJson = useCallback((msg: unknown) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(msg));
    }
  }, []);

  const startSession = useCallback(
    (config: SessionConfig) => {
      sendJson({ type: "start_session", config });
    },
    [sendJson],
  );

  const sendAction = useCallback(
    (action: string, amount?: number) => {
      dispatch({ type: "action_sent" });
      sendJson({ type: "player_action", action, amount: amount ?? null });
    },
    [sendJson],
  );

  const nextHand = useCallback(() => {
    sendJson({ type: "next_hand" });
  }, [sendJson]);

  const quit = useCallback(() => {
    sendJson({ type: "quit" });
  }, [sendJson]);

  return { state, startSession, sendAction, nextHand, quit };
}
