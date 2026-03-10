"""Layer 0: Pure Python hand evaluator.

Reference implementation — correctness is paramount, performance is secondary.

HandRank encoding:
    bits 20-23: hand category (0=high card .. 8=straight flush)
    bits 0-19:  tiebreaker kickers (up to 5 × 4 bits, rank values 0-12)
"""
from __future__ import annotations

from itertools import combinations

from plo_engine.types import FiveCardHand, PLOHand, Board, HandRank


def _encode_rank(category: int, kickers: tuple[int, ...]) -> HandRank:
    """Encode category + kickers into a single comparable integer.

    category: 0-8
    kickers: up to 5 rank values (0-12), ordered from most to least significant.
    """
    result = category << 20
    for i, k in enumerate(kickers):
        # kicker 0 is most significant, placed in highest bits
        shift = (4 - i) * 4
        result |= k << shift
    return result


def category_of(hand_rank: HandRank) -> int:
    """Extract the category (0-8) from a HandRank."""
    return hand_rank >> 20


def evaluate_5card(hand: FiveCardHand) -> HandRank:
    """Evaluate a 5-card poker hand and return its rank as a comparable integer.

    Higher integer = better hand.
    """
    ranks = sorted((c // 4 for c in hand), reverse=True)
    suits = [c % 4 for c in hand]

    # Count occurrences of each rank
    rank_counts: dict[int, int] = {}
    for r in ranks:
        rank_counts[r] = rank_counts.get(r, 0) + 1

    # Flush detection
    is_flush = len(set(suits)) == 1

    # Straight detection
    unique_ranks = sorted(set(ranks), reverse=True)
    is_straight = False
    straight_high = 0

    if len(unique_ranks) == 5:
        if unique_ranks[0] - unique_ranks[4] == 4:
            is_straight = True
            straight_high = unique_ranks[0]
        # Wheel: A-2-3-4-5
        elif unique_ranks == [12, 3, 2, 1, 0]:
            is_straight = True
            straight_high = 3  # 5-high (rank 3 = card '5')

    # Classify by count pattern
    counts_sorted = sorted(rank_counts.values(), reverse=True)

    if is_straight and is_flush:
        # Straight flush
        return _encode_rank(8, (straight_high,))

    if counts_sorted == [4, 1]:
        # Four of a kind
        quad_rank = [r for r, c in rank_counts.items() if c == 4][0]
        kicker = [r for r, c in rank_counts.items() if c == 1][0]
        return _encode_rank(7, (quad_rank, kicker))

    if counts_sorted == [3, 2]:
        # Full house
        trips_rank = [r for r, c in rank_counts.items() if c == 3][0]
        pair_rank = [r for r, c in rank_counts.items() if c == 2][0]
        return _encode_rank(6, (trips_rank, pair_rank))

    if is_flush:
        # Flush — kickers are all 5 ranks descending
        return _encode_rank(5, tuple(ranks))

    if is_straight:
        # Straight
        return _encode_rank(4, (straight_high,))

    if counts_sorted == [3, 1, 1]:
        # Three of a kind
        trips_rank = [r for r, c in rank_counts.items() if c == 3][0]
        kickers = sorted(
            (r for r, c in rank_counts.items() if c == 1), reverse=True
        )
        return _encode_rank(3, (trips_rank, kickers[0], kickers[1]))

    if counts_sorted == [2, 2, 1]:
        # Two pair
        pairs = sorted(
            (r for r, c in rank_counts.items() if c == 2), reverse=True
        )
        kicker = [r for r, c in rank_counts.items() if c == 1][0]
        return _encode_rank(2, (pairs[0], pairs[1], kicker))

    if counts_sorted == [2, 1, 1, 1]:
        # One pair
        pair_rank = [r for r, c in rank_counts.items() if c == 2][0]
        kickers = sorted(
            (r for r, c in rank_counts.items() if c == 1), reverse=True
        )
        return _encode_rank(1, (pair_rank, kickers[0], kickers[1], kickers[2]))

    # High card
    return _encode_rank(0, tuple(ranks))


def best_plo_hand(hole: PLOHand, board: Board) -> HandRank:
    """Find the best legal PLO hand: exactly 2 from hole, 3 from board.

    Iterates over all C(4,2)*C(5,3) = 60 combinations and returns the max.
    """
    if len(hole) != 4:
        raise ValueError(f"PLO hand must have exactly 4 hole cards, got {len(hole)}")
    if len(board) != 5:
        raise ValueError(f"Board must have exactly 5 cards, got {len(board)}")

    best = -1
    for h2 in combinations(hole, 2):
        for b3 in combinations(board, 3):
            five = (*h2, *b3)
            rank = evaluate_5card(five)
            if rank > best:
                best = rank
    return best
