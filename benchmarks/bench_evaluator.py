"""Benchmarks for hand evaluators."""
import time
from itertools import combinations

import jax
import jax.numpy as jnp

from plo_engine.types import parse_cards
from plo_engine.hand_evaluator import evaluate_5card, best_plo_hand
from plo_engine.hand_evaluator_jax import (
    evaluate_5card_jax,
    evaluate_5card_single_jax,
    best_plo_hand_jax,
    best_plo_hand_single_jax,
)


def bench_python_5card(n=10_000):
    """Benchmark pure Python 5-card evaluator."""
    # Generate n random 5-card hands
    hands = []
    import random
    random.seed(42)
    for _ in range(n):
        cards = tuple(sorted(random.sample(range(52), 5)))
        hands.append(cards)

    start = time.perf_counter()
    for h in hands:
        evaluate_5card(h)
    elapsed = time.perf_counter() - start

    rate = n / elapsed
    print(f"Python evaluate_5card: {rate:,.0f} hands/sec ({elapsed:.3f}s for {n:,})")
    return rate


def bench_python_plo(n=1_000):
    """Benchmark pure Python PLO best hand."""
    import random
    random.seed(42)
    pairs = []
    for _ in range(n):
        cards = random.sample(range(52), 9)
        hole = tuple(sorted(cards[:4]))
        board = tuple(sorted(cards[4:]))
        pairs.append((hole, board))

    start = time.perf_counter()
    for hole, board in pairs:
        best_plo_hand(hole, board)
    elapsed = time.perf_counter() - start

    rate = n / elapsed
    print(f"Python best_plo_hand: {rate:,.0f} hands/sec ({elapsed:.3f}s for {n:,})")
    return rate


def bench_jax_5card_batch(n=100_000):
    """Benchmark JAX batch 5-card evaluator."""
    key = jax.random.PRNGKey(42)
    # Generate batch of random 5-card hands
    all_cards = jnp.arange(52)
    hands = []
    for i in range(n):
        key, subkey = jax.random.split(key)
        h = jax.random.choice(subkey, all_cards, shape=(5,), replace=False)
        hands.append(jnp.sort(h))
    batch = jnp.stack(hands)

    # Warmup (JIT compilation)
    _ = evaluate_5card_jax(batch[:10])

    start = time.perf_counter()
    result = evaluate_5card_jax(batch)
    result.block_until_ready()
    elapsed = time.perf_counter() - start

    rate = n / elapsed
    print(f"JAX evaluate_5card (batch {n:,}): {rate:,.0f} hands/sec ({elapsed:.3f}s)")
    return rate


def bench_jax_plo_batch(n=10_000):
    """Benchmark JAX batch PLO evaluator."""
    key = jax.random.PRNGKey(42)
    holes = []
    boards = []
    for i in range(n):
        key, subkey = jax.random.split(key)
        cards = jax.random.choice(subkey, 52, shape=(9,), replace=False)
        holes.append(jnp.sort(cards[:4]))
        boards.append(jnp.sort(cards[4:]))

    hole_batch = jnp.stack(holes)
    board_batch = jnp.stack(boards)

    # Warmup
    _ = best_plo_hand_jax(hole_batch[:10], board_batch[:10])

    start = time.perf_counter()
    result = best_plo_hand_jax(hole_batch, board_batch)
    result.block_until_ready()
    elapsed = time.perf_counter() - start

    rate = n / elapsed
    print(f"JAX best_plo_hand (batch {n:,}): {rate:,.0f} hands/sec ({elapsed:.3f}s)")
    return rate


if __name__ == "__main__":
    print("=" * 60)
    print("Hand Evaluator Benchmarks")
    print("=" * 60)
    print()

    print("--- Pure Python ---")
    bench_python_5card(10_000)
    bench_python_plo(1_000)
    print()

    print("--- JAX (JIT compiled, batched) ---")
    bench_jax_5card_batch(100_000)
    bench_jax_plo_batch(10_000)
