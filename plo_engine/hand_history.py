"""Recording and replaying hands."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from plo_engine.types import PLOHand, Board, cards_to_str, card_to_str
from plo_engine.betting import Action, ActionType, HandPhase
from plo_engine.showdown import HandResult


@dataclass
class HandHistory:
    """
    Complete record of a single hand.

    Contains enough information to replay the hand exactly
    and to analyze any decision point after the fact.
    """
    hand_number: int
    timestamp: str                          # ISO format
    table_config: dict                      # seats, blinds, button, stacks at start

    # Cards
    deck_seed: int | None                   # for exact reproducibility
    hole_cards: dict[int, PLOHand]          # seat -> hole cards
    board_cards: Board                      # final board (up to 5 cards)
    burn_cards: list[int]                   # burned cards in deal order

    # Action sequence
    actions: list[Action]                   # in chronological order
    blind_posts: dict[int, float]           # seat -> blind/ante posted

    # Result
    result: HandResult
    final_stacks: dict[int, float]          # seat -> stack after hand

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dict."""
        return {
            "hand_number": self.hand_number,
            "timestamp": self.timestamp,
            "table_config": self.table_config,
            "deck_seed": self.deck_seed,
            "hole_cards": {
                str(k): list(v) for k, v in self.hole_cards.items()
            },
            "board_cards": list(self.board_cards),
            "burn_cards": self.burn_cards,
            "actions": [
                {
                    "type": a.action_type.name,
                    "seat": a.player_seat,
                    "amount": a.amount,
                    "is_all_in": a.is_all_in,
                }
                for a in self.actions
            ],
            "blind_posts": {str(k): v for k, v in self.blind_posts.items()},
            "net_profit": {
                str(k): v for k, v in self.result.net_profit.items()
            },
            "went_to_showdown": self.result.went_to_showdown,
            "winning_seat": self.result.winning_seat,
            "final_stacks": {str(k): v for k, v in self.final_stacks.items()},
        }

    @classmethod
    def from_dict(cls, d: dict) -> HandHistory:
        """Deserialize from dict."""
        actions = [
            Action(
                action_type=ActionType[a["type"]],
                player_seat=a["seat"],
                amount=a["amount"],
                is_all_in=a["is_all_in"],
            )
            for a in d["actions"]
        ]
        hole_cards = {
            int(k): tuple(v) for k, v in d["hole_cards"].items()
        }
        result = HandResult(
            showdown_results=[],
            net_profit={int(k): v for k, v in d["net_profit"].items()},
            went_to_showdown=d["went_to_showdown"],
            winning_seat=d["winning_seat"],
            hand_number=d["hand_number"],
        )
        return cls(
            hand_number=d["hand_number"],
            timestamp=d["timestamp"],
            table_config=d["table_config"],
            deck_seed=d.get("deck_seed"),
            hole_cards=hole_cards,
            board_cards=tuple(d["board_cards"]),
            burn_cards=d.get("burn_cards", []),
            actions=actions,
            blind_posts={int(k): v for k, v in d["blind_posts"].items()},
            result=result,
            final_stacks={int(k): v for k, v in d["final_stacks"].items()},
        )

    def describe(self) -> str:
        """Human-readable summary in standard hand history format."""
        lines = []
        tc = self.table_config
        lines.append(
            f"Hand #{self.hand_number} — "
            f"{tc.get('blind_level', 'unknown blinds')} — "
            f"{self.timestamp}"
        )
        lines.append(f"Button: Seat {tc.get('button', '?')}")
        lines.append("")

        # Stacks
        for seat_str, stack in sorted(tc.get("stacks", {}).items()):
            name = tc.get("names", {}).get(str(seat_str), f"Seat {seat_str}")
            lines.append(f"Seat {seat_str}: {name} ({stack:.0f})")
        lines.append("")

        # Blinds
        for seat, amount in self.blind_posts.items():
            lines.append(f"Seat {seat} posts {amount:.0f}")
        lines.append("")

        # Hole cards
        lines.append("*** HOLE CARDS ***")
        for seat, cards in sorted(self.hole_cards.items()):
            lines.append(f"Seat {seat}: [{cards_to_str(cards)}]")
        lines.append("")

        # Actions by phase
        phase_names = {
            "PREFLOP": "PREFLOP",
            "FLOP": "FLOP",
            "TURN": "TURN",
            "RIVER": "RIVER",
        }
        # Group actions (simple heuristic: board cards divide phases)
        lines.append("*** ACTIONS ***")
        for action in self.actions:
            lines.append(f"  {action.describe()}")
        lines.append("")

        # Board
        if self.board_cards:
            lines.append(f"*** BOARD [{cards_to_str(self.board_cards)}] ***")
            lines.append("")

        # Results
        lines.append("*** RESULTS ***")
        if self.result.went_to_showdown:
            lines.append("Went to showdown")
        else:
            lines.append(
                f"Seat {self.result.winning_seat} wins without showdown"
            )
        for seat, profit in sorted(self.result.net_profit.items()):
            sign = "+" if profit > 0 else ""
            lines.append(f"Seat {seat}: {sign}{profit:.0f}")

        return "\n".join(lines)


def build_hand_history(
    table_config: dict,
    result: HandResult,
    final_stacks: dict[int, float],
    deck_seed: int | None = None,
) -> HandHistory:
    """
    Build a HandHistory from the result of run_hand.

    Extracts stored data from the HandResult's internal attributes
    (set by run_hand).
    """
    action_log = getattr(result, "_action_log", [])
    board = getattr(result, "_board", ())
    hole_cards = getattr(result, "_hole_cards", {})
    deck = getattr(result, "_deck", None)
    blind_posts = getattr(result, "_blind_posts", {})
    burns = deck.burns if deck else []

    return HandHistory(
        hand_number=result.hand_number,
        timestamp=datetime.now(timezone.utc).isoformat(),
        table_config=table_config,
        deck_seed=deck_seed,
        hole_cards=hole_cards,
        board_cards=board,
        burn_cards=burns,
        actions=action_log,
        blind_posts=blind_posts,
        result=result,
        final_stacks=final_stacks,
    )
