"""Tests for the hand state machine and full hand execution."""

import pytest

from plo_engine.deck import Deck
from plo_engine.table import Table, BlindStructure, BlindLevel
from plo_engine.player import RandomPlayer, CallingStation
from plo_engine.hand_state import HandState, run_hand


def make_table(num_players=3, stack=1000.0, sb=5.0, bb=10.0):
    """Helper to create a table with players seated."""
    blinds = BlindStructure(levels=[BlindLevel(sb, bb)])
    table = Table(max(num_players, 2), blinds)
    for i in range(num_players):
        table.seat_player(i, RandomPlayer(f"Player{i}", seed=i * 100), stack)
    return table


class TestHandStateBasics:
    def test_create_hand_state(self):
        table = make_table(3)
        deck = Deck.from_seed(42)
        state = HandState(table, deck)
        assert len(state.players) == 3
        assert state.phase.name == "POST_BLINDS"

    def test_active_players(self):
        table = make_table(3)
        deck = Deck.from_seed(42)
        state = HandState(table, deck)
        assert len(state.active_players()) == 3

    def test_remaining_players(self):
        table = make_table(3)
        deck = Deck.from_seed(42)
        state = HandState(table, deck)
        state.players[0].is_folded = True
        assert len(state.remaining_players()) == 2

    def test_is_hand_over(self):
        table = make_table(3)
        deck = Deck.from_seed(42)
        state = HandState(table, deck)
        state.players[0].is_folded = True
        state.players[1].is_folded = True
        assert state.is_hand_over()


class TestRunHand:
    def test_run_hand_completes(self):
        """A hand with random players should complete without errors."""
        table = make_table(3, stack=1000.0)
        deck = Deck.from_seed(42)
        result = run_hand(table, deck)
        assert result is not None
        assert result.hand_number == 0

    def test_chip_conservation_single_hand(self):
        """Total chips must be preserved after a hand."""
        table = make_table(4, stack=500.0)
        total_before = sum(s.stack for s in table.seats if s.is_active)
        deck = Deck.from_seed(42)
        run_hand(table, deck)
        total_after = sum(s.stack for s in table.seats if s.is_occupied)
        assert abs(total_after - total_before) < 0.01

    def test_chip_conservation_many_hands(self):
        """Run many hands and verify chips are always conserved."""
        table = make_table(4, stack=500.0)
        total_chips = sum(s.stack for s in table.seats if s.is_active)

        for seed in range(50):
            active = table.active_seats()
            if len(active) < 2:
                break
            table.advance_button()
            deck = Deck.from_seed(seed)
            run_hand(table, deck)
            current_total = sum(
                table.seats[i].stack for i in range(table.num_seats)
                if table.seats[i].is_occupied
            )
            assert abs(current_total - total_chips) < 0.01, (
                f"Chip conservation violated at hand {seed}: "
                f"expected {total_chips}, got {current_total}"
            )

    def test_heads_up(self):
        """Heads-up hand should complete."""
        table = make_table(2, stack=500.0)
        deck = Deck.from_seed(42)
        result = run_hand(table, deck)
        assert result is not None

    def test_calling_stations(self):
        """A hand where everyone calls should reach showdown."""
        blinds = BlindStructure(levels=[BlindLevel(5.0, 10.0)])
        table = Table(3, blinds)
        for i in range(3):
            table.seat_player(i, CallingStation(f"Station{i}"), 500.0)

        deck = Deck.from_seed(42)
        result = run_hand(table, deck)
        assert result.went_to_showdown

    def test_result_has_net_profit(self):
        table = make_table(3)
        deck = Deck.from_seed(42)
        result = run_hand(table, deck)
        assert len(result.net_profit) > 0
        # Net profits should sum to zero
        assert abs(sum(result.net_profit.values())) < 0.01

    def test_all_players_get_cards(self):
        """All players should be dealt hole cards."""
        table = make_table(4)
        deck = Deck.from_seed(42)
        result = run_hand(table, deck)
        hole_cards = getattr(result, "_hole_cards", {})
        assert len(hole_cards) == 4
        for hand in hole_cards.values():
            assert len(hand) == 4

    def test_short_stack_all_in(self):
        """A very short-stacked player should be able to go all-in."""
        blinds = BlindStructure(levels=[BlindLevel(5.0, 10.0)])
        table = Table(3, blinds)
        table.seat_player(0, CallingStation("Short"), 15.0)  # barely above BB
        table.seat_player(1, CallingStation("Normal1"), 500.0)
        table.seat_player(2, CallingStation("Normal2"), 500.0)

        deck = Deck.from_seed(42)
        result = run_hand(table, deck)

        # Hand should complete
        assert result is not None
        total = sum(table.seats[i].stack for i in range(3))
        assert abs(total - 1015.0) < 0.01


class TestRunHandManySeeds:
    """Stress tests across many seeds to catch edge cases."""

    @pytest.mark.parametrize("num_players", [2, 3, 4, 6])
    def test_many_seeds(self, num_players):
        """Run 20 hands with different seeds per player count."""
        table = make_table(num_players, stack=500.0)
        total_chips = num_players * 500.0

        for seed in range(20):
            active = table.active_seats()
            if len(active) < 2:
                break
            table.advance_button()
            deck = Deck.from_seed(seed * 7 + 3)
            run_hand(table, deck)
            current = sum(
                table.seats[i].stack for i in range(table.num_seats)
                if table.seats[i].is_occupied
            )
            assert abs(current - total_chips) < 0.01
