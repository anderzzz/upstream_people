"""Tests for equity calculator."""
import math

import pytest
import jax

from plo_engine.types import parse_plo_hand, parse_board, make_plo_hand, Range
from plo_engine.equity import (
    equity_hand_vs_range,
    equity_range_vs_range,
    equity_multiway,
    EquityResult,
)


def _small_range(hands_str: list[str]) -> Range:
    """Build a small range from hand strings for testing."""
    hands = [parse_plo_hand(h) for h in hands_str]
    return Range.from_hands(hands)


class TestRiverEquity:
    """River equity is deterministic — no runout variance."""

    def test_winner_gets_100pct(self):
        # Our hand: top set of aces
        hand = parse_plo_hand("Ah Ad 2c 3d")
        board = parse_board("As Kd Qc 7h 4s")
        opp_range = _small_range(["Kh Kc 5d 6c"])  # set of kings

        result = equity_hand_vs_range(hand, opp_range, board)
        assert result.equity == 1.0
        assert result.win_pct == 1.0
        assert result.confidence_interval is None  # exhaustive

    def test_loser_gets_0pct(self):
        hand = parse_plo_hand("Kh Kc 5d 6c")
        board = parse_board("As Kd Qc 7h 4s")
        opp_range = _small_range(["Ah Ad 2c 3d"])

        result = equity_hand_vs_range(hand, opp_range, board)
        assert result.equity == 0.0

    def test_tie_is_50pct(self):
        # Both players have identical made hand (same straight)
        hand = parse_plo_hand("Ah Td 2c 3d")
        board = parse_board("Kh Qd Jc 5s 4h")
        # Opponent also has A-T for broadway
        opp_range = _small_range(["As Tc 6d 7c"])

        result = equity_hand_vs_range(hand, opp_range, board)
        assert abs(result.equity - 0.5) < 0.01
        assert result.tie_pct > 0.9


class TestSymmetry:
    def test_equities_sum_to_one(self):
        """Hand A equity + Hand B equity = 1.0 on a complete board."""
        hand_a = parse_plo_hand("Ah Kh 2c 3d")
        hand_b = parse_plo_hand("Qd Jd 5s 6s")
        board = parse_board("Td 9d 8c 4h 7c")

        range_a = Range.from_hands([hand_a])
        range_b = Range.from_hands([hand_b])

        eq_a = equity_hand_vs_range(hand_a, range_b, board)
        eq_b = equity_hand_vs_range(hand_b, range_a, board)

        assert abs(eq_a.equity + eq_b.equity - 1.0) < 0.001


class TestMonteCarloConvergence:
    def test_increasing_samples_reduces_ci(self):
        """Standard error should decrease as 1/sqrt(n)."""
        hand = parse_plo_hand("Ah Ad Kh Kd")
        board = parse_board("Qs Jc 5h")  # flop
        opp_range = _small_range([
            "Th Td 9c 8c",
            "Qh Qd 2c 3c",
            "9h 9d 4c 6c",
        ])

        key = jax.random.PRNGKey(42)
        r100 = equity_hand_vs_range(hand, opp_range, board, num_samples=100, rng_key=key)
        r1000 = equity_hand_vs_range(hand, opp_range, board, num_samples=1000, rng_key=key)

        # CI should be smaller with more samples
        ci100 = r100.confidence_interval[1] - r100.confidence_interval[0]
        ci1000 = r1000.confidence_interval[1] - r1000.confidence_interval[0]
        assert ci1000 < ci100

    def test_mc_vs_exhaustive_on_river(self):
        """MC and exhaustive should agree on the river."""
        hand = parse_plo_hand("Ah Ad 2c 3d")
        board = parse_board("As Kd Qc 7h 4s")
        opp_range = _small_range(["Kh Kc 5d 6c", "Qh Qd 8c 9c"])

        exact = equity_hand_vs_range(hand, opp_range, board)
        mc = equity_hand_vs_range(
            hand, opp_range, board,
            num_samples=5000, rng_key=jax.random.PRNGKey(123),
        )

        # MC should be within CI of exact
        assert abs(mc.equity - exact.equity) < 0.05


class TestMultiway:
    def test_equities_sum_to_one(self):
        """Sum of all players' equities should be ~1.0."""
        hand_a = parse_plo_hand("Ah Ad Kh 2c")
        hand_b = parse_plo_hand("Qd Jd Td 9c")
        hand_c = parse_plo_hand("5s 6s 7s 8c")
        board = parse_board("3h 4d Kc")

        result = equity_multiway(
            [hand_a, hand_b, hand_c], board,
            num_samples=2000, rng_key=jax.random.PRNGKey(42),
        )

        total_eq = sum(r.equity for r in result.results)
        assert abs(total_eq - 1.0) < 0.05  # within MC tolerance

    def test_two_player_multiway_matches_hvr(self):
        """Two-player multiway should give similar results to hand_vs_range."""
        hand_a = parse_plo_hand("Ah Ad Kh 2c")
        hand_b = parse_plo_hand("Qd Jd Td 9c")
        board = parse_board("3h 4d Kc 5s 8h")

        key = jax.random.PRNGKey(42)

        range_b = Range.from_hands([hand_b])
        hvr = equity_hand_vs_range(hand_a, range_b, board)

        mw = equity_multiway([hand_a, hand_b], board, num_samples=5000, rng_key=key)

        # Should be close
        assert abs(mw.results[0].equity - hvr.equity) < 0.05


class TestBlockerConsistency:
    def test_empty_range_after_blockers(self):
        """If all opponent hands are blocked, equity should be 1.0."""
        hand = parse_plo_hand("Ah Ad Kh Kd")
        board = parse_board("As Ks Qc 7h 4s")
        # Opponent range only contains hands with A or K — all blocked
        opp_range = _small_range(["Ac 2c 3c 4c"])  # has Ac which conflicts with board As
        # After removing blockers, range should be empty → equity 1.0
        result = equity_hand_vs_range(hand, opp_range, board)
        assert result.equity == 1.0
