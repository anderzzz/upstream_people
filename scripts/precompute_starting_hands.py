"""Precompute starting hand equity table for all 270,725 PLO hands.

For each hand, computes:
- StartingHandProfile classification
- Equity vs. 1-5 random opponents (Monte Carlo)

Supports checkpointing: saves progress periodically and resumes from
the last checkpoint if interrupted.

Usage:
    PYTHONPATH=. python scripts/precompute_starting_hands.py [--samples N] [--workers N]

Output:
    data/starting_hand_table.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from itertools import combinations
from multiprocessing import Pool, cpu_count
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from plo_engine.types import PLOHand, Range, card_to_str, cards_to_str
from plo_engine.domain import StartingHandProfile
from plo_engine.equity import equity_multiway

import jax
import jax.numpy as jnp


OUTPUT_PATH = PROJECT_ROOT / "data" / "starting_hand_table.json"
CHECKPOINT_PATH = PROJECT_ROOT / "data" / "_checkpoint_starting_hands.json"
CHECKPOINT_INTERVAL = 500  # save every N hands


def hand_key(hand: PLOHand) -> str:
    """Canonical string key for a hand: comma-separated sorted card ints."""
    return ",".join(str(c) for c in hand)


def hand_display(hand: PLOHand) -> str:
    """Human-readable hand string."""
    return cards_to_str(hand)


def compute_hand_entry(args: tuple) -> tuple[str, dict]:
    """Compute profile + equities for a single hand. Designed for multiprocessing."""
    hand, num_samples, max_opponents = args

    # Profile
    profile = StartingHandProfile.classify(hand)

    # Equities vs N opponents
    equities = {}
    full_range = Range.full()
    for n_opp in range(1, max_opponents + 1):
        # Build player list: hero hand + n_opp full ranges
        players: list[PLOHand | Range] = [hand] + [full_range] * n_opp
        rng_key = jax.random.PRNGKey(hash(hand) % (2**31))
        result = equity_multiway(players, board=(), num_samples=num_samples, rng_key=rng_key)
        hero_result = result.results[0]
        equities[str(n_opp)] = {
            "equity": round(hero_result.equity, 4),
            "win": round(hero_result.win_pct, 4),
            "tie": round(hero_result.tie_pct, 4),
            "ci": [round(hero_result.confidence_interval[0], 4),
                   round(hero_result.confidence_interval[1], 4)]
                  if hero_result.confidence_interval else None,
        }

    entry = {
        "hand": hand_display(hand),
        "category": profile.category.name,
        "suit_structure": profile.suit_structure.name,
        "is_connected": profile.is_connected,
        "gap_count": profile.gap_count,
        "has_ace": profile.has_ace,
        "has_suited_ace": profile.has_suited_ace,
        "num_pairs": profile.num_pairs,
        "highest_pair": profile.highest_pair,
        "preflop_equity_estimate": profile.preflop_equity_estimate,
        "equities": equities,
    }

    return hand_key(hand), entry


def load_checkpoint() -> dict:
    """Load checkpoint if it exists."""
    if CHECKPOINT_PATH.exists():
        with open(CHECKPOINT_PATH) as f:
            return json.load(f)
    return {}


def save_checkpoint(data: dict) -> None:
    """Save checkpoint."""
    with open(CHECKPOINT_PATH, "w") as f:
        json.dump(data, f)


def main():
    parser = argparse.ArgumentParser(description="Precompute PLO starting hand table")
    parser.add_argument("--samples", type=int, default=5000,
                        help="MC samples per equity calculation (default: 5000)")
    parser.add_argument("--max-opponents", type=int, default=5,
                        help="Max number of opponents to compute equity against (default: 5)")
    parser.add_argument("--workers", type=int, default=1,
                        help="Number of parallel workers (default: 1, multiprocessing can conflict with JAX)")
    parser.add_argument("--limit", type=int, default=0,
                        help="Limit number of hands to compute (0 = all, useful for testing)")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from checkpoint")
    args = parser.parse_args()

    # Generate all hands
    all_hands: list[PLOHand] = [
        tuple(sorted(combo)) for combo in combinations(range(52), 4)
    ]
    total = len(all_hands)
    print(f"Total PLO hands: {total:,}")

    if args.limit > 0:
        all_hands = all_hands[:args.limit]
        total = len(all_hands)
        print(f"Limited to {total:,} hands")

    # Load checkpoint
    results = load_checkpoint() if args.resume else {}
    done = len(results)
    if done > 0:
        print(f"Resuming from checkpoint: {done:,} hands already computed")

    # Filter out already-done hands
    remaining = [(h, args.samples, args.max_opponents)
                 for h in all_hands if hand_key(h) not in results]
    print(f"Remaining to compute: {len(remaining):,}")

    if not remaining:
        print("All hands already computed!")
    else:
        start_time = time.time()
        completed = 0

        if args.workers > 1:
            # Multiprocessing (may not play well with JAX)
            with Pool(args.workers) as pool:
                for key, entry in pool.imap_unordered(compute_hand_entry, remaining, chunksize=10):
                    results[key] = entry
                    completed += 1
                    if completed % CHECKPOINT_INTERVAL == 0:
                        elapsed = time.time() - start_time
                        rate = completed / elapsed
                        eta = (len(remaining) - completed) / rate if rate > 0 else 0
                        print(f"  {done + completed:,}/{total:,} "
                              f"({(done + completed)/total:.1%}) "
                              f"rate={rate:.1f}/s ETA={eta/3600:.1f}h")
                        save_checkpoint(results)
        else:
            # Single process
            for task_args in remaining:
                key, entry = compute_hand_entry(task_args)
                results[key] = entry
                completed += 1
                if completed % CHECKPOINT_INTERVAL == 0:
                    elapsed = time.time() - start_time
                    rate = completed / elapsed
                    eta = (len(remaining) - completed) / rate if rate > 0 else 0
                    print(f"  {done + completed:,}/{total:,} "
                          f"({(done + completed)/total:.1%}) "
                          f"rate={rate:.1f}/s ETA={eta/3600:.1f}h")
                    save_checkpoint(results)

    # Save final output
    print(f"\nSaving {len(results):,} entries to {OUTPUT_PATH}")
    with open(OUTPUT_PATH, "w") as f:
        json.dump(results, f, separators=(",", ":"))

    # Clean up checkpoint
    if CHECKPOINT_PATH.exists():
        os.remove(CHECKPOINT_PATH)

    file_size = OUTPUT_PATH.stat().st_size / (1024 * 1024)
    print(f"Done! File size: {file_size:.1f} MB")


if __name__ == "__main__":
    main()
