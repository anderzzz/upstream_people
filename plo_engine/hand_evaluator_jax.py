"""Layer 0: JAX-accelerated batch hand evaluator.

Branchless implementation suitable for jax.jit compilation.
All control flow uses jnp.where instead of Python if/else.
"""
from __future__ import annotations

import jax
import jax.numpy as jnp
from functools import partial

# Pre-computed combination index arrays
HOLE_COMBOS = jnp.array([[0, 1], [0, 2], [0, 3], [1, 2], [1, 3], [2, 3]])  # (6, 2)
BOARD_COMBOS = jnp.array([
    [0, 1, 2], [0, 1, 3], [0, 1, 4], [0, 2, 3], [0, 2, 4],
    [0, 3, 4], [1, 2, 3], [1, 2, 4], [1, 3, 4], [2, 3, 4],
])  # (10, 3)


def _encode_rank_jax(category: jnp.ndarray, k0: jnp.ndarray, k1: jnp.ndarray,
                     k2: jnp.ndarray, k3: jnp.ndarray, k4: jnp.ndarray) -> jnp.ndarray:
    """Encode category + up to 5 kickers into a HandRank integer."""
    return (category << 20) | (k0 << 16) | (k1 << 12) | (k2 << 8) | (k3 << 4) | k4


def _evaluate_single_5card(cards: jnp.ndarray) -> jnp.ndarray:
    """Evaluate a single 5-card hand. cards shape: (5,) of ints 0-51.

    Returns a scalar HandRank int. Fully branchless for JIT compatibility.
    """
    ranks = cards // 4  # (5,)
    suits = cards % 4   # (5,)

    # Sort ranks descending
    sorted_ranks = jnp.sort(ranks)[::-1]  # (5,) descending

    # Rank counts using a 13-element histogram
    rank_counts = jnp.zeros(13, dtype=jnp.int32)
    rank_counts = rank_counts.at[ranks].add(1)

    # Max count and second max count
    sorted_counts = jnp.sort(rank_counts)[::-1]
    max_count = sorted_counts[0]
    second_count = sorted_counts[1]

    # Flush: all suits the same
    is_flush = jnp.all(suits == suits[0])

    # Straight detection
    unique_sorted = sorted_ranks
    r0, r1, r2, r3, r4 = unique_sorted[0], unique_sorted[1], unique_sorted[2], unique_sorted[3], unique_sorted[4]
    all_unique = (jnp.max(rank_counts) == 1)

    # Normal straight: 5 consecutive ranks
    is_normal_straight = all_unique & (r0 - r4 == 4)
    # Wheel: A-2-3-4-5 => sorted desc: 12, 3, 2, 1, 0
    is_wheel = all_unique & (r0 == 12) & (r1 == 3) & (r2 == 2) & (r3 == 1) & (r4 == 0)
    is_straight = is_normal_straight | is_wheel

    straight_high = jnp.where(is_wheel, jnp.int32(3), r0)

    # Get ranks sorted by (count desc, rank desc) for classification
    # For each rank, build a sort key: count * 16 + rank, then sort descending
    rank_keys = rank_counts * 16 + jnp.arange(13)
    sorted_indices = jnp.argsort(rank_keys)[::-1]  # highest key first

    # Extract the top 5 distinct-rank entries (enough for any hand)
    sr0 = sorted_indices[0]
    sr1 = sorted_indices[1]
    sr2 = sorted_indices[2]
    sr3 = sorted_indices[3]
    sr4 = sorted_indices[4]
    sc0 = rank_counts[sr0]

    # Straight flush
    sf_rank = _encode_rank_jax(jnp.int32(8), straight_high,
                               jnp.int32(0), jnp.int32(0), jnp.int32(0), jnp.int32(0))

    # Four of a kind: max_count == 4
    foak_rank = _encode_rank_jax(jnp.int32(7), sr0, sr1,
                                 jnp.int32(0), jnp.int32(0), jnp.int32(0))

    # Full house: max_count == 3, second_count == 2
    fh_rank = _encode_rank_jax(jnp.int32(6), sr0, sr1,
                               jnp.int32(0), jnp.int32(0), jnp.int32(0))

    # Flush
    fl_rank = _encode_rank_jax(jnp.int32(5), sorted_ranks[0], sorted_ranks[1],
                               sorted_ranks[2], sorted_ranks[3], sorted_ranks[4])

    # Straight
    st_rank = _encode_rank_jax(jnp.int32(4), straight_high,
                               jnp.int32(0), jnp.int32(0), jnp.int32(0), jnp.int32(0))

    # Three of a kind: max_count == 3, second_count == 1
    tok_rank = _encode_rank_jax(jnp.int32(3), sr0, sr1, sr2,
                                jnp.int32(0), jnp.int32(0))

    # Two pair: max_count == 2, second_count == 2
    tp_rank = _encode_rank_jax(jnp.int32(2), sr0, sr1, sr2,
                               jnp.int32(0), jnp.int32(0))

    # One pair: max_count == 2, second_count == 1
    op_rank = _encode_rank_jax(jnp.int32(1), sr0, sr1, sr2, sr3,
                               jnp.int32(0))

    # High card
    hc_rank = _encode_rank_jax(jnp.int32(0), sorted_ranks[0], sorted_ranks[1],
                               sorted_ranks[2], sorted_ranks[3], sorted_ranks[4])

    # Select the correct rank using cascading jnp.where
    # Priority order (check most specific first):
    result = hc_rank
    result = jnp.where((max_count == 2) & (second_count == 1), op_rank, result)
    result = jnp.where((max_count == 2) & (second_count == 2), tp_rank, result)
    result = jnp.where((max_count == 3) & (second_count == 1), tok_rank, result)
    result = jnp.where(is_straight & ~is_flush, st_rank, result)
    result = jnp.where(is_flush & ~is_straight, fl_rank, result)
    result = jnp.where((max_count == 3) & (second_count == 2), fh_rank, result)
    result = jnp.where(max_count == 4, foak_rank, result)
    result = jnp.where(is_straight & is_flush, sf_rank, result)

    return result


