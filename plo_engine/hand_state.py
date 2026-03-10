"""HandState: the state machine for one PLO hand."""

from __future__ import annotations

from dataclasses import dataclass, field

from plo_engine.types import PLOHand, Board, make_board
from plo_engine.deck import Deck
from plo_engine.betting import (
    Action, ActionType, HandPhase, Pot,
    calculate_pot_limit_max, calculate_pots,
    legal_actions as compute_legal_actions,
    validate_action,
)
from plo_engine.table import Table, BlindLevel
from plo_engine.player import Player, PlayerView, OpponentView
from plo_engine.showdown import (
    ShowdownResult, HandResult,
    resolve_showdown, distribute_pots,
)


# ---------------------------------------------------------------------------
# Per-player state within a hand
# ---------------------------------------------------------------------------

@dataclass
class PlayerHandState:
    """Per-player state within a single hand."""
    seat_index: int
    player: Player
    hole_cards: PLOHand | None = None
    is_folded: bool = False
    is_all_in: bool = False
    chips_invested: float = 0.0        # total put into pot this hand
    chips_invested_this_round: float = 0.0
    stack_at_start: float = 0.0        # for hand history

    def invest(self, amount: float, table: Table) -> float:
        """
        Move chips from stack to pot. Returns actual amount invested
        (may be less if short-stacked).
        """
        seat = table.seats[self.seat_index]
        actual = min(amount, seat.stack)
        seat.stack -= actual
        self.chips_invested += actual
        self.chips_invested_this_round += actual
        if seat.stack <= 0:
            self.is_all_in = True
        return actual

    def reset_round(self) -> None:
        """Reset per-round tracking at the start of a new betting round."""
        self.chips_invested_this_round = 0.0


# ---------------------------------------------------------------------------
# HandState
# ---------------------------------------------------------------------------

