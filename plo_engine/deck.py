"""Deck: shuffle, deal, reset. Uses JAX PRNG for reproducible shuffles."""

from __future__ import annotations

import jax
import jax.numpy as jnp

from plo_engine.types import PLOHand, Board, make_plo_hand, make_board


class Deck:
    """
    A shuffleable, dealable 52-card deck.

    Uses JAX PRNG for reproducible shuffles. Each Deck instance
    tracks its current position (how many cards have been dealt).
    Cards are never replaced — dealing is strictly sequential
    from the shuffled order.
    """

    def __init__(self, rng_key: jax.Array):
        """Create and shuffle a fresh deck."""
        cards = jnp.arange(52)
        shuffled = jax.random.permutation(rng_key, cards)
        self._cards: tuple[int, ...] = tuple(int(c) for c in shuffled)
        self._position: int = 0
        self._burns: list[int] = []

    def deal(self, n: int) -> tuple[int, ...]:
        """
        Deal n cards from the top of the deck.
        Advances the internal position.
        Raises if fewer than n cards remain.
        """
        if n < 0:
            raise ValueError(f"Cannot deal negative cards: {n}")
        if self._position + n > 52:
            raise ValueError(
                f"Cannot deal {n} cards, only {self.remaining()} remain"
            )
        cards = self._cards[self._position : self._position + n]
        self._position += n
        return cards

    def deal_plo_hand(self) -> PLOHand:
        """Convenience: deal 4 cards, return as sorted PLOHand tuple."""
        cards = self.deal(4)
        return make_plo_hand(*cards)

    def deal_flop(self) -> Board:
        """Deal 3 cards (burn 1 first, per standard rules)."""
        burn = self.deal(1)
        self._burns.append(burn[0])
        cards = self.deal(3)
        return make_board(*cards)

    def deal_turn_or_river(self) -> int:
        """Deal 1 card (burn 1 first)."""
        burn = self.deal(1)
        self._burns.append(burn[0])
        return self.deal(1)[0]

    def remaining(self) -> int:
        """Number of undealt cards."""
        return 52 - self._position

    @property
    def burns(self) -> list[int]:
        """Burned cards in deal order."""
        return list(self._burns)

    @property
    def seed_cards(self) -> tuple[int, ...]:
        """Full shuffled card order (for hand history reproducibility)."""
        return self._cards

    @classmethod
    def from_seed(cls, seed: int) -> Deck:
        """Create a deck from an integer seed for convenience."""
        return cls(jax.random.PRNGKey(seed))
