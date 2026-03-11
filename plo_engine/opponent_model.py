"""Opponent modeling — tracks per-opponent tendencies from observed actions."""

from __future__ import annotations

from dataclasses import dataclass, field

from plo_engine.betting import Action, ActionType


@dataclass
class OpponentStats:
    """Accumulated statistics for one opponent."""
    hands_observed: int = 0

    # Preflop stats
    vpip_count: int = 0          # voluntarily put $ in pot (not forced blind)
    vpip_opportunities: int = 0
    pfr_count: int = 0           # preflop raise
    pfr_opportunities: int = 0

    # Postflop stats
    cbet_count: int = 0          # continuation bet (bet on flop as preflop raiser)
    cbet_opportunities: int = 0
    fold_to_bet_count: int = 0
    fold_to_bet_opportunities: int = 0

    # General aggression
    aggression_bets: int = 0     # bets + raises
    aggression_passive: int = 0  # calls + checks

    @property
    def vpip(self) -> float:
        """Voluntarily Put $ In Pot percentage."""
        if self.vpip_opportunities == 0:
            return 0.5  # default assumption
        return self.vpip_count / self.vpip_opportunities

    @property
    def pfr(self) -> float:
        """Preflop Raise percentage."""
        if self.pfr_opportunities == 0:
            return 0.2  # default assumption
        return self.pfr_count / self.pfr_opportunities

    @property
    def aggression_factor(self) -> float:
        """Aggression factor (bets+raises) / (calls+checks). Higher = more aggressive."""
        if self.aggression_passive == 0:
            return 1.5  # default assumption
        return self.aggression_bets / self.aggression_passive

    @property
    def fold_to_bet(self) -> float:
        """Fold to bet frequency."""
        if self.fold_to_bet_opportunities == 0:
            return 0.4  # default assumption
        return self.fold_to_bet_count / self.fold_to_bet_opportunities

    @property
    def cbet(self) -> float:
        """Continuation bet frequency."""
        if self.cbet_opportunities == 0:
            return 0.5  # default assumption
        return self.cbet_count / self.cbet_opportunities


class OpponentModel:
    """
    Tracks per-opponent statistics across hands.

    Usage: call new_hand() at start of each hand, observe_action() for each
    action, and get_stats() to retrieve accumulated statistics.
    """

    def __init__(self):
        self._stats: dict[int, OpponentStats] = {}
        # Per-hand tracking
        self._preflop_raiser: int | None = None
        self._has_acted_preflop: set[int] = set()

    def _ensure_seat(self, seat: int) -> OpponentStats:
        if seat not in self._stats:
            self._stats[seat] = OpponentStats()
        return self._stats[seat]

    def new_hand(self) -> None:
        """Call at the start of each new hand."""
        self._preflop_raiser = None
        self._has_acted_preflop = set()
        for stats in self._stats.values():
            stats.hands_observed += 1

    def observe_action(self, seat: int, action: Action, board_len: int) -> None:
        """
        Record an observed action.

        board_len: length of the current board (0=preflop, 3=flop, 4=turn, 5=river)
        """
        stats = self._ensure_seat(seat)
        is_preflop = board_len == 0

        if is_preflop:
            self._observe_preflop(seat, action, stats)
        else:
            self._observe_postflop(seat, action, stats, board_len)

    def _observe_preflop(self, seat: int, action: Action, stats: OpponentStats) -> None:
        if seat not in self._has_acted_preflop:
            self._has_acted_preflop.add(seat)
            stats.vpip_opportunities += 1
            stats.pfr_opportunities += 1

            if action.action_type in (ActionType.CALL, ActionType.BET, ActionType.RAISE):
                stats.vpip_count += 1
            if action.action_type in (ActionType.BET, ActionType.RAISE):
                stats.pfr_count += 1
                self._preflop_raiser = seat
        else:
            # Already acted preflop — could be facing a raise
            if action.action_type in (ActionType.BET, ActionType.RAISE):
                stats.aggression_bets += 1
                self._preflop_raiser = seat
            elif action.action_type in (ActionType.CALL, ActionType.CHECK):
                stats.aggression_passive += 1
            elif action.action_type == ActionType.FOLD:
                stats.fold_to_bet_opportunities += 1
                stats.fold_to_bet_count += 1

    def _observe_postflop(self, seat: int, action: Action, stats: OpponentStats, board_len: int) -> None:
        # Continuation bet tracking (flop only)
        if board_len == 3 and seat == self._preflop_raiser:
            stats.cbet_opportunities += 1
            if action.action_type in (ActionType.BET, ActionType.RAISE):
                stats.cbet_count += 1

        # General aggression
        if action.action_type in (ActionType.BET, ActionType.RAISE):
            stats.aggression_bets += 1
        elif action.action_type in (ActionType.CALL, ActionType.CHECK):
            stats.aggression_passive += 1

        # Fold to bet
        if action.action_type == ActionType.FOLD:
            stats.fold_to_bet_opportunities += 1
            stats.fold_to_bet_count += 1

    def get_stats(self, seat: int) -> OpponentStats:
        """Get accumulated stats for a seat. Returns default stats if no data."""
        return self._ensure_seat(seat)

    def estimate_fold_equity(self, seat: int) -> float:
        """Estimate probability opponent will fold to a bet."""
        return self.get_stats(seat).fold_to_bet