class HandState:
    """
    Complete state of a single PLO hand in progress.

    Created by the Table at the start of each hand. Manages the
    phase state machine, delegates to betting and showdown modules.
    """

    def __init__(self, table: Table, deck: Deck):
        self.table = table
        self.deck = deck
        self.phase = HandPhase.POST_BLINDS
        self.board: Board = ()
        self.players: list[PlayerHandState] = []
        self.pots: list[Pot] = []
        self.current_bet: float = 0.0
        self.min_raise: float = table.blind_structure.current_level.big_blind
        self.action_log: list[Action] = []
        self._last_raiser_seat: int | None = None

        # Initialize player states for active seats
        for seat_idx in table.active_seats():
            seat = table.seats[seat_idx]
            self.players.append(PlayerHandState(
                seat_index=seat_idx,
                player=seat.player,
                stack_at_start=seat.stack,
            ))

    def _get_player(self, seat_index: int) -> PlayerHandState | None:
        for p in self.players:
            if p.seat_index == seat_index:
                return p
        return None

    def active_players(self) -> list[PlayerHandState]:
        """Players who haven't folded and aren't all-in."""
        return [p for p in self.players if not p.is_folded and not p.is_all_in]

    def remaining_players(self) -> list[PlayerHandState]:
        """Players who haven't folded (includes all-in)."""
        return [p for p in self.players if not p.is_folded]

    def is_hand_over(self) -> bool:
        """True if only one player remains (all others folded)."""
        return len(self.remaining_players()) <= 1

    def is_all_in_runout(self) -> bool:
        """True if all remaining players are all-in (or at most one is not)."""
        remaining = self.remaining_players()
        active = [p for p in remaining if not p.is_all_in]
        return len(active) <= 1 and len(remaining) >= 2

    def total_pot(self) -> float:
        """Sum of all chips invested by all players."""
        return sum(p.chips_invested for p in self.players)

    def _build_player_view(self, player: PlayerHandState) -> PlayerView:
        """Construct the PlayerView for a specific player."""
        seat = player.seat_index
        stack = self.table.seats[seat].stack
        amount_to_call = max(0.0, self.current_bet - player.chips_invested_this_round)
        pot_max = calculate_pot_limit_max(
            self.total_pot(), amount_to_call, stack,
        )

        opponents = []
        for p in self.players:
            if p.seat_index == seat:
                continue
            opponents.append(OpponentView(
                seat=p.seat_index,
                stack=self.table.seats[p.seat_index].stack,
                chips_in_pot=p.chips_invested,
                is_folded=p.is_folded,
                is_all_in=p.is_all_in,
                name=p.player.name,
            ))

        actions = compute_legal_actions(
            total_pot=self.total_pot(),
            current_bet=self.current_bet,
            player_chips_in_round=player.chips_invested_this_round,
            player_stack=stack,
            min_raise=self.min_raise,
        )
        # Set the correct seat index on all actions
        actions = [
            Action(a.action_type, seat, a.amount, a.is_all_in)
            for a in actions
        ]

        return PlayerView(
            my_seat=seat,
            my_hole_cards=player.hole_cards,
            my_stack=stack,
            my_chips_in_pot=player.chips_invested,
            board=self.board,
            pot_total=self.total_pot(),
            current_bet=self.current_bet,
            min_raise=self.min_raise,
            pot_limit_max=pot_max,
            opponents=opponents,
            button_position=self.table.button_position,
            blind_level=self.table.blind_structure.current_level,
            hand_phase=self.phase,
            action_history=list(self.action_log),
            legal_actions=actions,
        )

    def _apply_action(self, player: PlayerHandState, action: Action) -> None:
        """Apply a validated action to the game state."""
        at = action.action_type

        if at == ActionType.FOLD:
            player.is_folded = True

        elif at == ActionType.CHECK:
            pass  # nothing changes

        elif at == ActionType.CALL:
            amount_to_call = self.current_bet - player.chips_invested_this_round
            actual = player.invest(amount_to_call, self.table)

        elif at in (ActionType.BET, ActionType.RAISE):
            # amount is the total the player should have in this round
            additional = action.amount - player.chips_invested_this_round
            if additional > 0:
                actual = player.invest(additional, self.table)

            # Update current bet and min raise
            new_total = player.chips_invested_this_round
            if at == ActionType.BET:
                raise_size = new_total
            else:
                raise_size = new_total - self.current_bet

            # Only update min_raise if it's a full raise
            if raise_size >= self.min_raise:
                self.min_raise = raise_size
                self._last_raiser_seat = player.seat_index

            self.current_bet = new_total

        if action.is_all_in:
            player.is_all_in = True

        self.action_log.append(action)

        # Notify all players
        for p in self.players:
            p.player.notify_action(player.seat_index, action)

    def _reset_betting_round(self) -> None:
        """Reset per-round state for a new betting round."""
        self.current_bet = 0.0
        self.min_raise = self.table.blind_structure.current_level.big_blind
        self._last_raiser_seat = None
        for p in self.players:
            p.reset_round()

    # ------------------------------------------------------------------
    # Betting round execution
    # ------------------------------------------------------------------

    def _determine_first_actor(self, is_preflop: bool) -> int:
        """Return index into self.players for the first actor."""
        active = self.active_players()
        if not active:
            return 0

        if is_preflop:
            # UTG = first active player after BB
            # BB is the player with the highest blind investment
            blind_investments = {
                p.seat_index: p.chips_invested for p in self.players
            }
            # Find BB seat (highest blind poster)
            bb_seat = max(blind_investments, key=blind_investments.get)
            # Find first active seat after BB
            all_seats = [p.seat_index for p in self.players]
            bb_pos = all_seats.index(bb_seat)
            for i in range(1, len(all_seats) + 1):
                candidate_idx = (bb_pos + i) % len(all_seats)
                p = self.players[candidate_idx]
                if not p.is_folded and not p.is_all_in:
                    return candidate_idx
            return 0
        else:
            # Postflop: first active player left of button
            btn = self.table.button_position
            seat_list = [p.seat_index for p in self.players]
            # Walk clockwise from button+1
            for i in range(1, self.table.num_seats + 1):
                candidate_seat = (btn + i) % self.table.num_seats
                if candidate_seat in seat_list:
                    idx = seat_list.index(candidate_seat)
                    p = self.players[idx]
                    if not p.is_folded and not p.is_all_in:
                        return idx
            return 0

    def run_betting_round(self, is_preflop: bool = False) -> None:
        """
        Execute a complete betting round.

        The round ends when all active players have acted at least once
        AND the current bet has been matched by all, or all but one fold.
        """
        active = self.active_players()
        if len(active) <= 1:
            return

        num_players = len(self.players)
        first_idx = self._determine_first_actor(is_preflop)

        # Track who has had a chance to act
        has_acted: set[int] = set()
        current_idx = first_idx

        while True:
            # If no active players remain (all folded or all-in), stop
            if len(self.active_players()) <= 1:
                break
            if self.is_hand_over():
                break

            player = self.players[current_idx]

            # Skip folded, all-in players
            if player.is_folded or player.is_all_in:
                current_idx = (current_idx + 1) % num_players
                continue

            # Check if betting round is complete
            if player.seat_index in has_acted:
                # Everyone has acted and bet is matched
                all_matched = all(
                    p.chips_invested_this_round >= self.current_bet
                    or p.is_folded or p.is_all_in
                    for p in self.players
                )
                if all_matched:
                    break

            # Get action from player
            view = self._build_player_view(player)
            action = player.player.get_action(view)

            # Ensure seat is set correctly
            action = Action(
                action.action_type, player.seat_index,
                action.amount, action.is_all_in,
            )

            # Validate
            stack = self.table.seats[player.seat_index].stack
            valid, reason = validate_action(
                action, self.total_pot(), self.current_bet,
                player.chips_invested_this_round, stack,
                self.min_raise, player.is_folded, player.is_all_in,
            )
            if not valid:
                # Fall back to fold if invalid action
                action = Action(ActionType.FOLD, player.seat_index)

            # If a raise/bet, clear has_acted for reopening
            # (only if it's a full raise)
            old_bet = self.current_bet

            self._apply_action(player, action)
            has_acted.add(player.seat_index)

            if action.action_type in (ActionType.BET, ActionType.RAISE):
                new_bet = self.current_bet
                raise_size = new_bet - old_bet
                if raise_size >= self.min_raise or old_bet == 0:
                    # Full raise — reopen action for all except raiser
                    has_acted = {player.seat_index}

            # Next player
            current_idx = (current_idx + 1) % num_players

    # ------------------------------------------------------------------
    # Board dealing
    # ------------------------------------------------------------------

    def _deal_remaining_board(self) -> None:
        """Deal remaining community cards for all-in runout."""
        cards = list(self.board)
        if len(cards) < 3:
            flop = self.deck.deal_flop()
            cards.extend(flop)
            self.board = make_board(*cards)
            for p in self.players:
                p.player.notify_board(self.board)
        if len(cards) < 4:
            turn = self.deck.deal_turn_or_river()
            cards.append(turn)
            self.board = make_board(*cards)
            for p in self.players:
                p.player.notify_board(self.board)
        if len(cards) < 5:
            river = self.deck.deal_turn_or_river()
            cards.append(river)
            self.board = make_board(*cards)
            for p in self.players:
                p.player.notify_board(self.board)


