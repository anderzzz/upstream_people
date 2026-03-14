/**
 * Hooks for calling analysis API endpoints.
 */

import { useState, useCallback } from "react";

const API_BASE = "/analysis";

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

// --- Types ---

export interface EquityResult {
  equity: number;
  win: number;
  tie: number;
  loss: number;
  samples: number;
  confidence_interval: [number, number] | null;
}

export interface HandPropertiesResult {
  hand: string;
  board: string;
  board_texture: BoardTextureResult;
  hand_rank: number;
  made_hand: string;
  is_nutted: boolean;
  draws: string[];
  nut_draw_outs: number;
  total_outs: number;
  draw_equity_estimate: number;
  blocks_nut_flush: boolean;
  blocks_second_nut_flush: boolean;
  blocks_nut_straight: boolean;
  blocks_sets: number[];
  blocker_score: number;
  nut_rank: number;
  distance_to_nuts: number;
  description: string;
  is_good_bluff_candidate: boolean;
}

export interface BoardTextureResult {
  board: string;
  flush_draw: string;
  connectedness: string;
  pairedness: string;
  height: string;
  has_ace: boolean;
  num_broadway: number;
  straight_possible: boolean;
  flush_possible: boolean;
  flush_suit: string | null;
  nut_hand_description: string;
  description: string;
}

export interface StartingHandResult {
  hand: string;
  category: string;
  suit_structure: string;
  is_connected: boolean;
  gap_count: number;
  highest_pair: number | null;
  num_pairs: number;
  has_ace: boolean;
  has_suited_ace: boolean;
  suits_description: string;
  preflop_equity_estimate: number;
  description: string;
  precomputed_equities: Record<string, { equity: number; win: number; tie: number }> | null;
}

export interface ActionEVResult {
  action: string;
  ev: number;
  ev_bb: number;
}

export interface EquityMapCard {
  card: string;
  card_int: number;
  rank: number;
  suit: number;
  equity: number;
  delta: number;
}

export interface EquityMapResult {
  baseline_equity: number;
  board: string[];
  hand: string[];
  cards: EquityMapCard[];
}

// --- Generic fetch hook ---

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

function useApi<TReq, TRes>(path: string) {
  const [state, setState] = useState<UseApiState<TRes>>({
    data: null,
    loading: false,
    error: null,
  });

  const execute = useCallback(
    async (body: TReq) => {
      setState({ data: null, loading: true, error: null });
      try {
        const result = await post<TRes>(path, body);
        setState({ data: result, loading: false, error: null });
        return result;
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        setState({ data: null, loading: false, error: msg });
        return null;
      }
    },
    [path],
  );

  return { ...state, execute };
}

// --- Typed API hooks ---

export function useEquity() {
  return useApi<{ hand: string[]; board: string[]; opponents: number }, EquityResult>(
    "/equity",
  );
}

export function useHandProperties() {
  return useApi<{ hand: string[]; board: string[] }, HandPropertiesResult>(
    "/hand-properties",
  );
}

export function useStartingHand() {
  return useApi<{ hand: string[] }, StartingHandResult>("/starting-hand");
}

export function useActionEV() {
  return useApi<
    {
      hand: string[];
      board: string[];
      pot: number;
      to_call: number;
      stack: number;
      bb_size: number;
      opponents: number;
    },
    ActionEVResult[]
  >("/action-ev");
}

export function useEquityMap() {
  return useApi<
    { hand: string[]; board: string[]; opponents: number; samples: number },
    EquityMapResult
  >("/equity-map");
}
