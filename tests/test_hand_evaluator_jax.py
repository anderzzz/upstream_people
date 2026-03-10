"""Tests for JAX-accelerated hand evaluator.

Verifies that JAX evaluator produces identical results to the pure Python reference.
"""
import pytest
import jax.numpy as jnp

from plo_engine.types import parse_cards, parse_plo_hand, parse_board
from plo_engine.hand_evaluator import evaluate_5card, best_plo_hand, category_of
from plo_engine.hand_evaluator_jax import (
    evaluate_5card_jax,
    evaluate_5card_single_jax,
    best_plo_hand_jax,
    best_plo_hand_single_jax,
)


def parse(s: str) -> tuple[int, ...]:
    return parse_cards(s)


class TestJaxMatchesPython:
    """Verify JAX evaluator matches pure Python on known hands."""

    HANDS_5CARD = [
        "Ah Kh Qh Jh Th",   # royal flush
        "5h 4h 3h 2h Ah",   # wheel SF
        "Kh Qh Jh Th 9h",   # K-high SF
        "Ah Ac Ad As Kh",   # quads A + K kicker
        "Ah Ac Ad As Qh",   # quads A + Q kicker
        "3h 3c 3d Ah Ac",   # full house 3s over As
        "2h 2c 2d Kh Kc",   # full house 2s over Ks
        "Ah Th 7h 4h 3h",   # A-high flush
        "Ah Th 7h 4h 2h",   # A-high flush (lower kicker)
        "Ah Kd Qc Js Th",   # A-high straight
        "6d 5c 4h 3s 2d",   # 6-high straight
        "5d 4c 3h 2s Ad",   # wheel
        "Ah Ac Ad 4h 3c",   # trips
        "Ah Ac Kd Kc 3h",   # two pair
        "Ah Ac Kd Qc 3h",   # one pair
        "Ah Kd Qc Jh 9c",   # high card
        "6h 5h 4h 3h 2h",   # 6-high SF
        "2h 2c 2d 2s 3h",   # quads 2s
    ]

    def test_single_hands_match(self):
        for hand_str in self.HANDS_5CARD:
            cards = parse(hand_str)
            py_rank = evaluate_5card(cards)
            jax_rank = int(evaluate_5card_single_jax(jnp.array(cards)).item())
            assert py_rank == jax_rank, f"Mismatch on {hand_str}: py={py_rank}, jax={jax_rank}"

    def test_batch_evaluation(self):
        batch = jnp.array([parse(h) for h in self.HANDS_5CARD])
        jax_ranks = evaluate_5card_jax(batch)
        for i, hand_str in enumerate(self.HANDS_5CARD):
            py_rank = evaluate_5card(parse(hand_str))
            assert py_rank == int(jax_ranks[i].item()), f"Batch mismatch on {hand_str}"

    def test_ordering_preserved(self):
        """Verify that relative ordering matches Python evaluator."""
        batch = jnp.array([parse(h) for h in self.HANDS_5CARD])
        jax_ranks = evaluate_5card_jax(batch)

        for i in range(len(self.HANDS_5CARD)):
            for j in range(i + 1, len(self.HANDS_5CARD)):
                py_i = evaluate_5card(parse(self.HANDS_5CARD[i]))
                py_j = evaluate_5card(parse(self.HANDS_5CARD[j]))
                jax_i = int(jax_ranks[i].item())
                jax_j = int(jax_ranks[j].item())
                if py_i > py_j:
                    assert jax_i > jax_j, f"{self.HANDS_5CARD[i]} > {self.HANDS_5CARD[j]} in Python but not JAX"
                elif py_i < py_j:
                    assert jax_i < jax_j, f"{self.HANDS_5CARD[i]} < {self.HANDS_5CARD[j]} in Python but not JAX"
                else:
                    assert jax_i == jax_j, f"{self.HANDS_5CARD[i]} == {self.HANDS_5CARD[j]} in Python but not JAX"


class TestJaxPLOHand:
    """Test PLO best-hand extraction with JAX."""

    def test_basic_plo(self):
        hole = jnp.array(sorted(parse("Ah Kh Qh Jh")))
        board = jnp.array(sorted(parse("Th 9h 8h 2c 3d")))
        jax_rank = int(best_plo_hand_single_jax(hole, board).item())

        py_rank = best_plo_hand(parse_plo_hand("Ah Kh Qh Jh"), parse_board("Th 9h 8h 2c 3d"))
        assert jax_rank == py_rank

    def test_cannot_play_board(self):
        hole = jnp.array(sorted(parse("2c 3d 7s 8c")))
        board = jnp.array(sorted(parse("Ts Jh Qd Ks Ad")))
        jax_rank = int(best_plo_hand_single_jax(hole, board).item())

        py_rank = best_plo_hand(parse_plo_hand("2c 3d 7s 8c"), parse_board("Ts Jh Qd Ks Ad"))
        assert jax_rank == py_rank

    def test_batch_plo(self):
        holes_str = ["Ah Kh Qh Jh", "2c 3d 7s 8c", "Ah Ad Kh 2c"]
        boards_str = ["Th 9h 8h 2c 3d", "Ts Jh Qd Ks Ad", "As 5c 8d Jc Td"]

        holes = jnp.array([sorted(parse(h)) for h in holes_str])
        boards = jnp.array([sorted(parse(b)) for b in boards_str])
        jax_ranks = best_plo_hand_jax(holes, boards)

        for i in range(len(holes_str)):
            py_rank = best_plo_hand(
                parse_plo_hand(holes_str[i]),
                parse_board(boards_str[i]),
            )
            assert py_rank == int(jax_ranks[i].item()), f"Mismatch on hand {i}"


class TestJaxExhaustive:
    """Run JAX evaluator on a large sample and compare to Python."""

    def test_random_sample_1000(self):
        """Generate 1000 random 5-card hands and compare evaluators."""
        import jax.random
        key = jax.random.PRNGKey(42)

        num_samples = 1000
        all_cards = jnp.arange(52)

        mismatches = 0
        for i in range(num_samples):
            key, subkey = jax.random.split(key)
            hand = jax.random.choice(subkey, all_cards, shape=(5,), replace=False)
            hand_sorted = jnp.sort(hand)

            py_rank = evaluate_5card(tuple(int(c) for c in hand_sorted))
            jax_rank = int(evaluate_5card_single_jax(hand_sorted).item())

            if py_rank != jax_rank:
                mismatches += 1

        assert mismatches == 0, f"{mismatches} mismatches out of {num_samples}"
