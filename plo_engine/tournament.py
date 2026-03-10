"""Tournament / Session manager: multi-hand loop with blind escalation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

import jax

from plo_engine.deck import Deck
from plo_engine.table import Table, BlindStructure, BlindLevel
from plo_engine.player import Player
from plo_engine.hand_state import run_hand
from plo_engine.hand_history import HandHistory, build_hand_history


class SessionMode(Enum):
    CASH_GAME = auto()
    TOURNAMENT = auto()


@dataclass
class SessionConfig:
    """Configuration for a multi-hand session."""
    mode: SessionMode
    num_seats: int                       # 2-9
    starting_stack: float
    blind_structure: BlindStructure
    num_hands: int | None = None         # None = play until natural end
    allow_rebuy: bool = False
    rebuy_period_hands: int = 0
    rebuy_stack: float = 0.0
    master_seed: int = 42


class Session:
    """
    Runs a sequence of PLO hands.

    Manages the outer loop: seat players, deal hands, advance blinds,
    eliminate players, and collect hand histories.
    """

    def __init__(self, config: SessionConfig, players: list[Player]):
        if len(players) < 2:
            raise ValueError("Need at least 2 players")
        if len(players) > config.num_seats:
            raise ValueError(
                f"Too many players ({len(players)}) for {config.num_seats} seats"
            )

        self.config = config
        self.table = Table(config.num_seats, config.blind_structure)
        self.hand_histories: list[HandHistory] = []
        self.is_complete = False
        self._master_key = jax.random.PRNGKey(config.master_seed)
        self._hand_count = 0

        # Seat players
        for i, player in enumerate(players):
            self.table.seat_player(i, player, config.starting_stack)

        # Set initial button
        self.table.button_position = 0

    def _next_deck(self) -> tuple[Deck, int]:
        """Create the next deck using the session RNG."""
        self._master_key, subkey = jax.random.split(self._master_key)
        seed = int(jax.random.randint(subkey, (), 0, 2**30))
        return Deck.from_seed(seed), seed

    def _should_stop(self) -> bool:
        """Check if the session should end."""
        if self.is_complete:
            return True

        active = self.table.active_seats()
        if len(active) < 2:
            self.is_complete = True
            return True

        if self.config.num_hands is not None:
            if self._hand_count >= self.config.num_hands:
                self.is_complete = True
                return True

        return False

    def _advance_blinds_if_needed(self) -> None:
        """Advance blind level if the schedule requires it."""
        bs = self.config.blind_structure
        if bs.hands_per_level is not None and bs.hands_per_level > 0:
            if self._hand_count > 0 and self._hand_count % bs.hands_per_level == 0:
                bs.advance()

    def _eliminate_busted(self) -> list[int]:
        """Remove players with zero chips (tournament mode)."""
        eliminated = []
        if self.config.mode == SessionMode.TOURNAMENT:
            for seat_idx in list(self.table.active_seats()):
                seat = self.table.seats[seat_idx]
                if seat.stack <= 0 and seat.is_occupied:
                    eliminated.append(seat_idx)
                    self.table.remove_player(seat_idx)
        return eliminated

    def _handle_rebuys(self) -> None:
        """Handle rebuy logic if enabled."""
        if not self.config.allow_rebuy:
            return
        if self._hand_count > self.config.rebuy_period_hands:
            return
        for seat_idx in range(self.table.num_seats):
            seat = self.table.seats[seat_idx]
            if seat.is_occupied and seat.stack <= 0:
                seat.stack = self.config.rebuy_stack

    def _make_table_config(self) -> dict:
        """Snapshot table config for hand history."""
        level = self.table.blind_structure.current_level
        return {
            "button": self.table.button_position,
            "blind_level": f"{level.small_blind}/{level.big_blind}",
            "stacks": {
                str(s.player.name if s.player else i): s.stack
                for i, s in enumerate(self.table.seats) if s.is_occupied
            },
            "names": {
                str(i): s.player.name
                for i, s in enumerate(self.table.seats) if s.is_occupied
            },
        }

    def run_one_hand(self) -> HandHistory:
        """Run a single hand and return its history."""
        self._advance_blinds_if_needed()
        self.table.advance_button()
        self.table.hand_number = self._hand_count + 1

        deck, seed = self._next_deck()
        table_config = self._make_table_config()

        result = run_hand(self.table, deck)

        final_stacks = {
            i: self.table.seats[i].stack
            for i in self.table.active_seats()
        }
        # Include busted players too
        for p in getattr(result, "_player_states", []):
            if p.seat_index not in final_stacks:
                final_stacks[p.seat_index] = self.table.seats[p.seat_index].stack

        history = build_hand_history(table_config, result, final_stacks, seed)
        self.hand_histories.append(history)
        self._hand_count += 1

        # Post-hand maintenance
        self._handle_rebuys()
        self._eliminate_busted()

        return history

    def run(self) -> list[HandHistory]:
        """Run the full session. Returns all hand histories."""
        while not self._should_stop():
            self.run_one_hand()
        self.is_complete = True
        return self.hand_histories

    def standings(self) -> list[tuple[str, float]]:
        """Current standings: [(player_name, stack), ...] sorted by stack."""
        results = []
        for seat in self.table.seats:
            if seat.is_occupied and seat.player is not None:
                results.append((seat.player.name, seat.stack))
        return sorted(results, key=lambda x: x[1], reverse=True)

    def summary(self) -> str:
        """Session summary statistics."""
        lines = []
        lines.append(f"Session: {self.config.mode.name}")
        lines.append(f"Hands played: {self._hand_count}")
        level = self.table.blind_structure.current_level
        lines.append(f"Current blinds: {level.small_blind}/{level.big_blind}")
        lines.append("")
        lines.append("Standings:")
        for name, stack in self.standings():
            lines.append(f"  {name}: {stack:.0f}")

        if self.hand_histories:
            # Biggest pot
            biggest = max(
                self.hand_histories,
                key=lambda h: sum(abs(v) for v in h.result.net_profit.values()),
            )
            total_moved = sum(
                v for v in biggest.result.net_profit.values() if v > 0
            )
            lines.append(f"\nBiggest pot: Hand #{biggest.hand_number} ({total_moved:.0f} chips)")

        return "\n".join(lines)
