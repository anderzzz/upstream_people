"""Tests for betting logic: pot-limit calculations, action validation, side pots."""

import pytest

from plo_engine.betting import (
    Action, ActionType, Pot,
    calculate_pot_limit_max, calculate_pots,
    legal_actions, validate_action,
)


class TestPotLimitMax:
    def test_opening_bet_empty_pot(self):
        # Pot is 100, no bet yet, player has 500 stack
        # Can bet up to pot size = 100
        max_add = calculate_pot_limit_max(
            total_pot=100.0, amount_to_call=0.0, player_stack=500.0,
        )
        assert max_add == 100.0

    def test_facing_bet(self):
        # Pot is 200 (including A's bet of 50), B must call 50
        # After B calls, pot = 200 + 50 = 250
        # B can raise up to 250
        # Total additional for B = 50 (call) + 250 (raise) = 300
        max_add = calculate_pot_limit_max(
            total_pot=200.0, amount_to_call=50.0, player_stack=500.0,
        )
        assert max_add == 300.0

    def test_capped_by_stack(self):
        # Pot is 200, call 50, but player only has 100
        max_add = calculate_pot_limit_max(
            total_pot=200.0, amount_to_call=50.0, player_stack=100.0,
        )
        assert max_add == 100.0

    def test_no_bet_to_call(self):
        max_add = calculate_pot_limit_max(
            total_pot=50.0, amount_to_call=0.0, player_stack=1000.0,
        )
        assert max_add == 50.0

    def test_large_pot(self):
        max_add = calculate_pot_limit_max(
            total_pot=1000.0, amount_to_call=200.0, player_stack=5000.0,
        )
        # pot_after_call = 1200, max raise = 1200, total = 200 + 1200 = 1400
        assert max_add == 1400.0


class TestCalculatePots:
    def test_single_pot_equal_investments(self):
        investments = {0: 100.0, 1: 100.0, 2: 100.0}
        pots = calculate_pots(investments)
        assert len(pots) == 1
        assert pots[0].amount == 300.0
        assert sorted(pots[0].eligible_players) == [0, 1, 2]

    def test_side_pot_one_short(self):
        # Player 0 is all-in for 100, others put in 250
        investments = {0: 100.0, 1: 250.0, 2: 250.0}
        pots = calculate_pots(investments)
        assert len(pots) == 2
        # Main pot: 3 * 100 = 300
        assert pots[0].amount == 300.0
        assert sorted(pots[0].eligible_players) == [0, 1, 2]
        # Side pot: 2 * 150 = 300
        assert pots[1].amount == 300.0
        assert sorted(pots[1].eligible_players) == [1, 2]

    def test_multiple_side_pots(self):
        # Spec example: [100, 250, 250, 500]
        investments = {0: 100.0, 1: 250.0, 2: 250.0, 3: 500.0}
        pots = calculate_pots(investments)
        assert len(pots) == 3
        # Main: 4 * 100 = 400
        assert pots[0].amount == 400.0
        assert sorted(pots[0].eligible_players) == [0, 1, 2, 3]
        # Side 1: 3 * 150 = 450
        assert pots[1].amount == 450.0
        assert sorted(pots[1].eligible_players) == [1, 2, 3]
        # Side 2: 1 * 250 = 250
        assert pots[2].amount == 250.0
        assert pots[2].eligible_players == [3]

    def test_empty_investments(self):
        pots = calculate_pots({})
        assert pots == []

    def test_heads_up_equal(self):
        investments = {0: 500.0, 1: 500.0}
        pots = calculate_pots(investments)
        assert len(pots) == 1
        assert pots[0].amount == 1000.0

    def test_chip_conservation(self):
        """Total chips in all pots equals total invested."""
        investments = {0: 75.0, 1: 200.0, 2: 200.0, 3: 350.0, 4: 500.0}
        pots = calculate_pots(investments)
        total_in_pots = sum(p.amount for p in pots)
        total_invested = sum(investments.values())
        assert abs(total_in_pots - total_invested) < 0.01


