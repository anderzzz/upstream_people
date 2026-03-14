"""Analysis endpoints — equity, EV, hand properties, board texture."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from plo_engine.types import (
    parse_card, parse_cards, make_plo_hand, make_board,
    PLOHand, Board, Range, card_to_str,
)
from plo_engine.domain import (
    BoardTexture, HandProperties, StartingHandProfile,
)
from plo_engine.equity import equity_hand_vs_range, equity_multiway
from plo_engine.ev import evaluate_actions, ActionEV
from server.serializers import (
    serialize_board_texture,
    serialize_hand_properties,
    serialize_starting_hand_profile,
    serialize_equity_result,
    serialize_action_ev,
)

router = APIRouter()

# Precomputed table (loaded lazily on first request)
_starting_hand_table: dict | None = None
_TABLE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "starting_hand_table.json"


def _load_starting_hand_table() -> dict:
    global _starting_hand_table
    if _starting_hand_table is None and _TABLE_PATH.exists():
        with open(_TABLE_PATH) as f:
            _starting_hand_table = json.load(f)
    return _starting_hand_table or {}


def _parse_hand(cards: list[str]) -> PLOHand:
    """Parse list of card strings into a PLOHand."""
    ints = tuple(parse_card(c) for c in cards)
    return make_plo_hand(*ints)


def _parse_board(cards: list[str]) -> Board:
    """Parse list of card strings into a Board."""
    if not cards:
        return ()
    ints = tuple(parse_card(c) for c in cards)
    return make_board(*ints)


# --- Request schemas ---

class EquityRequest(BaseModel):
    hand: list[str]
    board: list[str] = []
    opponents: int = 1


class HandInfoRequest(BaseModel):
    hand: list[str]
    board: list[str]


class BoardTextureRequest(BaseModel):
    board: list[str]


class StartingHandRequest(BaseModel):
    hand: list[str]


class ActionEVRequest(BaseModel):
    hand: list[str]
    board: list[str]
    pot: float
    to_call: float = 0.0
    stack: float = 100.0
    bb_size: float = 1.0
    opponents: int = 1
    raise_sizes: list[float] | None = None


class EquityMapRequest(BaseModel):
    hand: list[str]
    board: list[str]
    opponents: int = 1
    samples: int = 5000


# --- Routes ---

@router.post("/equity")
async def compute_equity(req: EquityRequest):
    """Compute equity of a hand vs random opponent range(s)."""
    hand = _parse_hand(req.hand)
    board = _parse_board(req.board)

    if req.opponents == 1:
        result = equity_hand_vs_range(hand, Range.full(), board)
        return serialize_equity_result(result)
    else:
        players: list[PLOHand | Range] = [hand] + [Range.full()] * req.opponents
        multi = equity_multiway(players, board)
        return serialize_equity_result(multi.results[0])


@router.post("/hand-properties")
async def hand_properties(req: HandInfoRequest):
    """Analyze hand properties (made hand, draws, blockers)."""
    hand = _parse_hand(req.hand)
    board = _parse_board(req.board)
    props = HandProperties.analyze(hand, board)
    return serialize_hand_properties(props)


@router.post("/board-texture")
async def board_texture(req: BoardTextureRequest):
    """Analyze board texture."""
    board = _parse_board(req.board)
    bt = BoardTexture.from_board(board)
    return serialize_board_texture(bt)


@router.post("/starting-hand")
async def starting_hand(req: StartingHandRequest):
    """Classify a starting hand and return precomputed equities if available."""
    hand = _parse_hand(req.hand)
    profile = StartingHandProfile.classify(hand)
    result = serialize_starting_hand_profile(profile)

    # Look up precomputed equities
    table = _load_starting_hand_table()
    key = ",".join(str(c) for c in hand)
    if key in table:
        result["precomputed_equities"] = table[key].get("equities", {})
    else:
        result["precomputed_equities"] = None

    return result


@router.post("/action-ev")
async def action_ev(req: ActionEVRequest):
    """Evaluate EV of available actions."""
    hand = _parse_hand(req.hand)
    board = _parse_board(req.board)
    opponent_range = Range.full()

    actions = evaluate_actions(
        hand, board, opponent_range,
        pot=req.pot,
        to_call=req.to_call,
        stack=req.stack,
        bb_size=req.bb_size,
        raise_sizes=req.raise_sizes,
    )
    return [serialize_action_ev(a) for a in actions]


@router.post("/equity-map")
async def equity_map(req: EquityMapRequest):
    """Compute equity for each possible next card.

    Returns a list of {card, equity, delta} for every non-dead card,
    showing how equity changes if that card appears next.
    """
    hand = _parse_hand(req.hand)
    board = _parse_board(req.board)

    if len(board) < 3 or len(board) >= 5:
        return {"error": "Equity map requires a flop (3 cards) or turn (4 cards) board"}

    dead = set(hand) | set(board)
    opponent_range = Range.full()

    # Baseline equity on current board
    if req.opponents == 1:
        baseline = equity_hand_vs_range(
            hand, opponent_range, board, num_samples=req.samples,
        )
    else:
        players: list[PLOHand | Range] = [hand] + [opponent_range] * req.opponents
        baseline_multi = equity_multiway(players, board, num_samples=req.samples)
        baseline = baseline_multi.results[0]

    base_eq = baseline.equity

    # Compute equity for each possible next card
    cards = []
    for c in range(52):
        if c in dead:
            continue

        new_board = make_board(*(list(board) + [c]))

        if req.opponents == 1:
            result = equity_hand_vs_range(
                hand, opponent_range, new_board, num_samples=req.samples,
            )
        else:
            players = [hand] + [opponent_range] * req.opponents
            result_multi = equity_multiway(players, new_board, num_samples=req.samples)
            result = result_multi.results[0]

        cards.append({
            "card": card_to_str(c),
            "card_int": c,
            "rank": c // 4,
            "suit": c % 4,
            "equity": round(result.equity, 4),
            "delta": round(result.equity - base_eq, 4),
        })

    cards.sort(key=lambda x: x["equity"], reverse=True)

    return {
        "baseline_equity": round(base_eq, 4),
        "board": [card_to_str(c) for c in board],
        "hand": [card_to_str(c) for c in hand],
        "cards": cards,
    }


@router.get("/preflop-table")
async def preflop_table(
    category: str | None = None,
    min_equity: float | None = None,
    limit: int = 100,
    offset: int = 0,
):
    """Serve the precomputed starting hand table (or a filtered slice)."""
    table = _load_starting_hand_table()
    if not table:
        return {"error": "Precomputed table not available. Run scripts/precompute_starting_hands.py first."}

    entries = list(table.values())

    # Filter by category
    if category:
        entries = [e for e in entries if e.get("category") == category.upper()]

    # Filter by minimum equity (vs 1 opponent)
    if min_equity is not None:
        entries = [
            e for e in entries
            if e.get("equities", {}).get("1", {}).get("equity", 0) >= min_equity
        ]

    total = len(entries)

    # Sort by equity vs 1 opponent (descending)
    entries.sort(
        key=lambda e: e.get("equities", {}).get("1", {}).get("equity", 0),
        reverse=True,
    )

    # Paginate
    entries = entries[offset:offset + limit]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "entries": entries,
    }


@router.get("/ping")
async def ping():
    return {"status": "ok"}
