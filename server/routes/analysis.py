"""Analysis endpoints — equity, EV, hand properties."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


# --- Request / Response schemas (will grow) ---

class EquityRequest(BaseModel):
    hand: list[str]       # e.g. ["As", "Kh", "Qd", "Jc"]
    board: list[str]      # e.g. ["Td", "9s", "2h"] or []
    villain_range: str    # range notation — TBD


class EquityResponse(BaseModel):
    equity: float
    win: float
    tie: float
    samples: int


class HandInfoRequest(BaseModel):
    hand: list[str]
    board: list[str]


# --- Routes ---

@router.post("/equity", response_model=EquityResponse)
async def compute_equity(req: EquityRequest):
    """Compute equity of a hand vs a range on a board."""
    # TODO: wire to plo_engine.equity via EngineBridge
    return EquityResponse(equity=0.0, win=0.0, tie=0.0, samples=0)


@router.post("/hand-properties")
async def hand_properties(req: HandInfoRequest):
    """Analyze hand properties (made hand, draws, blockers)."""
    # TODO: wire to plo_engine.domain
    return {"status": "stub"}


@router.get("/ping")
async def ping():
    return {"status": "ok"}
