"""Table: seats, stacks, blinds, button position."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from plo_engine.player import Player


@dataclass
class BlindLevel:
    small_blind: float
    big_blind: float
    ante: float = 0.0


@dataclass
class BlindStructure:
    """
    Defines the blind levels for a game or tournament.

    For a cash game: a single level that never changes.
    For a tournament: a schedule of escalating levels.
    """
    levels: list[BlindLevel]
    current_level_index: int = 0
    hands_per_level: int | None = None  # if None, advance by external trigger

    @property
    def current_level(self) -> BlindLevel:
        return self.levels[self.current_level_index]

    def advance(self) -> None:
        if self.current_level_index < len(self.levels) - 1:
            self.current_level_index += 1


@dataclass
class Seat:
    """A seat at the table. May be occupied or empty."""
    player: Player | None = None
    stack: float = 0.0
    is_sitting_out: bool = False

    @property
    def is_occupied(self) -> bool:
        return self.player is not None

    @property
    def is_active(self) -> bool:
        return self.is_occupied and not self.is_sitting_out and self.stack > 0


class Table:
    """
    The poker table: seats, stacks, blinds, button position.

    Persists across hands. HandState is created fresh each hand.
    """

    def __init__(
        self,
        num_seats: int,
        blind_structure: BlindStructure,
    ):
        if num_seats < 2 or num_seats > 9:
            raise ValueError(f"num_seats must be 2-9, got {num_seats}")
        self.seats: list[Seat] = [Seat() for _ in range(num_seats)]
        self.blind_structure: BlindStructure = blind_structure
        self.button_position: int = 0
        self.hand_number: int = 0

    @property
    def num_seats(self) -> int:
        return len(self.seats)

    def seat_player(self, seat_index: int, player: Player, stack: float) -> None:
        """Seat a player with a given stack."""
        if seat_index < 0 or seat_index >= self.num_seats:
            raise ValueError(f"Invalid seat index: {seat_index}")
        if self.seats[seat_index].is_occupied:
            raise ValueError(f"Seat {seat_index} is already occupied")
        self.seats[seat_index] = Seat(player=player, stack=stack)

    def remove_player(self, seat_index: int) -> None:
        """Remove a player (elimination or leaving)."""
        self.seats[seat_index] = Seat()

    def active_seats(self) -> list[int]:
        """Seat indices with players who have chips and are not sitting out."""
        return [i for i, s in enumerate(self.seats) if s.is_active]

    def advance_button(self) -> None:
        """Move the dealer button to the next active seat."""
        active = self.active_seats()
        if not active:
            return
        # Find next active seat after current button
        for i in range(1, self.num_seats + 1):
            candidate = (self.button_position + i) % self.num_seats
            if candidate in active:
                self.button_position = candidate
                return

    def advance_blind_level(self) -> None:
        """Move to the next blind level."""
        self.blind_structure.advance()

    def post_blinds(self) -> dict[int, float]:
        """
        Determine who posts blinds and antes.
        Returns {seat_index: amount_posted}.

        Handles heads-up (button=SB) and 3+ player rules.
        Short stacks post what they can.
        """
        active = self.active_seats()
        if len(active) < 2:
            return {}

        level = self.blind_structure.current_level
        posts: dict[int, float] = {}

        # Find positions relative to button
        btn_idx = active.index(self.button_position) if self.button_position in active else 0

        if len(active) == 2:
            # Heads-up: button posts SB, other posts BB
            sb_seat = active[btn_idx]
            bb_seat = active[(btn_idx + 1) % 2]
        else:
            # 3+ players: left of button = SB, next = BB
            sb_seat = active[(btn_idx + 1) % len(active)]
            bb_seat = active[(btn_idx + 2) % len(active)]

        # Post small blind
        sb_amount = min(level.small_blind, self.seats[sb_seat].stack)
        if sb_amount > 0:
            self.seats[sb_seat].stack -= sb_amount
            posts[sb_seat] = sb_amount

        # Post big blind
        bb_amount = min(level.big_blind, self.seats[bb_seat].stack)
        if bb_amount > 0:
            self.seats[bb_seat].stack -= bb_amount
            posts[bb_seat] = posts.get(bb_seat, 0.0) + bb_amount

        # Post antes
        if level.ante > 0:
            for seat_idx in active:
                ante_amount = min(level.ante, self.seats[seat_idx].stack)
                if ante_amount > 0:
                    self.seats[seat_idx].stack -= ante_amount
                    posts[seat_idx] = posts.get(seat_idx, 0.0) + ante_amount

        return posts
