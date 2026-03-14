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


# ---------------------------------------------------------------------------
# Analysis serializers
# ---------------------------------------------------------------------------

def serialize_board_texture(bt) -> dict:
    """Convert a BoardTexture to a JSON-serializable dict."""
    from plo_engine.types import cards_to_str, SUIT_NAMES
    return {
        "board": cards_to_str(bt.board),
        "flush_draw": bt.flush_draw.name,
        "connectedness": bt.connectedness.name,
        "pairedness": bt.pairedness.name,
        "height": bt.height.name,
        "has_ace": bt.has_ace,
        "num_broadway": bt.num_broadway,
        "straight_possible": bt.straight_possible,
        "flush_possible": bt.flush_possible,
        "flush_suit": SUIT_NAMES[bt.flush_suit] if bt.flush_suit is not None else None,
        "nut_hand_description": bt.nut_hand_description,
        "description": bt.describe(),
    }


def serialize_hand_properties(hp) -> dict:
    """Convert a HandProperties to a JSON-serializable dict."""
    from plo_engine.domain import DrawType
    draw_names = [d.name for d in DrawType
                  if d in hp.draws and d != DrawType.NONE]
    return {
        "hand": cards_to_str(hp.hand),
        "board": cards_to_str(hp.board),
        "board_texture": serialize_board_texture(hp.board_texture),
        "hand_rank": hp.hand_rank,
        "made_hand": hp.made_hand.name,
        "is_nutted": hp.is_nutted,
        "draws": draw_names,
        "nut_draw_outs": hp.nut_draw_outs,
        "total_outs": hp.total_outs,
        "draw_equity_estimate": round(hp.draw_equity_estimate, 4),
        "blocks_nut_flush": hp.blocks_nut_flush,
        "blocks_second_nut_flush": hp.blocks_second_nut_flush,
        "blocks_nut_straight": hp.blocks_nut_straight,
        "blocks_sets": hp.blocks_sets,
        "blocker_score": round(hp.blocker_score, 4),
        "nut_rank": hp.nut_rank,
        "distance_to_nuts": hp.distance_to_nuts,
        "description": hp.describe(),
        "is_good_bluff_candidate": hp.is_good_bluff_candidate(),
    }


def serialize_starting_hand_profile(shp) -> dict:
    """Convert a StartingHandProfile to a JSON-serializable dict."""
    return {
        "hand": cards_to_str(shp.hand),
        "category": shp.category.name,
        "suit_structure": shp.suit_structure.name,
        "is_connected": shp.is_connected,
        "gap_count": shp.gap_count,
        "highest_pair": shp.highest_pair,
        "num_pairs": shp.num_pairs,
        "has_ace": shp.has_ace,
        "has_suited_ace": shp.has_suited_ace,
        "suits_description": shp.suits_description,
        "preflop_equity_estimate": shp.preflop_equity_estimate,
        "description": shp.describe(),
    }


def serialize_equity_result(er) -> dict:
    """Convert an EquityResult to a JSON-serializable dict."""
    return {
        "equity": round(er.equity, 4),
        "win": round(er.win_pct, 4),
        "tie": round(er.tie_pct, 4),
        "loss": round(er.loss_pct, 4),
        "samples": er.sample_count,
        "confidence_interval": (
            [round(er.confidence_interval[0], 4),
             round(er.confidence_interval[1], 4)]
            if er.confidence_interval else None
        ),
    }


def serialize_action_ev(aev) -> dict:
    """Convert an ActionEV to a JSON-serializable dict."""
    return {
        "action": aev.action,
        "ev": round(aev.ev, 4),
        "ev_bb": round(aev.ev_bb, 4),
    }
