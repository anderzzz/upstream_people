"""Pure functions converting engine dataclasses to JSON-safe dicts."""

from __future__ import annotations

from plo_engine.types import card_to_str, cards_to_str
from plo_engine.betting import Action, ActionType, HandPhase
from plo_engine.player import PlayerView, OpponentView
from plo_engine.table import BlindLevel
from plo_engine.hand_history import HandHistory


def serialize_player_view(view: PlayerView) -> dict:
    """Convert a PlayerView to a JSON-serializable dict."""
    return {
        "my_seat": view.my_seat,
        "my_hole_cards": [card_to_str(c) for c in view.my_hole_cards],
        "my_stack": round(view.my_stack, 2),
        "my_chips_in_pot": round(view.my_chips_in_pot, 2),
        "board": [card_to_str(c) for c in view.board],
        "pot_total": round(view.pot_total, 2),
        "current_bet": round(view.current_bet, 2),
        "min_raise": round(view.min_raise, 2),
        "pot_limit_max": round(view.pot_limit_max, 2),
        "opponents": [_serialize_opponent(o) for o in view.opponents],
        "button_position": view.button_position,
        "blind_level": _serialize_blind_level(view.blind_level),
        "hand_phase": view.hand_phase.name,
        "legal_actions": [serialize_action(a) for a in view.legal_actions],
    }


def _serialize_opponent(opp: OpponentView) -> dict:
    return {
        "seat": opp.seat,
        "stack": round(opp.stack, 2),
        "chips_in_pot": round(opp.chips_in_pot, 2),
        "is_folded": opp.is_folded,
        "is_all_in": opp.is_all_in,
        "name": opp.name,
        "hole_cards": [card_to_str(c) for c in opp.hole_cards] if opp.hole_cards else None,
    }


def _serialize_blind_level(bl: BlindLevel) -> dict:
    return {
        "small_blind": bl.small_blind,
        "big_blind": bl.big_blind,
        "ante": bl.ante,
    }


def serialize_action(action: Action) -> dict:
    """Convert an Action to a JSON-serializable dict."""
    return {
        "action_type": action.action_type.name.lower(),
        "player_seat": action.player_seat,
        "amount": round(action.amount, 2),
        "is_all_in": action.is_all_in,
    }


def serialize_hand_result(history: HandHistory) -> dict:
    """Convert a HandHistory's result info to a JSON-serializable dict."""
    result = history.result
    return {
        "hand_number": history.hand_number,
        "net_profit": {str(k): round(v, 2) for k, v in result.net_profit.items()},
        "went_to_showdown": result.went_to_showdown,
        "winning_seat": result.winning_seat,
        "board": [card_to_str(c) for c in history.board_cards] if history.board_cards else [],
        "showdown_hands": {
            str(seat): [card_to_str(c) for c in cards]
            for seat, cards in history.hole_cards.items()
        } if result.went_to_showdown else {},
    }


def serialize_standings(standings: list[tuple[str, float]]) -> list[dict]:
    """Convert standings list to JSON-serializable format."""
    return [
        {"name": name, "stack": round(stack, 2)}
        for name, stack in standings
    ]
