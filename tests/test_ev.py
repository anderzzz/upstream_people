"""Tests for EV and decision engine."""
import pytest

from plo_engine.ev import pot_odds, pot_limit_max_raise, effective_pot_odds, ImpliedOddsModel


class TestPotOdds:
    def test_basic(self):
        # pot=100, bet=50 -> need 33.3% equity
        assert abs(pot_odds(100, 50) - 1/3) < 0.001

    def test_pot_size_bet(self):
        # pot=100, bet=100 -> need 50% equity
        assert abs(pot_odds(100, 100) - 0.5) < 0.001

    def test_small_bet(self):
        # pot=100, bet=10 -> need ~9% equity
        assert abs(pot_odds(100, 10) - 10/110) < 0.001

    def test_zero_pot(self):
        assert pot_odds(0, 0) == 0.0


class TestPotLimitMaxRaise:
    def test_no_call(self):
        # pot=100, to_call=0 -> max raise = 100 (pot-size bet)
        assert pot_limit_max_raise(100, 0) == 100

    def test_with_call(self):
        # pot=100, to_call=50 -> max raise = 100 + 2*50 = 200
        assert pot_limit_max_raise(100, 50) == 200

    def test_3bet(self):
        # pot=10, to_call=30 -> max raise = 10 + 60 = 70
        assert pot_limit_max_raise(10, 30) == 70


class TestImpliedOdds:
    def test_positive_implied_odds(self):
        # With good implied odds, effective pot odds should be better
        normal = pot_odds(100, 50)  # 33.3%
        implied = ImpliedOddsModel(
            expected_additional_winnings=100,
            expected_additional_losses=0,
            probability_of_improvement=0.3,
        )
        effective = effective_pot_odds(100, 50, implied)
        # With implied odds, we need less equity to call
        assert effective < normal

    def test_reverse_implied_odds(self):
        # With reverse implied odds (losses when we hit), we need more equity
        normal = pot_odds(100, 50)
        implied = ImpliedOddsModel(
            expected_additional_winnings=0,
            expected_additional_losses=200,
            probability_of_improvement=0.3,
        )
        effective = effective_pot_odds(100, 50, implied)
        assert effective > normal
