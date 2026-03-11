"""Tests for the heuristic player and opponent model."""

import pytest

from plo_engine.player import RandomPlayer
from plo_engine.players.heuristic_player import HeuristicPlayer
from plo_engine.opponent_model import OpponentModel, OpponentStats
from plo_engine.tournament import Session, SessionConfig, SessionMode
from plo_engine.table import BlindLevel, BlindStructure
from plo_engine.betting import Action, ActionType


# ---------------------------------------------------------------------------
# Opponent Model tests
# ---------------------------------------------------------------------------

class TestOpponentStats:
    def test_defaults_with_no_data(self):
        stats = OpponentStats()
        assert stats.vpip == 0.5
        assert stats.pfr == 0.2
        assert stats.aggression_factor == 1.5
        assert stats.fold_to_bet == 0.4
        assert stats.cbet == 0.5

    def test_vpip_calculation(self):
        stats = OpponentStats(vpip_count=3, vpip_opportunities=10)
        assert stats.vpip == 0.3

    def test_aggression_factor(self):
        stats = OpponentStats(aggression_bets=6, aggression_passive=3)
        assert stats.aggression_factor == 2.0


class TestOpponentModel:
    def test_new_hand_increments_observed(self):
        model = OpponentModel()
        model._ensure_seat(0)
        model.new_hand()
        assert model.get_stats(0).hands_observed == 1
        model.new_hand()
        assert model.get_stats(0).hands_observed == 2

    def test_preflop_raise_tracked(self):
        model = OpponentModel()
        model.new_hand()
        action = Action(ActionType.RAISE, player_seat=1, amount=30)
        model.observe_action(1, action, board_len=0)
        stats = model.get_stats(1)
        assert stats.vpip_count == 1
        assert stats.pfr_count == 1

    def test_preflop_call_is_vpip_not_pfr(self):
        model = OpponentModel()
        model.new_hand()
        action = Action(ActionType.CALL, player_seat=1, amount=10)
        model.observe_action(1, action, board_len=0)
        stats = model.get_stats(1)
        assert stats.vpip_count == 1
        assert stats.pfr_count == 0

    def test_fold_tracked(self):
        model = OpponentModel()
        model.new_hand()
        # First action (not a fold to bet, just first act)
        call = Action(ActionType.CALL, player_seat=1, amount=10)
        model.observe_action(1, call, board_len=0)
        # Second preflop action facing a raise
        fold = Action(ActionType.FOLD, player_seat=1)
        model.observe_action(1, fold, board_len=0)
        stats = model.get_stats(1)
        assert stats.fold_to_bet_count == 1


# ---------------------------------------------------------------------------
# Heuristic Player tests
# ---------------------------------------------------------------------------

class TestHeuristicPlayer:
    def _run_session(self, style: str, num_hands: int = 20) -> list:
        hero = HeuristicPlayer(f"{style}-Bot", style=style, seed=42)
        villain = RandomPlayer("Random", seed=43)
        config = SessionConfig(
            mode=SessionMode.CASH_GAME,
            num_seats=2,
            starting_stack=1000,
            blind_structure=BlindStructure(levels=[BlindLevel(5, 10, 0)]),
            num_hands=num_hands,
            master_seed=42,
        )
        session = Session(config, [hero, villain])
        return session.run()

    def test_tag_plays_without_error(self):
        histories = self._run_session("TAG")
        assert len(histories) == 20

    def test_lag_plays_without_error(self):
        histories = self._run_session("LAG")
        assert len(histories) >= 1  # may end early if a player busts

    def test_nit_plays_without_error(self):
        histories = self._run_session("NIT")
        assert len(histories) == 20

    def test_chip_conservation(self):
        hero = HeuristicPlayer("Hero", style="TAG", seed=42)
        villain = HeuristicPlayer("Villain", style="LAG", seed=43)
        config = SessionConfig(
            mode=SessionMode.CASH_GAME,
            num_seats=2,
            starting_stack=1000,
            blind_structure=BlindStructure(levels=[BlindLevel(5, 10, 0)]),
            num_hands=50,
            master_seed=100,
        )
        session = Session(config, [hero, villain])
        session.run()
        standings = session.standings()
        total = sum(s for _, s in standings)
        assert abs(total - 2000) < 0.01, f"Chip leak! Total: {total}"

    def test_three_player_session(self):
        players = [
            HeuristicPlayer("TAG", style="TAG", seed=1),
            HeuristicPlayer("LAG", style="LAG", seed=2),
            HeuristicPlayer("NIT", style="NIT", seed=3),
        ]
        config = SessionConfig(
            mode=SessionMode.CASH_GAME,
            num_seats=3,
            starting_stack=1000,
            blind_structure=BlindStructure(levels=[BlindLevel(5, 10, 0)]),
            num_hands=30,
            master_seed=42,
        )
        session = Session(config, players)
        histories = session.run()
        assert len(histories) == 30
        total = sum(s for _, s in session.standings())
        assert abs(total - 3000) < 0.01

    def test_heuristic_vs_random_multihand(self):
        """Heuristic player should generally beat random over many hands."""
        hero = HeuristicPlayer("Heuristic", style="TAG", seed=42)
        villain = RandomPlayer("Random", seed=43)
        config = SessionConfig(
            mode=SessionMode.CASH_GAME,
            num_seats=2,
            starting_stack=1000,
            blind_structure=BlindStructure(levels=[BlindLevel(5, 10, 0)]),
            num_hands=100,
            master_seed=42,
        )
        session = Session(config, [hero, villain])
        session.run()
        # Just verify it runs; we don't enforce that heuristic always wins
        # due to variance, but it shouldn't crash
        standings = session.standings()
        assert len(standings) == 2
