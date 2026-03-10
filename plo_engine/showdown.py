"""Winner determination and pot distribution at showdown."""

from __future__ import annotations

from dataclasses import dataclass

from plo_engine.types import PLOHand, Board, HandRank
from plo_engine.hand_evaluator import best_plo_hand
from plo_engine.betting import Pot


@dataclass
class ShowdownResult:
    """Result of the showdown for one pot."""
    pot: Pot
    winners: list[int]              # seat indices of winner(s)
    winning_hand_rank: HandRank
    amount_per_winner: float        # pot.amount / len(winners)


@dataclass
class HandResult:
    """Complete result of a hand."""
    showdown_results: list[ShowdownResult]   # one per pot
    net_profit: dict[int, float]             # seat -> net chips won/lost
    went_to_showdown: bool                   # False if everyone folded
    winning_seat: int | None                 # only set if won without showdown
    hand_number: int


def resolve_showdown(
    hole_cards: dict[int, PLOHand],
    board: Board,
    pots: list[Pot],
    folded: set[int],
    button_position: int,
) -> list[ShowdownResult]:
    """
    Evaluate all remaining players' hands and determine winners for each pot.

    hole_cards: {seat_index: PLOHand} for all players dealt in.
    board: the final 5-card board.
    pots: list of Pot objects (main + side pots).
    folded: set of seat indices that have folded.
    button_position: for odd-chip rule (first left of button gets odd chip).

    Returns one ShowdownResult per pot.
    """
    if len(board) != 5:
        raise ValueError(f"Showdown requires 5 board cards, got {len(board)}")

    # Evaluate hands for all non-folded players
    hand_ranks: dict[int, HandRank] = {}
    for seat, hole in hole_cards.items():
        if seat not in folded:
            hand_ranks[seat] = best_plo_hand(hole, board)

    results: list[ShowdownResult] = []
    for pot in pots:
        # Among eligible players who haven't folded
        contenders = [s for s in pot.eligible_players if s not in folded]
        if not contenders:
            # All eligible players folded — shouldn't normally happen
            # Give to first eligible player (edge case)
            contenders = pot.eligible_players[:1]

        # Find best hand rank among contenders
        best_rank = max(hand_ranks.get(s, -1) for s in contenders)
        winners = [s for s in contenders if hand_ranks.get(s, -1) == best_rank]

        amount_each = pot.amount / len(winners)

        results.append(ShowdownResult(
            pot=pot,
            winners=sorted(winners),
            winning_hand_rank=best_rank,
            amount_per_winner=amount_each,
        ))

    return results


def distribute_pots(
    results: list[ShowdownResult],
    investments: dict[int, float],
) -> dict[int, float]:
    """
    Compute net profit/loss per seat from showdown results.

    Returns {seat: net_change} where negative means lost chips.
    """
    winnings: dict[int, float] = {}
    for seat in investments:
        winnings[seat] = 0.0

    for result in results:
        for seat in result.winners:
            winnings[seat] = winnings.get(seat, 0.0) + result.amount_per_winner

    # Net profit = winnings - investment
    net: dict[int, float] = {}
    for seat in investments:
        net[seat] = round(winnings.get(seat, 0.0) - investments[seat], 2)

    return net
