"""Utility functions — parsing, display, formatting helpers.

Most parsing utilities live in types.py. This module provides higher-level
formatting for analysis output.
"""
from __future__ import annotations

from plo_engine.types import cards_to_str, PLOHand, Board
from plo_engine.equity import EquityResult, MultiplayerEquityResult


def format_equity(result: EquityResult) -> str:
    """Format an equity result for display."""
    parts = [
        f"Equity: {result.equity:.1%}",
        f"Win: {result.win_pct:.1%}",
        f"Tie: {result.tie_pct:.1%}",
        f"Loss: {result.loss_pct:.1%}",
    ]
    if result.confidence_interval:
        lo, hi = result.confidence_interval
        parts.append(f"95% CI: [{lo:.1%}, {hi:.1%}]")
    parts.append(f"Samples: {result.sample_count:,}")
    return " | ".join(parts)


def format_multiway_equity(result: MultiplayerEquityResult) -> str:
    """Format multiway equity results for display."""
    lines = [f"Multiway equity ({result.sample_count:,} samples):"]
    for i, r in enumerate(result.results):
        lines.append(f"  Player {i + 1}: {r.equity:.1%} (W:{r.win_pct:.1%} T:{r.tie_pct:.1%})")
    return "\n".join(lines)


def format_hand_board(hand: PLOHand, board: Board) -> str:
    """Format hand and board for display."""
    hand_str = cards_to_str(hand)
    board_str = cards_to_str(board) if board else "(preflop)"
    return f"Hand: [{hand_str}]  Board: [{board_str}]"