# ---------------------------------------------------------------------------
# Hand runner — orchestrates a full hand
# ---------------------------------------------------------------------------

def run_hand(table: Table, deck: Deck) -> HandResult:
    """
    Run a single PLO hand to completion.

    Returns a HandResult with showdown results and net profit per seat.
    """
    state = HandState(table, deck)

    if len(state.players) < 2:
        raise ValueError("Need at least 2 players to run a hand")

    # --- Post blinds ---
    state.phase = HandPhase.POST_BLINDS
    blind_posts = table.post_blinds()
    for seat_idx, amount in blind_posts.items():
        player = state._get_player(seat_idx)
        if player:
            player.chips_invested += amount
            player.chips_invested_this_round += amount

    # Set current bet to big blind for preflop
    bb = table.blind_structure.current_level.big_blind
    state.current_bet = bb
    state.min_raise = bb

    # --- Deal hole cards ---
    state.phase = HandPhase.DEAL_HOLE_CARDS
    for player in state.players:
        player.hole_cards = deck.deal_plo_hand()
        player.player.notify_deal(player.hole_cards)

    # --- Preflop betting ---
    state.phase = HandPhase.PREFLOP_BETTING
    if not state.is_hand_over() and not state.is_all_in_runout():
        state.run_betting_round(is_preflop=True)

    # --- Flop ---
    if not state.is_hand_over():
        if state.is_all_in_runout():
            state._deal_remaining_board()
        else:
            state.phase = HandPhase.DEAL_FLOP
            flop = deck.deal_flop()
            state.board = flop
            for p in state.players:
                p.player.notify_board(state.board)

            state.phase = HandPhase.FLOP_BETTING
            state._reset_betting_round()
            if not state.is_all_in_runout():
                state.run_betting_round(is_preflop=False)

    # --- Turn ---
    if not state.is_hand_over() and len(state.board) < 4:
        if state.is_all_in_runout():
            state._deal_remaining_board()
        else:
            state.phase = HandPhase.DEAL_TURN
            turn = deck.deal_turn_or_river()
            state.board = make_board(*state.board, turn)
            for p in state.players:
                p.player.notify_board(state.board)

            state.phase = HandPhase.TURN_BETTING
            state._reset_betting_round()
            if not state.is_all_in_runout():
                state.run_betting_round(is_preflop=False)

    # --- River ---
    if not state.is_hand_over() and len(state.board) < 5:
        if state.is_all_in_runout():
            state._deal_remaining_board()
        else:
            state.phase = HandPhase.DEAL_RIVER
            river = deck.deal_turn_or_river()
            state.board = make_board(*state.board, river)
            for p in state.players:
                p.player.notify_board(state.board)

            state.phase = HandPhase.RIVER_BETTING
            state._reset_betting_round()
            if not state.is_all_in_runout():
                state.run_betting_round(is_preflop=False)

    # --- Showdown / Distribution ---
    state.phase = HandPhase.SHOWDOWN

    investments = {p.seat_index: p.chips_invested for p in state.players}

    if state.is_hand_over():
        # Everyone folded — last player standing wins
        winner = state.remaining_players()[0]
        total = sum(investments.values())
        net = {p.seat_index: -p.chips_invested for p in state.players}
        net[winner.seat_index] = total - winner.chips_invested
        # Credit the winner's stack
        table.seats[winner.seat_index].stack += total

        result = HandResult(
            showdown_results=[],
            net_profit={k: round(v, 2) for k, v in net.items()},
            went_to_showdown=False,
            winning_seat=winner.seat_index,
            hand_number=table.hand_number,
        )
    else:
        # Showdown
        state.phase = HandPhase.SHOWDOWN
        pots = calculate_pots(investments)
        folded = {p.seat_index for p in state.players if p.is_folded}
        hole_cards = {
            p.seat_index: p.hole_cards for p in state.players
            if p.hole_cards is not None
        }

        showdown_results = resolve_showdown(
            hole_cards, state.board, pots, folded,
            table.button_position,
        )
        net = distribute_pots(showdown_results, investments)

        # Apply to stacks
        for seat_idx, profit in net.items():
            table.seats[seat_idx].stack += investments[seat_idx] + profit

        result = HandResult(
            showdown_results=showdown_results,
            net_profit=net,
            went_to_showdown=True,
            winning_seat=None,
            hand_number=table.hand_number,
        )

    state.phase = HandPhase.HAND_COMPLETE

    # Notify players
    for p in state.players:
        p.player.notify_showdown(result)

    # Store action log and state on result for hand history
    result._action_log = state.action_log
    result._board = state.board
    result._hole_cards = {p.seat_index: p.hole_cards for p in state.players}
    result._deck = deck
    result._blind_posts = blind_posts
    result._player_states = state.players

    return result
