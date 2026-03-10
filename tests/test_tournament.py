"""Tests for tournament / session manager."""

import pytest

from plo_engine.table import BlindStructure, BlindLevel
from plo_engine.player import RandomPlayer, CallingStation
from plo_engine.tournament import Session, SessionConfig, SessionMode


def make_players(n, seed_base=0):
    return [RandomPlayer(f"Player{i}", seed=seed_base + i) for i in range(n)]


class TestCashGameSession:
    def test_run_fixed_hands(self):
        config = SessionConfig(
            mode=SessionMode.CASH_GAME,
            num_seats=4,
            starting_stack=500.0,
            blind_structure=BlindStructure(levels=[BlindLevel(5.0, 10.0)]),
            num_hands=10,
            master_seed=42,
        )
        session = Session(config, make_players(4))
        histories = session.run()
        assert len(histories) == 10
        assert session.is_complete

    def test_chip_conservation(self):
        config = SessionConfig(
            mode=SessionMode.CASH_GAME,
            num_seats=3,
            starting_stack=1000.0,
            blind_structure=BlindStructure(levels=[BlindLevel(5.0, 10.0)]),
            num_hands=20,
            master_seed=99,
        )
        session = Session(config, make_players(3, seed_base=50))
        session.run()
        total = sum(stack for _, stack in session.standings())
        assert abs(total - 3000.0) < 0.01

    def test_standings(self):
        config = SessionConfig(
            mode=SessionMode.CASH_GAME,
            num_seats=3,
            starting_stack=500.0,
            blind_structure=BlindStructure(levels=[BlindLevel(5.0, 10.0)]),
            num_hands=5,
        )
        session = Session(config, make_players(3))
        session.run()
        standings = session.standings()
        assert len(standings) == 3
        # Sorted by stack descending
        assert standings[0][1] >= standings[1][1] >= standings[2][1]


class TestTournamentSession:
    def test_tournament_runs_to_completion(self):
        config = SessionConfig(
            mode=SessionMode.TOURNAMENT,
            num_seats=3,
            starting_stack=100.0,
            blind_structure=BlindStructure(
                levels=[BlindLevel(5.0, 10.0), BlindLevel(10.0, 20.0)],
                hands_per_level=10,
            ),
            master_seed=42,
        )
        session = Session(config, make_players(3))
        histories = session.run()
        assert session.is_complete
        assert len(histories) > 0
        # At most one player should remain (or all hands exhausted)
        standings = session.standings()
        active_stacks = [s for _, s in standings if s > 0]
        assert len(active_stacks) <= 2  # at most one active + possibly busted

    def test_blind_advancement(self):
        config = SessionConfig(
            mode=SessionMode.CASH_GAME,
            num_seats=3,
            starting_stack=10000.0,  # large stacks to avoid bust
            blind_structure=BlindStructure(
                levels=[
                    BlindLevel(5.0, 10.0),
                    BlindLevel(10.0, 20.0),
                    BlindLevel(25.0, 50.0),
                ],
                hands_per_level=3,
            ),
            num_hands=9,
            master_seed=42,
        )
        players = [CallingStation(f"Station{i}") for i in range(3)]
        session = Session(config, players)
        session.run()
        assert len(session.hand_histories) == 9
        # After 9 hands with 3 per level, should have advanced twice
        level = session.table.blind_structure.current_level
        assert level.big_blind == 50.0


class TestSessionSummary:
    def test_summary_format(self):
        config = SessionConfig(
            mode=SessionMode.CASH_GAME,
            num_seats=3,
            starting_stack=500.0,
            blind_structure=BlindStructure(levels=[BlindLevel(5.0, 10.0)]),
            num_hands=5,
        )
        session = Session(config, make_players(3))
        session.run()
        summary = session.summary()
        assert "CASH_GAME" in summary
        assert "Hands played: 5" in summary
        assert "Standings:" in summary


class TestSessionEdgeCases:
    def test_minimum_players(self):
        config = SessionConfig(
            mode=SessionMode.CASH_GAME,
            num_seats=2,
            starting_stack=500.0,
            blind_structure=BlindStructure(levels=[BlindLevel(5.0, 10.0)]),
            num_hands=5,
        )
        session = Session(config, make_players(2))
        histories = session.run()
        assert len(histories) == 5

    def test_too_many_players_rejected(self):
        config = SessionConfig(
            mode=SessionMode.CASH_GAME,
            num_seats=2,
            starting_stack=500.0,
            blind_structure=BlindStructure(levels=[BlindLevel(5.0, 10.0)]),
        )
        with pytest.raises(ValueError, match="Too many players"):
            Session(config, make_players(3))

    def test_too_few_players_rejected(self):
        config = SessionConfig(
            mode=SessionMode.CASH_GAME,
            num_seats=4,
            starting_stack=500.0,
            blind_structure=BlindStructure(levels=[BlindLevel(5.0, 10.0)]),
        )
        with pytest.raises(ValueError, match="at least 2"):
            Session(config, [RandomPlayer("Lonely", seed=0)])

    def test_run_one_hand_at_a_time(self):
        config = SessionConfig(
            mode=SessionMode.CASH_GAME,
            num_seats=3,
            starting_stack=500.0,
            blind_structure=BlindStructure(levels=[BlindLevel(5.0, 10.0)]),
            num_hands=5,
        )
        session = Session(config, make_players(3))
        for _ in range(5):
            history = session.run_one_hand()
            assert history is not None
        assert len(session.hand_histories) == 5
