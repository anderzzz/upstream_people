"""Game room — WebSocket endpoint for live PLO play."""

from __future__ import annotations

import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from server.engine_bridge import EngineBridge
from server.serializers import serialize_hand_result

router = APIRouter()


@router.websocket("/ws")
async def game_session(websocket: WebSocket):
    """
    WebSocket connection for a single game session.

    State machine:
      1. Accept connection, send "connected"
      2. Wait for "start_session" → create session
      3. Hand loop: run_one_hand, handle action_request/player_action, send results
      4. Between hands: wait for "next_hand" or "quit"
    """
    await websocket.accept()
    bridge = EngineBridge()

    # Track the last action_request view for resolving player actions
    pending_view: dict | None = None

    async def send(msg: dict) -> None:
        """Send a message to the client, tracking action_request views."""
        nonlocal pending_view
        if msg["type"] == "action_request":
            pending_view = msg["view"]
        await websocket.send_json(msg)

    try:
        await websocket.send_json({"type": "connected"})

        # ── Wait for start_session ──
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)

            if msg.get("type") == "start_session":
                config = msg.get("config", {})
                response = bridge.create_session(config)
                await websocket.send_json(response)
                break
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": "Expected start_session message",
                })

        # ── Hand loop ──
        while not bridge.should_stop():
            pending_view = None

            # Start listening for player_action messages concurrently
            # with the engine thread
            action_listener = asyncio.create_task(
                _action_listener(websocket, bridge, lambda: pending_view)
            )

            try:
                history = await bridge.run_one_hand(send)
            except Exception as e:
                action_listener.cancel()
                await websocket.send_json({
                    "type": "error",
                    "message": f"Engine error: {e}",
                })
                break

            action_listener.cancel()

            if history is None:
                break

            # Send hand result and standings
            await websocket.send_json({
                "type": "hand_result",
                "result": serialize_hand_result(history),
            })
            await websocket.send_json({
                "type": "standings",
                "standings": bridge.get_standings(),
            })

            if bridge.should_stop():
                await websocket.send_json({
                    "type": "session_over",
                    "reason": "Session complete",
                })
                break

            # Wait for next_hand or quit
            while True:
                raw = await websocket.receive_text()
                msg = json.loads(raw)
                if msg.get("type") == "next_hand":
                    break
                elif msg.get("type") == "quit":
                    await websocket.send_json({
                        "type": "session_over",
                        "reason": "Player quit",
                    })
                    return
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Expected next_hand or quit",
                    })

    except WebSocketDisconnect:
        if bridge.ws_player:
            bridge.ws_player.signal_disconnect()


async def _action_listener(
    websocket: WebSocket,
    bridge: EngineBridge,
    get_pending_view,
):
    """
    Continuously listen for player_action messages and deliver them
    to the engine thread via ws_player.submit_action().
    """
    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)

            if msg.get("type") == "player_action":
                view = get_pending_view()
                if view is None:
                    await websocket.send_json({
                        "type": "error",
                        "message": "No action requested",
                    })
                    continue

                action = bridge.resolve_action(msg, view)
                bridge.ws_player.submit_action(action)
            # Ignore other message types during hand
    except asyncio.CancelledError:
        pass
    except WebSocketDisconnect:
        if bridge.ws_player:
            bridge.ws_player.signal_disconnect()