class TestValidateAction:
    def _validate(self, action, total_pot=100.0, current_bet=0.0,
                  chips_in_round=0.0, stack=500.0, min_raise=10.0):
        return validate_action(
            action, total_pot, current_bet, chips_in_round,
            stack, min_raise, False, False,
        )

    def test_fold_always_valid(self):
        valid, _ = self._validate(Action(ActionType.FOLD, 0))
        assert valid

    def test_check_no_bet(self):
        valid, _ = self._validate(Action(ActionType.CHECK, 0))
        assert valid

    def test_check_facing_bet_invalid(self):
        valid, reason = self._validate(
            Action(ActionType.CHECK, 0), current_bet=50.0,
        )
        assert not valid
        assert "Cannot check" in reason

    def test_call_facing_bet(self):
        valid, _ = self._validate(
            Action(ActionType.CALL, 0, amount=50.0), current_bet=50.0,
        )
        assert valid

    def test_call_no_bet_invalid(self):
        valid, reason = self._validate(
            Action(ActionType.CALL, 0, amount=0.0),
        )
        assert not valid

    def test_bet_no_existing(self):
        valid, _ = self._validate(
            Action(ActionType.BET, 0, amount=50.0),
            total_pot=100.0, current_bet=0.0,
        )
        assert valid

    def test_bet_below_minimum(self):
        valid, reason = self._validate(
            Action(ActionType.BET, 0, amount=5.0),
            min_raise=10.0,
        )
        assert not valid
        assert "below minimum" in reason

    def test_bet_over_pot_limit(self):
        valid, reason = self._validate(
            Action(ActionType.BET, 0, amount=200.0),
            total_pot=100.0, stack=500.0,
        )
        assert not valid
        assert "exceeds pot-limit" in reason

    def test_raise_valid(self):
        valid, _ = self._validate(
            Action(ActionType.RAISE, 0, amount=100.0),
            total_pot=200.0, current_bet=50.0, min_raise=50.0,
        )
        assert valid

    def test_folded_player_invalid(self):
        valid, _ = validate_action(
            Action(ActionType.CHECK, 0),
            100.0, 0.0, 0.0, 500.0, 10.0, True, False,
        )
        assert not valid

    def test_all_in_player_invalid(self):
        valid, _ = validate_action(
            Action(ActionType.CHECK, 0),
            100.0, 0.0, 0.0, 0.0, 10.0, False, True,
        )
        assert not valid

    def test_all_in_for_less_than_min_raise_valid(self):
        # Player has 5 chips but min_raise is 10
        # All-in for less is always allowed
        valid, _ = self._validate(
            Action(ActionType.BET, 0, amount=5.0, is_all_in=True),
            total_pot=100.0, stack=5.0, min_raise=10.0,
        )
        assert valid


class TestLegalActions:
    def test_no_bet_includes_check_and_bet(self):
        actions = legal_actions(
            total_pot=100.0, current_bet=0.0,
            player_chips_in_round=0.0, player_stack=500.0,
            min_raise=10.0,
        )
        types = {a.action_type for a in actions}
        assert ActionType.FOLD in types
        assert ActionType.CHECK in types
        assert ActionType.BET in types
        assert ActionType.CALL not in types

    def test_facing_bet_includes_call_and_raise(self):
        actions = legal_actions(
            total_pot=200.0, current_bet=50.0,
            player_chips_in_round=0.0, player_stack=500.0,
            min_raise=50.0,
        )
        types = {a.action_type for a in actions}
        assert ActionType.FOLD in types
        assert ActionType.CALL in types
        assert ActionType.RAISE in types
        assert ActionType.CHECK not in types

    def test_all_in_included(self):
        actions = legal_actions(
            total_pot=100.0, current_bet=0.0,
            player_chips_in_round=0.0, player_stack=50.0,
            min_raise=10.0,
        )
        bets = [a for a in actions if a.action_type == ActionType.BET]
        assert any(a.is_all_in for a in bets)

    def test_zero_stack_only_fold_check(self):
        """Player with no chips can only check or fold."""
        actions = legal_actions(
            total_pot=100.0, current_bet=0.0,
            player_chips_in_round=0.0, player_stack=0.0,
            min_raise=10.0,
        )
        types = {a.action_type for a in actions}
        assert types == {ActionType.FOLD, ActionType.CHECK}
