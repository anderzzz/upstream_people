"""Thin bridge between the API layer and plo_engine.

Keeps FastAPI routes clean — all engine interaction goes through here.
This will grow as we wire up real endpoints.
"""

from __future__ import annotations


class EngineBridge:
    """Wraps plo_engine objects for use by API routes."""

    def __init__(self):
        # Will hold session state, table, players, etc.
        pass

    def handle_message(self, msg: dict) -> dict:
        """Process a game action message. Placeholder."""
        action = msg.get("action", "unknown")
        return {
            "type": "ack",
            "action_received": action,
            "message": "Engine bridge not yet wired",
        }
