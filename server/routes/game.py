"""Game room — WebSocket endpoint for live PLO play."""

from __future__ import annotations

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from server.engine_bridge import EngineBridge

router = APIRouter()


@router.websocket("/ws")
async def game_session(websocket: WebSocket):
    """WebSocket connection for a single game session.

    Protocol (sketch — will evolve):
        Client sends: {"action": "fold|call|raise", "amount": optional float}
        Server sends: {"type": "state|result|error", ...}
    """
    await websocket.accept()
    bridge = EngineBridge()

    try:
        # Send initial game state once session setup is defined
        await websocket.send_json({"type": "connected", "message": "Table open"})

        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)

            # Route message to engine — placeholder for real game loop
            response = bridge.handle_message(msg)
            await websocket.send_json(response)

    except WebSocketDisconnect:
        pass
