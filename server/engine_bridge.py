"""Bridge between the async WebSocket layer and the synchronous PLO engine.

Owns Session + WebSocketPlayer. Runs the engine in a background thread
and shuttles messages between the thread and the async handler.
"""

from __future__ import annotations

import asyncio
from typing import Callable, Awaitable

from plo_engine.player import RandomPlayer, CallingStation
from plo_engine.tournament import Session, SessionConfig, SessionMode
from plo_engine.table import BlindLevel, BlindStructure
from plo_engine.betting import Action, ActionType
from plo_engine.hand_history import HandHistory
from server.ws_player import WebSocketPlayer
from server.serializers import (
    serialize_hand_result, serialize_standings,
)


def _create_bots(bot_type: str, count: int) -> list:
    """Create AI opponents of the specified type."""
    bots = []
    for i in range(count):
        name = f"Bot-{i + 1}"
        if bot_type == "random":
            bots.append(RandomPlayer(name, seed=42 + i))
        elif bot_type == "calling":
            bots.append(CallingStation(name))
        elif bot_type == "heuristic":
            try:
                from plo_engine.players.heuristic_player import HeuristicPlayer
                bots.append(HeuristicPlayer(name, seed=42 + i))
            except ImportError:
                bots.append(RandomPlayer(name, seed=42 + i))
        else:
            bots.append(RandomPlayer(name, seed=42 + i))
    return bots


class EngineBridge:
    """Wraps plo_engine objects for use by the WebSocket route."""

    def __init__(self):
        self.session: Session | None = None
        self.ws_player: WebSocketPlayer | None = None
        self._player_names: dict[int, str] = {}

    def create_session(self, config: dict) -> dict:
        """
        Create a new game session from client config.

        config keys: opponents (int), bot_type (str), stack (float), blinds (str "SB/BB")
        """
        opponents = min(5, max(1, config.get("opponents", 2)))
        bot_type = config.get("bot_type", "random")
        stack = config.get("stack", 1000)
        blinds_str = config.get("blinds", "5/10")

        parts = blinds_str.split("/")
        sb, bb = float(parts[0]), float(parts[1])
        blind_structure = BlindStructure(
            levels=[BlindLevel(small_blind=sb, big_blind=bb, ante=0)]
        )

        self.ws_player = WebSocketPlayer("You")
        bots = _create_bots(bot_type, opponents)
        players = [self.ws_player] + bots

        session_config = SessionConfig(
            mode=SessionMode.CASH_GAME,
            num_seats=len(players),
            starting_stack=stack,
            blind_structure=blind_structure,
            master_seed=42,
        )
        self.session = Session(session_config, players)

        # Build name map
        self._player_names = {}
        for i, p in enumerate(players):
            self._player_names[i] = p.name

        # Build response
        player_infos = []
        for i, p in enumerate(players):
            player_infos.append({
                "seat": i,
                "name": p.name,
                "stack": stack,
                "is_human": i == 0,
            })

        return {
            "type": "session_started",
            "players": player_infos,
            "blinds": {"small_blind": sb, "big_blind": bb},
        }

    def make_hand_started_message(self) -> dict:
        """Snapshot of table state at hand start."""
        session = self.session
        table = session.table

        players = []
        for i, seat in enumerate(table.seats):
            if seat.is_occupied and seat.player is not None:
                players.append({
                    "seat": i,
                    "name": seat.player.name,
                    "stack": round(seat.stack, 2),
                })

        return {
            "type": "hand_started",
            "hand_number": session._hand_count + 1,
            "button": table.button_position,
            "your_seat": 0,
            "players": players,
        }

    async def run_one_hand(
        self,
        send: Callable[[dict], Awaitable[None]],
    ) -> HandHistory | None:
        """
        Run one hand in a background thread, concurrently draining
        outbound messages and sending them to the client.

        Returns the HandHistory, or None if disconnected.
        """
        ws_player = self.ws_player
        if ws_player is None or self.session is None:
            return None

        # Send hand_started before the engine thread begins
        await send(self.make_hand_started_message())

        history_container: list[HandHistory | None] = [None]
        error_container: list[Exception | None] = [None]

        def run_in_thread():
            try:
                history_container[0] = self.session.run_one_hand()
            except Exception as e:
                error_container[0] = e

        # Start engine thread
        engine_task = asyncio.get_event_loop().run_in_executor(None, run_in_thread)

        # Drain outbound messages while engine runs
        try:
            while not engine_task.done():
                messages = ws_player.drain_messages()
                for msg in messages:
                    # Enrich action_performed with player name
                    if msg["type"] == "action_performed":
                        seat = msg.get("seat")
                        if seat is not None:
                            msg["player_name"] = self._player_names.get(seat, f"Seat {seat}")
                    await send(msg)
                await asyncio.sleep(0.05)

            # Wait for thread to finish
            await engine_task

            # Drain any remaining messages
            for msg in ws_player.drain_messages():
                if msg["type"] == "action_performed":
                    seat = msg.get("seat")
                    if seat is not None:
                        msg["player_name"] = self._player_names.get(seat, f"Seat {seat}")
                await send(msg)

        except Exception:
            ws_player.signal_disconnect()
            try:
                await engine_task
            except Exception:
                pass
            return None

        if error_container[0] is not None:
            raise error_container[0]

        return history_container[0]

    def resolve_action(self, msg: dict, last_view: dict) -> Action:
        """
        Map a client action message to an engine Action.

        msg: {"action": "fold|check|call|raise|bet", "amount": optional float}
        last_view: the serialized PlayerView from the most recent action_request
        """
        action_str = msg.get("action", "fold").lower()
        amount = msg.get("amount")
        legal_actions = last_view.get("legal_actions", [])
        seat = last_view.get("my_seat", 0)

        # Map string to ActionType
        type_map = {
            "fold": ActionType.FOLD,
            "check": ActionType.CHECK,
            "call": ActionType.CALL,
            "bet": ActionType.BET,
            "raise": ActionType.RAISE,
        }

        target_type = type_map.get(action_str, ActionType.FOLD)

        # Find exact match in legal actions
        for la in legal_actions:
            la_type = ActionType[la["action_type"].upper()]
            if la_type == target_type:
                if target_type in (ActionType.FOLD, ActionType.CHECK, ActionType.CALL):
                    return Action(la_type, seat, la["amount"], la["is_all_in"])
                elif amount is not None:
                    # For raise/bet with amount — find closest legal action
                    pass
                else:
                    # No amount specified — use first matching action
                    return Action(la_type, seat, la["amount"], la["is_all_in"])

        # For raise/bet with amount, find closest legal match
        if target_type in (ActionType.BET, ActionType.RAISE) and amount is not None:
            candidates = [
                la for la in legal_actions
                if ActionType[la["action_type"].upper()] == target_type
            ]
            if candidates:
                # Find closest by amount
                best = min(candidates, key=lambda la: abs(la["amount"] - amount))
                return Action(target_type, seat, best["amount"], best["is_all_in"])

        # Fallback: fold
        return Action(ActionType.FOLD, seat)

    def should_stop(self) -> bool:
        """Check if the session should end."""
        if self.session is None:
            return True
        return self.session._should_stop()

    def get_standings(self) -> list[dict]:
        """Get current standings."""
        if self.session is None:
            return []
        return serialize_standings(self.session.standings())
