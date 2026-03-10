"""Betting round logic, pot-limit rules, side pots, and shared enums."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


# ---------------------------------------------------------------------------
# Hand phase — shared across modules to avoid circular imports
# ---------------------------------------------------------------------------

class HandPhase(Enum):
    POST_BLINDS = auto()
    DEAL_HOLE_CARDS = auto()
    PREFLOP_BETTING = auto()
    DEAL_FLOP = auto()
    FLOP_BETTING = auto()
    DEAL_TURN = auto()
    TURN_BETTING = auto()
    DEAL_RIVER = auto()
    RIVER_BETTING = auto()
    SHOWDOWN = auto()
    DISTRIBUTE_POTS = auto()
    HAND_COMPLETE = auto()


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

class ActionType(Enum):
    FOLD = auto()
    CHECK = auto()
    CALL = auto()
    BET = auto()       # first bet in a round (current_bet == 0)
    RAISE = auto()     # raise over an existing bet


@dataclass(frozen=True)
class Action:
    """A player action."""
    action_type: ActionType
    player_seat: int
    amount: float = 0.0       # total chips put in this round (for BET/RAISE/CALL)
    is_all_in: bool = False   # true if this action puts the player all-in

    def describe(self) -> str:
        name = self.action_type.name.lower()
        if self.action_type in (ActionType.FOLD, ActionType.CHECK):
            s = f"Seat {self.player_seat} {name}s"
        elif self.action_type == ActionType.CALL:
            s = f"Seat {self.player_seat} calls {self.amount:.0f}"
        elif self.action_type == ActionType.BET:
            s = f"Seat {self.player_seat} bets {self.amount:.0f}"
        elif self.action_type == ActionType.RAISE:
            s = f"Seat {self.player_seat} raises to {self.amount:.0f}"
        else:
            s = f"Seat {self.player_seat} {name} {self.amount:.0f}"
        if self.is_all_in:
            s += " (all-in)"
        return s


# ---------------------------------------------------------------------------
# Pot-limit calculations
# ---------------------------------------------------------------------------

def calculate_pot_limit_max(
    total_pot: float,
    amount_to_call: float,
    player_stack: float,
) -> float:
    """
    Maximum *additional* chips a player can put in under pot-limit rules.

    Standard rule: you may raise up to the size of the pot after your call.

    total_pot: all chips currently in the middle (all rounds, all players).
    amount_to_call: chips needed to match the current bet.
    player_stack: player's remaining stack (not yet in pot).

    Returns the maximum additional chips the player can put in, capped
    by their stack.
    """
    pot_after_call = total_pot + amount_to_call
    max_raise = pot_after_call
    max_additional = amount_to_call + max_raise
    return min(max_additional, player_stack)


def legal_actions(
    total_pot: float,
    current_bet: float,
    player_chips_in_round: float,
    player_stack: float,
    min_raise: float,
) -> list[Action]:
    """
    Generate all legal actions for a player at a given seat.

    Returns a list of actions with standard bet sizes.
    The seat index is set to -1; the caller should replace it.
    """
    actions: list[Action] = []
    amount_to_call = current_bet - player_chips_in_round

    # Fold is always legal
    actions.append(Action(ActionType.FOLD, player_seat=-1))

    if amount_to_call <= 0:
        # No bet to face — can check or bet
        actions.append(Action(ActionType.CHECK, player_seat=-1))

        if player_stack > 0:
            pot_max = calculate_pot_limit_max(total_pot, 0.0, player_stack)
            if pot_max > 0:
                _add_bet_sizes(
                    actions, ActionType.BET, total_pot, 0.0,
                    min_raise, pot_max, player_stack, player_chips_in_round,
                )
    else:
        # Facing a bet — can call or raise
        call_amount = min(amount_to_call, player_stack)
        is_all_in = call_amount >= player_stack
        actions.append(Action(
            ActionType.CALL, player_seat=-1,
            amount=player_chips_in_round + call_amount,
            is_all_in=is_all_in,
        ))

        if not is_all_in:
            remaining_after_call = player_stack - call_amount
            if remaining_after_call > 0:
                pot_max = calculate_pot_limit_max(
                    total_pot, amount_to_call, player_stack,
                )
                _add_bet_sizes(
                    actions, ActionType.RAISE, total_pot, amount_to_call,
                    min_raise, pot_max, player_stack, player_chips_in_round,
                )

    return actions


def _add_bet_sizes(
    actions: list[Action],
    action_type: ActionType,
    total_pot: float,
    amount_to_call: float,
    min_raise: float,
    pot_max_additional: float,
    player_stack: float,
    player_chips_in_round: float,
) -> None:
    """Add standard bet/raise sizes to the action list."""
    # Min raise total = current_bet + min_raise (for raise) or min_raise (for bet)
    # pot_max_additional is the max additional chips the player can put in
    min_total = player_chips_in_round + min_raise
    max_total = player_chips_in_round + pot_max_additional

    if action_type == ActionType.RAISE:
        min_total = player_chips_in_round + amount_to_call + min_raise

    # All-in total
    all_in_total = player_chips_in_round + player_stack

    # Standard sizes: 33%, 50%, 67%, 75%, 100% of pot
    sizes = []
    for frac in (0.33, 0.50, 0.67, 0.75, 1.0):
        bet_size = total_pot * frac
        if action_type == ActionType.RAISE:
            total = player_chips_in_round + amount_to_call + bet_size
        else:
            total = player_chips_in_round + bet_size
        sizes.append(total)

    # Add min-raise
    sizes.append(min_total)
    # Add all-in
    sizes.append(all_in_total)

    seen = set()
    for total in sorted(sizes):
        # Clamp to [min_total, max_total] but allow all-in below min
        if total < min_total and total != all_in_total:
            continue
        if total > max_total:
            total = max_total

        # Round to avoid float noise
        total = round(total, 2)
        if total in seen:
            continue
        if total <= player_chips_in_round:
            continue
        seen.add(total)

        is_all_in = abs(total - all_in_total) < 0.01
        actions.append(Action(
            action_type, player_seat=-1,
            amount=total, is_all_in=is_all_in,
        ))


def validate_action(
    action: Action,
    total_pot: float,
    current_bet: float,
    player_chips_in_round: float,
    player_stack: float,
    min_raise: float,
    player_is_folded: bool,
    player_is_all_in: bool,
) -> tuple[bool, str]:
    """
    Check whether an action is legal.

    Returns (is_valid, reason_if_invalid).
    """
    if player_is_folded:
        return False, "Player has already folded"
    if player_is_all_in:
        return False, "Player is all-in"

    amount_to_call = current_bet - player_chips_in_round
    at = action.action_type

    if at == ActionType.FOLD:
        return True, ""

    if at == ActionType.CHECK:
        if amount_to_call > 0:
            return False, f"Cannot check when facing a bet of {amount_to_call}"
        return True, ""

    if at == ActionType.CALL:
        if amount_to_call <= 0:
            return False, "Nothing to call"
        return True, ""

    # BET or RAISE
    if at == ActionType.BET:
        if current_bet > 0:
            return False, "Cannot bet when there is already a bet; use raise"
        additional = action.amount - player_chips_in_round
        if additional <= 0:
            return False, "Bet amount must be positive"
        # Check minimum (allow all-in for less)
        if additional < min_raise and additional < player_stack:
            return False, f"Bet {additional} is below minimum {min_raise}"
        # Check pot limit
        pot_max = calculate_pot_limit_max(total_pot, 0.0, player_stack)
        if additional > pot_max + 0.01:
            return False, f"Bet {additional} exceeds pot-limit max {pot_max}"
        return True, ""

    if at == ActionType.RAISE:
        if current_bet <= 0:
            return False, "Cannot raise when there is no bet; use bet"
        additional = action.amount - player_chips_in_round
        raise_size = additional - amount_to_call
        # Check minimum raise (allow all-in for less)
        if raise_size < min_raise and additional < player_stack:
            return False, f"Raise of {raise_size} is below minimum {min_raise}"
        # Check pot limit
        pot_max = calculate_pot_limit_max(total_pot, amount_to_call, player_stack)
        if additional > pot_max + 0.01:
            return False, f"Raise total {additional} exceeds pot-limit max {pot_max}"
        return True, ""

    return False, f"Unknown action type: {at}"


# ---------------------------------------------------------------------------
# Side pots
# ---------------------------------------------------------------------------

@dataclass
class Pot:
    """A main pot or side pot."""
    amount: float
    eligible_players: list[int]  # seat indices who can win this pot


def calculate_pots(investments: dict[int, float]) -> list[Pot]:
    """
    Calculate main and side pots from player investments.

    investments: {seat_index: total_chips_invested_this_hand}

    Algorithm:
    1. Get sorted unique investment levels.
    2. For each level, each player contributes up to (level - prev_level).
    3. Players who invested >= level are eligible.
    """
    if not investments:
        return []

    # Sort players by investment ascending
    sorted_players = sorted(investments.items(), key=lambda x: x[1])

    pots: list[Pot] = []
    prev_level = 0.0

    # Get unique investment levels
    levels = sorted(set(investments.values()))

    for level in levels:
        increment = level - prev_level
        if increment <= 0:
            continue
        amount = 0.0
        eligible = []
        for seat, invested in investments.items():
            contribution = min(invested, level) - min(invested, prev_level)
            amount += contribution
            if invested >= level:
                eligible.append(seat)
        if amount > 0:
            pots.append(Pot(amount=round(amount, 2), eligible_players=sorted(eligible)))
        prev_level = level

    return pots
