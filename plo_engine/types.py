"""Core data types for the PLO engine.

Card representation: integers 0-51.
    card = rank * 4 + suit
    rank: 0=2, 1=3, ..., 8=T, 9=J, 10=Q, 11=K, 12=A
    suit: 0=clubs, 1=diamonds, 2=hearts, 3=spades
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import ClassVar, Callable

import jax
import jax.numpy as jnp

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

PLOHand = tuple[int, int, int, int]
Board = tuple[int, ...]
FiveCardHand = tuple[int, int, int, int, int]
HandRank = int

# ---------------------------------------------------------------------------
# Card class (thin wrapper for human interaction)
# ---------------------------------------------------------------------------

RANK_NAMES: str = "23456789TJQKA"
SUIT_NAMES: str = "cdhs"


@dataclass(frozen=True, slots=True)
class Card:
    """Thin wrapper for display and parsing. Internal computation uses raw ints."""

    id: int  # 0-51

    RANK_NAMES: ClassVar[str] = RANK_NAMES
    SUIT_NAMES: ClassVar[str] = SUIT_NAMES

    def __post_init__(self):
        if not 0 <= self.id <= 51:
            raise ValueError(f"Card id must be 0-51, got {self.id}")

    @property
    def rank(self) -> int:
        return self.id // 4

    @property
    def suit(self) -> int:
        return self.id % 4

    def __str__(self) -> str:
        return f"{self.RANK_NAMES[self.rank]}{self.SUIT_NAMES[self.suit]}"

    def __repr__(self) -> str:
        return f"Card({str(self)})"

    @classmethod
    def from_str(cls, s: str) -> Card:
        """Parse 'Ah', 'Tc', '2d' etc."""
        if len(s) != 2:
            raise ValueError(f"Card string must be 2 characters, got '{s}'")
        rank = cls.RANK_NAMES.index(s[0].upper())
        suit = cls.SUIT_NAMES.index(s[1].lower())
        return cls(rank * 4 + suit)


# ---------------------------------------------------------------------------
# Utility functions (operate on raw ints)
# ---------------------------------------------------------------------------


def card_to_str(card: int) -> str:
    """Convert card int to human-readable string like 'Ah'."""
    return f"{RANK_NAMES[card // 4]}{SUIT_NAMES[card % 4]}"


def cards_to_str(cards: tuple[int, ...] | list[int]) -> str:
    """Convert multiple cards to string like 'Ah Kd Tc 2s'."""
    return " ".join(card_to_str(c) for c in cards)


def parse_card(s: str) -> int:
    """Parse a single card string like 'Ah' to int."""
    s = s.strip()
    if len(s) != 2:
        raise ValueError(f"Card string must be 2 characters, got '{s}'")
    rank = RANK_NAMES.index(s[0].upper())
    suit = SUIT_NAMES.index(s[1].lower())
    return rank * 4 + suit


def parse_cards(s: str) -> tuple[int, ...]:
    """Parse 'Ah Kd Tc 2s' into tuple of card ints. Also accepts 'AhKdTc2s'."""
    s = s.strip()
    if not s:
        return ()
    # Try space-separated first
    if " " in s:
        return tuple(parse_card(tok) for tok in s.split())
    # Otherwise try consecutive 2-char tokens
    if len(s) % 2 != 0:
        raise ValueError(f"Cannot parse card string: '{s}'")
    return tuple(parse_card(s[i : i + 2]) for i in range(0, len(s), 2))


def make_plo_hand(*cards: int) -> PLOHand:
    """Create a sorted PLOHand tuple from 4 card ints."""
    if len(cards) != 4:
        raise ValueError(f"PLO hand must have exactly 4 cards, got {len(cards)}")
    if len(set(cards)) != 4:
        raise ValueError("PLO hand must have 4 distinct cards")
    for c in cards:
        if not 0 <= c <= 51:
            raise ValueError(f"Card must be 0-51, got {c}")
    return tuple(sorted(cards))  # type: ignore


def make_board(*cards: int) -> Board:
    """Create a sorted Board tuple from 0-5 card ints."""
    if len(cards) > 5:
        raise ValueError(f"Board can have at most 5 cards, got {len(cards)}")
    if len(set(cards)) != len(cards):
        raise ValueError("Board must have distinct cards")
    for c in cards:
        if not 0 <= c <= 51:
            raise ValueError(f"Card must be 0-51, got {c}")
    return tuple(sorted(cards))  # type: ignore


def parse_plo_hand(s: str) -> PLOHand:
    """Parse 'Ah Kd Tc 2s' into a PLOHand (sorted 4-tuple)."""
    cards = parse_cards(s)
    return make_plo_hand(*cards)


def parse_board(s: str) -> Board:
    """Parse 'Ah Kd Tc' into a Board (sorted tuple, 0-5 cards)."""
    if not s.strip():
        return ()
    cards = parse_cards(s)
    return make_board(*cards)


# ---------------------------------------------------------------------------
# Range
# ---------------------------------------------------------------------------


def _all_plo_hands() -> list[PLOHand]:
    """Generate all C(52,4) = 270,725 possible PLO hands."""
    return [tuple(sorted(combo)) for combo in combinations(range(52), 4)]


class Range:
    """A range of PLO starting hands with weights.

    Internally stored as a dict mapping hand tuples to weights in [0, 1].
    Hands are stored as sorted 4-tuples of card ints.
    """

    __slots__ = ("hands",)

    def __init__(self, hands: dict[PLOHand, float]):
        self.hands = hands

    def remove_blockers(self, dead_cards: set[int]) -> Range:
        """Return new Range excluding hands containing any dead card."""
        return Range(
            {
                hand: weight
                for hand, weight in self.hands.items()
                if not any(c in dead_cards for c in hand)
            }
        )

    def normalize(self) -> Range:
        """Scale weights to sum to 1.0 (probability distribution)."""
        total = sum(self.hands.values())
        if total == 0:
            return self
        return Range({h: w / total for h, w in self.hands.items()})

    def num_combos(self) -> float:
        """Sum of weights (effective number of combos in range)."""
        return sum(self.hands.values())

    def filter(self, predicate: Callable[[PLOHand, float], bool]) -> Range:
        """Keep only hands satisfying predicate(hand, weight)."""
        return Range({h: w for h, w in self.hands.items() if predicate(h, w)})

    def sample_hand(self, key: jax.Array, dead_cards: set[int]) -> PLOHand:
        """Sample a single hand from the range, weighted, excluding dead cards."""
        filtered = self.remove_blockers(dead_cards)
        if not filtered.hands:
            raise ValueError("No valid hands in range after removing blockers")
        hands_list = list(filtered.hands.keys())
        weights = jnp.array([filtered.hands[h] for h in hands_list])
        weights = weights / weights.sum()
        idx = int(jax.random.choice(key, len(hands_list), p=weights).item())
        return hands_list[idx]

    def __len__(self) -> int:
        return len(self.hands)

    def __contains__(self, hand: PLOHand) -> bool:
        return hand in self.hands

    def __repr__(self) -> str:
        return f"Range({len(self.hands)} hands, {self.num_combos():.0f} combos)"

    # --- Construction class methods ---

    @classmethod
    def full(cls) -> Range:
        """All 270,725 PLO hands with weight 1.0."""
        return cls({hand: 1.0 for hand in _all_plo_hands()})

    @classmethod
    def from_hands(cls, hands: list[PLOHand], weight: float = 1.0) -> Range:
        """Construct range from explicit hand list."""
        return cls({tuple(sorted(h)): weight for h in hands})

    @classmethod
    def from_filter(cls, predicate: Callable[[PLOHand], bool]) -> Range:
        """Construct range by filtering all possible hands."""
        return cls(
            {hand: 1.0 for hand in _all_plo_hands() if predicate(hand)}
        )
