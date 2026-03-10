"""Layer 1: Equity calculator.

Supports hand vs range, range vs range, and multiway equity calculations
using both exhaustive enumeration and Monte Carlo sampling.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import combinations

import jax
import jax.numpy as jnp

from plo_engine.types import PLOHand, Board, Range
from plo_engine.hand_evaluator import best_plo_hand

# When total evaluations fall below this, use exhaustive enumeration
ENUM_THRESHOLD = 1_000_000


@dataclass(frozen=True)
class EquityResult:
    """Result of an equity calculation."""
    equity: float
    win_pct: float
    tie_pct: float
    loss_pct: float
    sample_count: int
    confidence_interval: tuple[float, float] | None


@dataclass(frozen=True)
class MultiplayerEquityResult:
    """Equity results for each player in a multiway pot."""
    results: list[EquityResult]
    sample_count: int


def _remaining_cards(dead_cards: set[int]) -> list[int]:
    """Cards not in the dead set."""
    return [c for c in range(52) if c not in dead_cards]


def equity_hand_vs_range(
    hand: PLOHand,
    opponent_range: Range,
    board: Board,
    *,
    num_samples: int | None = None,
    rng_key: jax.Array | None = None,
) -> EquityResult:
    """Calculate equity of a specific hand against an opponent range.

    If num_samples is None, use exhaustive enumeration when feasible.
    Otherwise, use Monte Carlo.
    """
    dead_cards = set(hand) | set(board)
    filtered = opponent_range.remove_blockers(dead_cards)

    if not filtered.hands:
        return EquityResult(1.0, 1.0, 0.0, 0.0, 0, None)

    cards_to_come = 5 - len(board)
    remaining = _remaining_cards(dead_cards)

    # Decide: enumerate or MC
    if num_samples is None:
        # Estimate total evaluations
        num_opp_hands = len(filtered.hands)
        if cards_to_come == 0:
            total_evals = num_opp_hands
        else:
            num_runouts = math.comb(len(remaining), cards_to_come)
            total_evals = num_opp_hands * num_runouts

        if total_evals <= ENUM_THRESHOLD:
            return _enumerate_hand_vs_range(hand, filtered, board, dead_cards)
        else:
            num_samples = 10_000  # default MC

    if rng_key is None:
        rng_key = jax.random.PRNGKey(0)

    return _mc_hand_vs_range(hand, filtered, board, dead_cards, num_samples, rng_key)


def _enumerate_hand_vs_range(
    hand: PLOHand,
    opponent_range: Range,
    board: Board,
    dead_cards: set[int],
) -> EquityResult:
    """Exhaustive enumeration for hand vs range."""
    cards_to_come = 5 - len(board)
    wins = 0.0
    ties = 0.0
    total = 0.0

    remaining = _remaining_cards(dead_cards)

    for opp_hand, weight in opponent_range.hands.items():
        if any(c in dead_cards for c in opp_hand):
            continue

        opp_dead = dead_cards | set(opp_hand)
        opp_remaining = [c for c in remaining if c not in opp_hand]

        if cards_to_come == 0:
            full_board = board
            our_rank = best_plo_hand(hand, full_board)
            opp_rank = best_plo_hand(opp_hand, full_board)
            if our_rank > opp_rank:
                wins += weight
            elif our_rank == opp_rank:
                ties += weight
            total += weight
        else:
            for runout in combinations(opp_remaining, cards_to_come):
                full_board = tuple(sorted(board + runout))
                our_rank = best_plo_hand(hand, full_board)
                opp_rank = best_plo_hand(opp_hand, full_board)
                if our_rank > opp_rank:
                    wins += weight
                elif our_rank == opp_rank:
                    ties += weight
                total += weight

    if total == 0:
        return EquityResult(0.5, 0.0, 0.0, 0.0, 0, None)

    equity = (wins + ties * 0.5) / total
    win_pct = wins / total
    tie_pct = ties / total
    loss_pct = 1.0 - win_pct - tie_pct

    return EquityResult(
        equity=equity,
        win_pct=win_pct,
        tie_pct=tie_pct,
        loss_pct=loss_pct,
        sample_count=int(total),
        confidence_interval=None,  # exact
    )


def _mc_hand_vs_range(
    hand: PLOHand,
    opponent_range: Range,
    board: Board,
    dead_cards: set[int],
    num_samples: int,
    rng_key: jax.Array,
) -> EquityResult:
    """Monte Carlo equity estimation."""
    cards_to_come = 5 - len(board)
    wins = 0
    ties = 0
    total = 0

    filtered_normalized = opponent_range.normalize()

    for i in range(num_samples):
        key = jax.random.fold_in(rng_key, i)
        k1, k2 = jax.random.split(key)

        # Sample opponent hand
        try:
            opp_hand = filtered_normalized.sample_hand(k1, dead_cards)
        except ValueError:
            continue

        # Sample remaining board cards
        all_dead = dead_cards | set(opp_hand)
        remaining = _remaining_cards(all_dead)

        if cards_to_come > 0 and len(remaining) < cards_to_come:
            continue

        if cards_to_come > 0:
            indices = jax.random.choice(
                k2, len(remaining), shape=(cards_to_come,), replace=False
            )
            runout = tuple(remaining[int(idx)] for idx in indices)
            full_board = tuple(sorted(board + runout))
        else:
            full_board = board

        our_rank = best_plo_hand(hand, full_board)
        opp_rank = best_plo_hand(opp_hand, full_board)

        if our_rank > opp_rank:
            wins += 1
        elif our_rank == opp_rank:
            ties += 1
        total += 1

    if total == 0:
        return EquityResult(0.5, 0.0, 0.0, 0.0, 0, None)

    equity = (wins + ties * 0.5) / total
    win_pct = wins / total
    tie_pct = ties / total
    loss_pct = 1.0 - win_pct - tie_pct
    ci_half = 1.96 * math.sqrt(equity * (1 - equity) / total) if total > 0 else 0

    return EquityResult(
        equity=equity,
        win_pct=win_pct,
        tie_pct=tie_pct,
        loss_pct=loss_pct,
        sample_count=total,
        confidence_interval=(equity - ci_half, equity + ci_half),
    )


def equity_range_vs_range(
    range_a: Range,
    range_b: Range,
    board: Board,
    *,
    num_samples: int = 10_000,
    rng_key: jax.Array | None = None,
) -> EquityResult:
    """Calculate equity of range_a against range_b. Always Monte Carlo."""
    if rng_key is None:
        rng_key = jax.random.PRNGKey(0)

    dead_cards_board = set(board)
    wins = 0
    ties = 0
    total = 0

    range_a_norm = range_a.remove_blockers(dead_cards_board).normalize()
    range_b_norm = range_b.remove_blockers(dead_cards_board).normalize()

    cards_to_come = 5 - len(board)

    for i in range(num_samples):
        key = jax.random.fold_in(rng_key, i)
        k1, k2, k3 = jax.random.split(key, 3)

        # Sample hand A
        try:
            hand_a = range_a_norm.sample_hand(k1, dead_cards_board)
        except ValueError:
            continue
        dead_a = dead_cards_board | set(hand_a)

        # Sample hand B (must not conflict with hand A)
        try:
            hand_b = range_b_norm.sample_hand(k2, dead_a)
        except ValueError:
            continue
        all_dead = dead_a | set(hand_b)

        # Sample runout
        remaining = _remaining_cards(all_dead)
        if cards_to_come > 0 and len(remaining) < cards_to_come:
            continue

        if cards_to_come > 0:
            indices = jax.random.choice(
                k3, len(remaining), shape=(cards_to_come,), replace=False
            )
            runout = tuple(remaining[int(idx)] for idx in indices)
            full_board = tuple(sorted(board + runout))
        else:
            full_board = board

        rank_a = best_plo_hand(hand_a, full_board)
        rank_b = best_plo_hand(hand_b, full_board)

        if rank_a > rank_b:
            wins += 1
        elif rank_a == rank_b:
            ties += 1
        total += 1

    if total == 0:
        return EquityResult(0.5, 0.0, 0.0, 0.0, 0, None)

    equity = (wins + ties * 0.5) / total
    win_pct = wins / total
    tie_pct = ties / total
    loss_pct = 1.0 - win_pct - tie_pct
    ci_half = 1.96 * math.sqrt(equity * (1 - equity) / total)

    return EquityResult(
        equity=equity,
        win_pct=win_pct,
        tie_pct=tie_pct,
        loss_pct=loss_pct,
        sample_count=total,
        confidence_interval=(equity - ci_half, equity + ci_half),
    )


def equity_multiway(
    hands_or_ranges: list[PLOHand | Range],
    board: Board,
    *,
    num_samples: int = 10_000,
    rng_key: jax.Array | None = None,
) -> MultiplayerEquityResult:
    """Equity for a multiway pot (2-6 players)."""
    if rng_key is None:
        rng_key = jax.random.PRNGKey(0)

    n_players = len(hands_or_ranges)
    wins = [0.0] * n_players
    ties = [0.0] * n_players
    total = 0

    cards_to_come = 5 - len(board)
    dead_board = set(board)

    for i in range(num_samples):
        key = jax.random.fold_in(rng_key, i)
        keys = jax.random.split(key, n_players + 1)

        # Sample concrete hands for each player
        dead = set(dead_board)
        concrete_hands: list[PLOHand] = []
        valid = True

        for j, hor in enumerate(hands_or_ranges):
            if isinstance(hor, tuple):
                # Specific hand
                if any(c in dead for c in hor):
                    valid = False
                    break
                concrete_hands.append(hor)
                dead |= set(hor)
            else:
                # Range — sample
                try:
                    h = hor.sample_hand(keys[j], dead)
                except ValueError:
                    valid = False
                    break
                concrete_hands.append(h)
                dead |= set(h)

        if not valid:
            continue

        # Sample runout
        remaining = _remaining_cards(dead)
        if cards_to_come > 0 and len(remaining) < cards_to_come:
            continue

        if cards_to_come > 0:
            indices = jax.random.choice(
                keys[-1], len(remaining), shape=(cards_to_come,), replace=False
            )
            runout = tuple(remaining[int(idx)] for idx in indices)
            full_board = tuple(sorted(board + runout))
        else:
            full_board = board

        # Evaluate all hands
        ranks = [best_plo_hand(h, full_board) for h in concrete_hands]
        best_rank = max(ranks)
        winners = [j for j in range(n_players) if ranks[j] == best_rank]

        for j in range(n_players):
            if ranks[j] == best_rank:
                if len(winners) == 1:
                    wins[j] += 1
                else:
                    ties[j] += 1.0 / len(winners)

        total += 1

    results = []
    for j in range(n_players):
        if total == 0:
            results.append(EquityResult(1.0 / n_players, 0, 0, 0, 0, None))
        else:
            eq = (wins[j] + ties[j]) / total
            win_pct = wins[j] / total
            # For multiway, tie_pct represents split pot scenarios
            tie_pct_j = ties[j] / total
            loss_pct = 1.0 - win_pct - tie_pct_j
            ci_half = 1.96 * math.sqrt(eq * (1 - eq) / total) if total > 0 else 0
            results.append(EquityResult(
                equity=eq,
                win_pct=win_pct,
                tie_pct=tie_pct_j,
                loss_pct=loss_pct,
                sample_count=total,
                confidence_interval=(eq - ci_half, eq + ci_half),
            ))

    return MultiplayerEquityResult(results=results, sample_count=total)
