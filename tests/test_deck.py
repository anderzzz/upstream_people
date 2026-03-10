"""Tests for Deck."""

import jax
import pytest

from plo_engine.deck import Deck


class TestDeck:
    def test_fresh_deck_has_52_cards(self):
        deck = Deck.from_seed(42)
        assert deck.remaining() == 52

    def test_deal_reduces_remaining(self):
        deck = Deck.from_seed(42)
        deck.deal(5)
        assert deck.remaining() == 47

    def test_deal_returns_correct_count(self):
        deck = Deck.from_seed(42)
        cards = deck.deal(10)
        assert len(cards) == 10

    def test_all_cards_unique(self):
        deck = Deck.from_seed(42)
        cards = deck.deal(52)
        assert len(set(cards)) == 52

    def test_all_cards_in_range(self):
        deck = Deck.from_seed(42)
        cards = deck.deal(52)
        assert all(0 <= c <= 51 for c in cards)

    def test_deal_raises_when_exhausted(self):
        deck = Deck.from_seed(42)
        deck.deal(50)
        with pytest.raises(ValueError):
            deck.deal(5)

    def test_deal_negative_raises(self):
        deck = Deck.from_seed(42)
        with pytest.raises(ValueError):
            deck.deal(-1)

    def test_reproducibility_same_seed(self):
        d1 = Deck.from_seed(123)
        d2 = Deck.from_seed(123)
        assert d1.deal(52) == d2.deal(52)

    def test_different_seeds_differ(self):
        d1 = Deck.from_seed(1)
        d2 = Deck.from_seed(2)
        # Extremely unlikely to be the same
        assert d1.deal(52) != d2.deal(52)

    def test_deal_plo_hand(self):
        deck = Deck.from_seed(42)
        hand = deck.deal_plo_hand()
        assert len(hand) == 4
        # PLOHand is sorted ascending
        assert hand == tuple(sorted(hand))
        assert deck.remaining() == 48

    def test_deal_flop_burns_one(self):
        deck = Deck.from_seed(42)
        # Deal some hands first (like in a real game)
        deck.deal(8)  # 2 players * 4 cards
        flop = deck.deal_flop()
        assert len(flop) == 3
        assert len(deck.burns) == 1
        # 52 - 8 (hands) - 1 (burn) - 3 (flop) = 40
        assert deck.remaining() == 40

    def test_deal_turn_or_river_burns_one(self):
        deck = Deck.from_seed(42)
        deck.deal(8)
        deck.deal_flop()  # 1 burn + 3 cards
        card = deck.deal_turn_or_river()  # 1 burn + 1 card
        assert isinstance(card, int)
        assert 0 <= card <= 51
        assert len(deck.burns) == 2
        # 52 - 8 - 4 - 2 = 38
        assert deck.remaining() == 38

    def test_full_hand_deal(self):
        """Simulate dealing a full 6-player hand."""
        deck = Deck.from_seed(42)
        hands = [deck.deal_plo_hand() for _ in range(6)]
        flop = deck.deal_flop()
        turn = deck.deal_turn_or_river()
        river = deck.deal_turn_or_river()

        # All dealt cards should be unique
        all_cards = []
        for h in hands:
            all_cards.extend(h)
        all_cards.extend(flop)
        all_cards.append(turn)
        all_cards.append(river)
        all_cards.extend(deck.burns)
        assert len(set(all_cards)) == len(all_cards)

    def test_from_jax_key(self):
        key = jax.random.PRNGKey(99)
        deck = Deck(key)
        assert deck.remaining() == 52
        cards = deck.deal(52)
        assert len(set(cards)) == 52
