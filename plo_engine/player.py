"""Player interface and built-in player types."""

from __future__ import annotations

import random as pyrandom
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

from plo_engine.types import PLOHand, Board
from plo_engine.betting import (
    Action, ActionType, HandPhase,
)
from plo_engine.table import BlindLevel


# ---------------------------------------------------------------------------
# Views — what a player can see
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class OpponentView:
    """What I can see about another player."""
    seat: int
    stack: float
    chips_in_pot: float
    is_folded: bool
    is_all_in: bool
    name: str
    hole_cards: PLOHand | None = None  # only populated at showdown


@dataclass(frozen=True)
class PlayerView:
    """
    The game state as visible to a specific player.
    Mirrors what a human player would see at a real table.
    """
    # My info
    my_seat: int
    my_hole_cards: PLOHand
    my_stack: float
    my_chips_in_pot: float

    # Table info
    board: Board
    pot_total: float
    current_bet: float
    min_raise: float
    pot_limit_max: float

    # Other players
    opponents: list[OpponentView]

    # Context
    button_position: int
    blind_level: BlindLevel
    hand_phase: HandPhase
    action_history: list[Action]

    # Legal actions already computed
    legal_actions: list[Action]


# ---------------------------------------------------------------------------
# Player ABC
# ---------------------------------------------------------------------------

class Player(ABC):
    """
    Abstract base for any entity that can play at a PLO table.

    The table calls get_action() when it's this player's turn.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def get_action(self, view: PlayerView) -> Action:
        """Choose an action given the current visible game state."""
        ...

    def notify_deal(self, hole_cards: PLOHand) -> None:
        """Called when this player is dealt cards."""
        pass

    def notify_action(self, seat: int, action: Action) -> None:
        """Called when any player takes an action."""
        pass

    def notify_showdown(self, result: object) -> None:
        """Called at the end of a hand with full results."""
        pass

    def notify_board(self, board: Board) -> None:
        """Called when community cards are revealed."""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"


# ---------------------------------------------------------------------------
# Built-in player types
# ---------------------------------------------------------------------------

class RandomPlayer(Player):
    """
    Randomly selects among legal actions. Useful for testing.

    Action weights control the probability of fold/call-check/bet-raise.
    """

    def __init__(
        self,
        name: str,
        seed: int | None = None,
        fold_weight: float = 1.0,
        call_weight: float = 1.0,
        raise_weight: float = 1.0,
    ):
        super().__init__(name)
        self._rng = pyrandom.Random(seed)
        self._fold_w = fold_weight
        self._call_w = call_weight
        self._raise_w = raise_weight

    def get_action(self, view: PlayerView) -> Action:
        actions = view.legal_actions
        if not actions:
            raise ValueError("No legal actions available")

        # Assign weights by category
        weighted: list[tuple[Action, float]] = []
        for a in actions:
            if a.action_type == ActionType.FOLD:
                weighted.append((a, self._fold_w))
            elif a.action_type in (ActionType.CHECK, ActionType.CALL):
                weighted.append((a, self._call_w))
            else:
                weighted.append((a, self._raise_w))

        total_w = sum(w for _, w in weighted)
        if total_w <= 0:
            return self._rng.choice(actions)

        r = self._rng.random() * total_w
        cumulative = 0.0
        for action, w in weighted:
            cumulative += w
            if r <= cumulative:
                return action
        return weighted[-1][0]


class CallingStation(Player):
    """Always calls (never folds, never raises)."""

    def get_action(self, view: PlayerView) -> Action:
        for a in view.legal_actions:
            if a.action_type == ActionType.CALL:
                return a
            if a.action_type == ActionType.CHECK:
                return a
        # Shouldn't happen, but fold as last resort
        for a in view.legal_actions:
            if a.action_type == ActionType.FOLD:
                return a
        return view.legal_actions[0]


class HumanPlayer(Player):
    """
    A human player who inputs actions via a callback.

    The callback receives a PlayerView and must return a legal Action.
    """

    def __init__(self, name: str, input_callback: Callable[[PlayerView], Action]):
        super().__init__(name)
        self._callback = input_callback

    def get_action(self, view: PlayerView) -> Action:
        return self._callback(view)
