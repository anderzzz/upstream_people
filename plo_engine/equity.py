"""Layer 1: Equity calculator.

Supports hand vs range, range vs range, and multiway equity calculations
using both exhaustive enumeration and Monte Carlo sampling.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import combinations

import numpy as np
import jax
import jax.numpy as jnp

from plo_engine.types import PLOHand, Board, Range
from plo_engine.hand_evaluator import best_plo_hand


def _prepare_range_arrays(
    range_: Range, dead_cards: set[int],
) -> tuple[np.ndarray, np.ndarray]:
    """Pre-filter a range and build NumPy arrays for fast sampling.

    Returns (hands_array, weights_array) where:
      - hands_array: shape (N, 4) int array of card ints
      - weights_array: shape (N,) float probabilities (sums to 1)
    """
    filtered = range_.remove_blockers(dead_cards)
    if not filtered.hands:
        return np.empty((0, 4), dtype=np.int32), np.empty(0, dtype=np.float64)
    hands_list = list(filtered.hands.keys())
    weights = np.array([filtered.hands[h] for h in hands_list], dtype=np.float64)
    weights /= weights.sum()
    hands_arr = np.array(hands_list, dtype=np.int32)
    return hands_arr, weights

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
    """Monte Carlo equity estimation.

    Uses NumPy for sampling (much faster than JAX for this loop-heavy task).
    Pre-builds filtered range arrays once rather than per-sample.
    """
    cards_to_come = 5 - len(board)
    wins = 0
    ties = 0
    total = 0

    # Pre-build filtered range arrays (one-time cost)
    opp_hands_arr, opp_weights = _prepare_range_arrays(opponent_range, dead_cards)
    if len(opp_hands_arr) == 0:
        return EquityResult(1.0, 1.0, 0.0, 0.0, 0, None)

    # Pre-compute remaining cards (excluding hero + board)
    remaining_base = np.array(_remaining_cards(dead_cards), dtype=np.int32)

    # Use NumPy RNG seeded from JAX key for reproducibility
    seed = int(jax.random.randint(rng_key, (), 0, 2**31 - 1).item())
    rng = np.random.RandomState(seed)

    # Pre-sample all opponent hand indices at once
    opp_indices = rng.choice(len(opp_hands_arr), size=num_samples, p=opp_weights)

    for i in range(num_samples):
        opp_hand = tuple(opp_hands_arr[opp_indices[i]])

        # Check no overlap with dead cards (hero's hand already excluded
        # via _prepare_range_arrays, but board overlap possible on turn/river
        # if opponent hand was filtered before board was set — shouldn't happen
        # here since we filter on dead_cards which includes board)

        # Build remaining deck excluding opponent hand
        opp_set = set(opp_hand)
        remaining = [c for c in remaining_base if c not in opp_set]

        if cards_to_come > 0 and len(remaining) < cards_to_come:
            continue

        if cards_to_come > 0:
            runout_indices = rng.choice(len(remaining), size=cards_to_come, replace=False)
            runout = tuple(remaining[j] for j in runout_indices)
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

    # Pre-build arrays for range A (filtered for board blockers)
    hands_a, weights_a = _prepare_range_arrays(range_a, dead_cards_board)
    if len(hands_a) == 0:
        return EquityResult(0.5, 0.0, 0.0, 0.0, 0, None)

    cards_to_come = 5 - len(board)

    seed = int(jax.random.randint(rng_key, (), 0, 2**31 - 1).item())
    rng = np.random.RandomState(seed)

    # Pre-sample range A indices
    a_indices = rng.choice(len(hands_a), size=num_samples, p=weights_a)

    for i in range(num_samples):
        hand_a = tuple(hands_a[a_indices[i]])
        dead_a = dead_cards_board | set(hand_a)

        # Build filtered range B (must exclude hand A's cards)
        # This per-sample filtering is unavoidable but uses NumPy
        hands_b, weights_b = _prepare_range_arrays(range_b, dead_a)
        if len(hands_b) == 0:
            continue

        b_idx = rng.choice(len(hands_b), p=weights_b)
        hand_b = tuple(hands_b[b_idx])
        all_dead = dead_a | set(hand_b)

        # Sample runout
        remaining = _remaining_cards(all_dead)
        if cards_to_come > 0 and len(remaining) < cards_to_come:
            continue

        if cards_to_come > 0:
            r_indices = rng.choice(len(remaining), size=cards_to_come, replace=False)
            runout = tuple(remaining[j] for j in r_indices)
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


def _is_uniform_range(r: Range) -> bool:
    """Check if a range has uniform weights (all 1.0), like Range.full()."""
    if not r.hands:
        return False
    first = next(iter(r.hands.values()))
    return all(w == first for w in r.hands.values())


def equity_multiway(
    hands_or_ranges: list[PLOHand | Range],
    board: Board,
    *,
    num_samples: int = 10_000,
    rng_key: jax.Array | None = None,
) -> MultiplayerEquityResult:
    """Equity for a multiway pot (2-6 players).

    Uses NumPy for all sampling. For uniform ranges (Range.full()), deals
    random cards directly from the remaining deck rather than filtering the
    full range per-sample — this is orders of magnitude faster for multiway.
    """
    if rng_key is None:
        rng_key = jax.random.PRNGKey(0)

    n_players = len(hands_or_ranges)
    wins = [0.0] * n_players
    ties = [0.0] * n_players
    total = 0

    cards_to_come = 5 - len(board)
    dead_board = set(board)

    seed = int(jax.random.randint(rng_key, (), 0, 2**31 - 1).item())
    rng = np.random.RandomState(seed)

    # Classify each player as fixed hand, uniform range, or weighted range
    player_types: list[str] = []  # "fixed", "uniform", "weighted"
    for hor in hands_or_ranges:
        if isinstance(hor, tuple):
            player_types.append("fixed")
        elif _is_uniform_range(hor):
            player_types.append("uniform")
        else:
            player_types.append("weighted")

    # Pre-build arrays for the first weighted range player
    first_weighted_idx = None
    first_weighted_arrays: tuple[np.ndarray, np.ndarray] | None = None
    first_weighted_pre_indices: np.ndarray | None = None

    for j, ptype in enumerate(player_types):
        if ptype == "weighted":
            pre_dead = set(dead_board)
            all_prior_fixed = True
            for k in range(j):
                if player_types[k] == "fixed":
                    pre_dead |= set(hands_or_ranges[k])
                else:
                    all_prior_fixed = False
                    break
            if all_prior_fixed:
                first_weighted_idx = j
                hands_arr, weights_arr = _prepare_range_arrays(
                    hands_or_ranges[j], pre_dead,
                )
                first_weighted_arrays = (hands_arr, weights_arr)
                if len(hands_arr) > 0:
                    first_weighted_pre_indices = rng.choice(
                        len(hands_arr), size=num_samples, p=weights_arr,
                    )
            break

    for i in range(num_samples):
        dead = set(dead_board)
        concrete_hands: list[PLOHand] = []
        valid = True

        for j, hor in enumerate(hands_or_ranges):
            ptype = player_types[j]

            if ptype == "fixed":
                hand_tuple = hor  # type: ignore
                if any(c in dead for c in hand_tuple):
                    valid = False
                    break
                concrete_hands.append(hand_tuple)
                dead |= set(hand_tuple)

            elif ptype == "uniform":
                # Fast path: deal 4 random cards from remaining deck
                remaining = [c for c in range(52) if c not in dead]
                if len(remaining) < 4:
                    valid = False
                    break
                idxs = rng.choice(len(remaining), size=4, replace=False)
                h = tuple(sorted(remaining[k] for k in idxs))
                concrete_hands.append(h)
                dead |= set(h)

            else:  # weighted
                if (j == first_weighted_idx
                        and first_weighted_arrays is not None
                        and first_weighted_pre_indices is not None):
                    hands_arr, _ = first_weighted_arrays
                    if len(hands_arr) == 0:
                        valid = False
                        break
                    h = tuple(hands_arr[first_weighted_pre_indices[i]])
                else:
                    hands_arr, weights_arr = _prepare_range_arrays(hor, dead)
                    if len(hands_arr) == 0:
                        valid = False
                        break
                    idx = rng.choice(len(hands_arr), p=weights_arr)
                    h = tuple(hands_arr[idx])
                concrete_hands.append(h)
                dead |= set(h)

        if not valid:
            continue

        # Sample runout
        remaining = _remaining_cards(dead)
        if cards_to_come > 0 and len(remaining) < cards_to_come:
            continue

        if cards_to_come > 0:
            r_indices = rng.choice(len(remaining), size=cards_to_come, replace=False)
            runout = tuple(remaining[k] for k in r_indices)
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
