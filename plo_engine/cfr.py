"""Layer 3: CFR solver (stub).

Full specification deferred to a later document.
"""
from __future__ import annotations

from plo_engine.types import PLOHand, Board, Range
from plo_engine.game_tree import GameState


class CFRSolver:
    """Counterfactual Regret Minimization for PLO subtrees.

    Stub implementation — to be specified in a separate document.
    """

    def __init__(
        self,
        starting_ranges: list[Range],
        board: Board,
        pot: float,
        stacks: list[float],
        bet_sizes: list[float],
    ):
        self.starting_ranges = starting_ranges
        self.board = board
        self.pot = pot
        self.stacks = stacks
        self.bet_sizes = bet_sizes
        self._trained = False

    def train(self, iterations: int) -> None:
        """Run CFR for the given number of iterations."""
        raise NotImplementedError("CFR solver is not yet implemented")

    def get_strategy(self, hand: PLOHand, state: GameState) -> dict[str, float]:
        """Get mixed strategy (action -> probability) for a hand at a state."""
        raise NotImplementedError("CFR solver is not yet implemented")

    def get_ev(self, hand: PLOHand, state: GameState) -> float:
        """Get expected value for a hand at a state under current strategy."""
        raise NotImplementedError("CFR solver is not yet implemented")
