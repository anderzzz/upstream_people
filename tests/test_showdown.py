"""Tests for showdown resolution and pot distribution."""

import pytest

from plo_engine.types import parse_plo_hand, parse_board
from plo_engine.betting import Pot
from plo_engine.showdown import resolve_showdown, distribute_pots


class TestResolveShowdown:
    def test_single_pot_clear_winner(self):
        # Player 0 has aces (stronger), Player 1 has weaker hand
        board = parse_board("As 9h 4c 2d 7s")
        hole0 = parse_plo_hand("Ah Kd Tc 8s")  # pair of aces
        hole1 = parse_plo_hand("Jd Jc 6h 3s")  # pair of jacks, no straight

        pots = [Pot(amount=200.0, eligible_players=[0, 1])]
        results = resolve_showdown(
            {0: hole0, 1: hole1}, board, pots, set(), button_position=0,
        )

        assert len(results) == 1
        assert results[0].winners == [0]
        assert results[0].amount_per_winner == 200.0

    def test_split_pot(self):
        # Both players make the same straight from the board
        board = parse_board("Ts 9h 8c 7d 6s")
        hole0 = parse_plo_hand("Ah Kd 2c 3s")  # T-high straight from board
        hole1 = parse_plo_hand("Ad Kc 2h 3d")  # Same straight

        pots = [Pot(amount=200.0, eligible_players=[0, 1])]
        results = resolve_showdown(
            {0: hole0, 1: hole1}, board, pots, set(), button_position=0,
        )

        # Both should win (split)
        assert len(results[0].winners) == 2
        assert results[0].amount_per_winner == 100.0

    def test_folded_player_excluded(self):
        board = parse_board("As 9h 4c 2d 7s")
        hole0 = parse_plo_hand("3h 3d 5c 6s")  # weak
        hole1 = parse_plo_hand("Ah Kd Tc 8s")  # strong but folded

        pots = [Pot(amount=200.0, eligible_players=[0, 1])]
        results = resolve_showdown(
            {0: hole0, 1: hole1}, board, pots, folded={1}, button_position=0,
        )

        assert results[0].winners == [0]
        assert results[0].amount_per_winner == 200.0

    def test_side_pots(self):
        board = parse_board("As Kh Qc Jd Ts")
        # Player 0: broadway straight (A-K-Q-J-T)
        hole0 = parse_plo_hand("Ah Kd 2c 3s")
        # Player 1: also broadway with different suits
        hole1 = parse_plo_hand("Ad Kc 2h 3d")
        # Player 2: weaker
        hole2 = parse_plo_hand("9h 8d 7c 6s")

        pots = [
            Pot(amount=300.0, eligible_players=[0, 1, 2]),
            Pot(amount=200.0, eligible_players=[1, 2]),
        ]
        results = resolve_showdown(
            {0: hole0, 1: hole1, 2: hole2},
            board, pots, set(), button_position=0,
        )

        # Main pot: split between 0 and 1
        assert sorted(results[0].winners) == [0, 1]
        assert results[0].amount_per_winner == 150.0
        # Side pot: player 1 wins
        assert results[1].winners == [1]
        assert results[1].amount_per_winner == 200.0

    def test_requires_5_board_cards(self):
        with pytest.raises(ValueError):
            resolve_showdown({}, parse_board("As Kh Qc"), [], set(), 0)


class TestDistributePots:
    def test_net_profit(self):
        from plo_engine.showdown import ShowdownResult

        results = [
            ShowdownResult(
                pot=Pot(amount=300.0, eligible_players=[0, 1, 2]),
                winners=[0],
                winning_hand_rank=0,
                amount_per_winner=300.0,
            ),
        ]
        investments = {0: 100.0, 1: 100.0, 2: 100.0}
        net = distribute_pots(results, investments)

        assert net[0] == 200.0    # won 300, invested 100
        assert net[1] == -100.0   # lost 100
        assert net[2] == -100.0   # lost 100

    def test_chip_conservation(self):
        from plo_engine.showdown import ShowdownResult

        results = [
            ShowdownResult(
                pot=Pot(amount=400.0, eligible_players=[0, 1, 2, 3]),
                winners=[0, 1],
                winning_hand_rank=0,
                amount_per_winner=200.0,
            ),
            ShowdownResult(
                pot=Pot(amount=300.0, eligible_players=[1, 2, 3]),
                winners=[2],
                winning_hand_rank=0,
                amount_per_winner=300.0,
            ),
        ]
        investments = {0: 100.0, 1: 250.0, 2: 250.0, 3: 100.0}
        net = distribute_pots(results, investments)

        # Net profits should sum to zero (chip conservation)
        assert abs(sum(net.values())) < 0.01
