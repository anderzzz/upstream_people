"""Layer 2: EV and Decision Engine.

Pot odds, implied odds, and action expected value calculations.
"""
from __future__ import annotations

from dataclasses import dataclass

from plo_engine.types import PLOHand, Board, Range
from plo_engine.equity import equity_hand_vs_range


def pot_odds(pot: float, bet_to_call: float) -> float:
    """Minimum equity needed to profitably call.

    Returns bet_to_call / (pot + bet_to_call).
    Example: pot=100, bet=50 -> 50/150 = 33.3%
    """
    if pot + bet_to_call == 0:
        return 0.0
    return bet_to_call / (pot + bet_to_call)


def pot_limit_max_raise(pot: float, to_call: float) -> float:
    """Maximum legal raise in pot-limit.

    You first call, then raise up to the new pot size.
    max_raise = pot + to_call + to_call
    total_bet = to_call + max_raise
    """
    return pot + 2 * to_call


@dataclass
class ImpliedOddsModel:
    """Model of future value/risk beyond the current bet."""
    expected_additional_winnings: float
    expected_additional_losses: float
    probability_of_improvement: float


def effective_pot_odds(
    pot: float,
    bet_to_call: float,
    implied: ImpliedOddsModel,
) -> float:
    """Adjusted pot odds incorporating implied odds."""
    eff_pot = pot + implied.expected_additional_winnings * implied.probability_of_improvement
    eff_cost = bet_to_call + implied.expected_additional_losses * (1 - implied.probability_of_improvement)
    if eff_pot + eff_cost == 0:
        return 0.0
    return eff_cost / (eff_pot + eff_cost)


@dataclass
class ActionEV:
    """Expected value of a possible action."""
    action: str
    ev: float
    ev_bb: float


def evaluate_actions(
    hand: PLOHand,
    board: Board,
    opponent_range: Range,
    pot: float,
    to_call: float,
    stack: float,
    *,
    bb_size: float = 1.0,
    raise_sizes: list[float] | None = None,
    num_samples: int = 5000,
) -> list[ActionEV]:
    """Evaluate EV of each available action.

    For fold: EV = 0 (sunk costs ignored).
    For call: EV = equity * (pot + to_call) - (1 - equity) * to_call.
    For raise: simplified model using fold equity estimate.
    """
    result = equity_hand_vs_range(
        hand, opponent_range, board, num_samples=num_samples,
    )
    eq = result.equity

    actions: list[ActionEV] = []

    # Fold
    actions.append(ActionEV(action="fold", ev=0.0, ev_bb=0.0))

    # Check (if to_call == 0)
    if to_call == 0:
        check_ev = eq * pot - (1 - eq) * 0
        actions.append(ActionEV(
            action="check",
            ev=check_ev,
            ev_bb=check_ev / bb_size if bb_size > 0 else 0,
        ))
    else:
        # Call
        call_ev = eq * (pot + to_call) - (1 - eq) * to_call
        actions.append(ActionEV(
            action="call",
            ev=call_ev,
            ev_bb=call_ev / bb_size if bb_size > 0 else 0,
        ))

    # Raises
    if raise_sizes is None:
        raise_sizes = [0.5, 0.75, 1.0]  # fractions of pot

    max_raise = pot_limit_max_raise(pot, to_call)

    for frac in raise_sizes:
        raise_amount = frac * (pot + to_call)
        total_bet = to_call + raise_amount

        if total_bet > stack:
            total_bet = stack
            raise_amount = stack - to_call

        if raise_amount <= 0:
            continue

        if total_bet > max_raise:
            total_bet = max_raise
            raise_amount = max_raise - to_call

        # Simplified raise EV model:
        # Assume opponent folds ~30% (rough estimate, proper fold equity needs Layer 3)
        fold_equity = 0.30
        call_fraction = 1.0 - fold_equity

        # When opponent folds, we win the pot
        ev_fold = fold_equity * pot
        # When opponent calls, it's an equity calculation with bigger pot
        new_pot = pot + total_bet + to_call
        ev_call = call_fraction * (eq * new_pot - (1 - eq) * total_bet)

        raise_ev = ev_fold + ev_call

        action_name = f"raise_{frac:.0%}" if frac < 10 else f"raise_to_{total_bet:.0f}"
        actions.append(ActionEV(
            action=action_name,
            ev=raise_ev,
            ev_bb=raise_ev / bb_size if bb_size > 0 else 0,
        ))

    return actions
