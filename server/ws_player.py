"""WebSocketPlayer — bridges the synchronous Player interface with async WebSocket."""

from __future__ import annotations

import queue
import time

from plo_engine.player import Player, PlayerView
from plo_engine.betting import Action, ActionType
from plo_engine.types import PLOHand, Board, card_to_str
from server.serializers import serialize_player_view, serialize_action


class WebSocketPlayer(Player):
    """
    A Player whose get_action() blocks until the WebSocket handler delivers an action.

    Outbound messages (notifications to the frontend) are pushed to a thread-safe queue
    that the async handler drains and sends over the WebSocket.
    """

    def __init__(self, name: str = "You"):
        super().__init__(name)
        self._action_queue: queue.Queue[Action | None] = queue.Queue()
        self._outbound: queue.Queue[dict] = queue.Queue()
        self._disconnected = False

    # ----- Player interface (called from engine thread) -----

    def get_action(self, view: PlayerView) -> Action:
        """Block until the WebSocket handler provides an action."""
        self._outbound.put({
            "type": "action_request",
            "view": serialize_player_view(view),
        })

        try:
            action = self._action_queue.get(timeout=120)
        except queue.Empty:
            # Timeout — fold to avoid hanging forever
            for a in view.legal_actions:
                if a.action_type == ActionType.FOLD:
                    return a
            return view.legal_actions[0]

        if action is None:
            # Disconnect signal — fold
            for a in view.legal_actions:
                if a.action_type == ActionType.FOLD:
                    return a
            return view.legal_actions[0]

        return action

    def notify_deal(self, hole_cards: PLOHand) -> None:
        self._outbound.put({
            "type": "hole_cards",
            "cards": [card_to_str(c) for c in hole_cards],
        })

    def notify_action(self, seat: int, action: Action) -> None:
        self._outbound.put({
            "type": "action_performed",
            "seat": seat,
            "player_name": "",  # filled in by bridge if needed
            "action": action.action_type.name.lower(),
            "amount": round(action.amount, 2),
            "is_all_in": action.is_all_in,
        })
        # Small delay so frontend can animate bot actions
        time.sleep(0.15)

    def notify_board(self, board: Board) -> None:
        phase_map = {3: "FLOP", 4: "TURN", 5: "RIVER"}
        self._outbound.put({
            "type": "board_dealt",
            "board": [card_to_str(c) for c in board],
            "phase": phase_map.get(len(board), "UNKNOWN"),
        })

    def notify_showdown(self, result: object) -> None:
        # Hand result is sent separately by the bridge
        pass

    # ----- Async-side interface (called from WebSocket handler) -----

    def submit_action(self, action: Action) -> None:
        """Deliver an action from the WebSocket handler to unblock get_action()."""
        self._action_queue.put(action)

    def signal_disconnect(self) -> None:
        """Signal that the WebSocket has disconnected."""
        self._disconnected = True
        self._action_queue.put(None)

    def drain_messages(self) -> list[dict]:
        """Drain all pending outbound messages (called from async side)."""
        messages = []
        while True:
            try:
                messages.append(self._outbound.get_nowait())
            except queue.Empty:
                break
        return messages