# Vectorized version: evaluate a batch of 5-card hands
_evaluate_single_jit = jax.jit(_evaluate_single_5card)


@jax.jit
def evaluate_5card_jax(cards: jnp.ndarray) -> jnp.ndarray:
    """Evaluate a batch of 5-card hands.

    Args:
        cards: int array of shape (batch, 5), each entry a card int 0-51

    Returns:
        int array of shape (batch,), each entry a HandRank
    """
    return jax.vmap(_evaluate_single_5card)(cards)


@jax.jit
def evaluate_5card_single_jax(cards: jnp.ndarray) -> jnp.ndarray:
    """Evaluate a single 5-card hand (shape (5,))."""
    return _evaluate_single_5card(cards)


@jax.jit
def best_plo_hand_jax(hole: jnp.ndarray, board: jnp.ndarray) -> jnp.ndarray:
    """Evaluate best PLO hand for a batch of (hole, board) pairs.

    Args:
        hole: int array of shape (batch, 4)
        board: int array of shape (batch, 5)

    Returns:
        int array of shape (batch,) with best HandRank per entry
    """
    def _single_best(hole_single, board_single):
        # Gather the 6 hole pairs and 10 board triples
        hole_pairs = hole_single[HOLE_COMBOS]     # (6, 2)
        board_triples = board_single[BOARD_COMBOS]  # (10, 3)

        # All 60 combinations: (6, 10, 5)
        # Expand and concatenate
        hp = jnp.repeat(hole_pairs[:, None, :], 10, axis=1)   # (6, 10, 2)
        bt = jnp.repeat(board_triples[None, :, :], 6, axis=0)  # (6, 10, 3)
        all_hands = jnp.concatenate([hp, bt], axis=2)  # (6, 10, 5)
        all_hands = all_hands.reshape(60, 5)  # (60, 5)

        # Evaluate all 60 hands
        ranks = jax.vmap(_evaluate_single_5card)(all_hands)  # (60,)
        return jnp.max(ranks)

    return jax.vmap(_single_best)(hole, board)


@jax.jit
def best_plo_hand_single_jax(hole: jnp.ndarray, board: jnp.ndarray) -> jnp.ndarray:
    """Evaluate best PLO hand for a single (hole, board) pair.

    Args:
        hole: int array of shape (4,)
        board: int array of shape (5,)

    Returns:
        scalar HandRank
    """
    hole_pairs = hole[HOLE_COMBOS]         # (6, 2)
    board_triples = board[BOARD_COMBOS]    # (10, 3)
    hp = jnp.repeat(hole_pairs[:, None, :], 10, axis=1)
    bt = jnp.repeat(board_triples[None, :, :], 6, axis=0)
    all_hands = jnp.concatenate([hp, bt], axis=2).reshape(60, 5)
    ranks = jax.vmap(_evaluate_single_5card)(all_hands)
    return jnp.max(ranks)
