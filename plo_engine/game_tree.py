"""Layer 3: Game tree (stub).

Full specification deferred to a later document.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from plo_engine.types import Board
from plo_engine.ev import pot_limit_max_raise


@dataclass
class GameState:
    """A node in the PLO game tree."""

    board: Board
    pot: float
    stacks: list[float]
    current_player: int
    betting_round: int  # 0=preflop, 1=flop, 2=turn, 3=river
    action_history: list[str] = field(default_factory=list)
    is_terminal: bool = False

    def available_actions(self, bet_sizes: list[float] | None = None) -> list[str]:
        """Actions available at this node.

        In pot-limit: fold, check (if no bet), call, and raise to various
        sizes between min-raise and pot-limit max.

        bet_sizes: fractions of pot to include (e.g., [0.33, 0.67, 1.0]).
        """
        if self.is_terminal:
            return []

        if bet_sizes is None:
            bet_sizes = [0.33, 0.67, 1.0]

        actions = ["fold"]

        # Determine if there's a bet to call
        to_call = self._to_call()
        if to_call == 0:
            actions.append("check")
        else:
            actions.append("call")

        # Raise options
        max_raise = pot_limit_max_raise(self.pot, to_call)
        stack = self.stacks[self.current_player]

        for frac in bet_sizes:
            raise_amount = frac * (self.pot + to_call)
            total = to_call + raise_amount
            if total <= max_raise and total <= stack:
                actions.append(f"raise_{frac:.0%}")

        # All-in option
        if stack <= max_raise and stack > to_call:
            actions.append("all_in")

        return actions

    def _to_call(self) -> float:
        """Amount the current player needs to call (simplified)."""
        # This is a stub — proper implementation requires tracking
        # per-player bet amounts in the current round
        if not self.action_history:
            return 0.0
        last = self.action_history[-1]
        if last.startswith("raise") or last.startswith("bet"):
            return self.pot * 0.5  # placeholder
        return 0.0
