# Upstream People

Pot-Limit Omaha poker analysis engine with a web frontend. Combines game-theoretically sound computation with human-comprehensible strategic concepts to help players develop stronger PLO strategy.

## Architecture

### Engine (`plo_engine/`)

Layered design — each layer depends only on layers below it:

- **Foundation** (`types.py`): Card ints 0-51, PLOHand, Board, HandRank, Range
- **Layer 0** (`hand_evaluator.py`, `hand_evaluator_jax.py`): 5-card evaluation, PLO best-hand extraction (exactly 2 hole + 3 board)
- **Layer 0.5** (`domain.py`): Strategic vocabulary — BoardTexture, HandProperties, StartingHandProfile, RangeProfile
- **Layer 1** (`equity.py`): Equity calculation — exhaustive enumeration and Monte Carlo
- **Layer 2** (`ev.py`): Pot odds, implied odds, action EV
- **Layer 3** (`game_tree.py`, `cfr.py`): Game tree and CFR solver — stubs only
- **Game Simulation** (`hand_state.py`, `betting.py`, `table.py`, `player.py`, `showdown.py`, `tournament.py`, `deck.py`, `hand_history.py`): Full hand execution, multi-hand sessions, hand history recording
- **AI Players** (`players/heuristic_player.py`): Rule-based player using domain analysis (TAG/LAG/NIT styles)
- **Opponent Model** (`opponent_model.py`): Per-opponent stat tracking (VPIP, PFR, aggression, fold-to-bet, c-bet)

### API (`server/`)

FastAPI backend exposing the engine over HTTP/WebSocket:

- `main.py` — App setup, CORS, router mounting
- `engine_bridge.py` — Thin adapter between API routes and plo_engine
- `routes/game.py` — WebSocket endpoint (`/game/ws`) for live play sessions
- `routes/analysis.py` — REST endpoints for equity calculation and hand analysis

### Frontend (`frontend/`)

React + TypeScript SPA (Vite, PixiJS for rendering, D3 for data viz):

- Pages: Lobby, TableRoom, RangeRoom, StrategyMap, Lab
- Shared components: Card, Layout

### CLI (`cli/`)

Interactive terminal frontend for playing against AI opponents.

## Tech stack

- **Engine**: Python 3.11+, JAX for numerical computation
- **API**: FastAPI, uvicorn, websockets
- **Frontend**: React 19, TypeScript, Vite, PixiJS 8, D3 7, react-router-dom
- **Tests**: pytest

## Working with the code

- Run tests: `python -m pytest tests/ -v`
- Run API server: `uvicorn server.main:app --reload`
- Run frontend dev: `cd frontend && npm run dev`
- Run example: `PYTHONPATH=. python examples/basic_analysis.py`
- Run benchmarks: `PYTHONPATH=. python benchmarks/bench_evaluator.py`
- Play CLI: `PYTHONPATH=. python -m cli.app --bot-type heuristic --opponents 2`

## Conventions

- Correctness first, performance second. The pure Python evaluator is the reference — JAX must match it exactly.
- Cards are always raw ints (0-51) in computation. The `Card` class is only for human interaction.
- Hands and boards are sorted ascending tuples.
- HandRank is a single int: higher = better. Bits 20-23 encode category (0=high card..8=straight flush), bits 0-19 encode kickers.
- JAX code must be branchless inside `jit` — use `jnp.where`, not Python `if/else` on array values.
- Plain Python for anything with dynamic/recursive structure (game tree, parsing, display).
- All AI players implement `Player.get_action(view: PlayerView) -> Action` from `player.py`. New player types go in `plo_engine/players/`.
- Opponent model infers hand phase from board length (0=preflop, 3=flop, 4=turn, 5=river) to avoid changing the `Player` ABC signature.
- API routes stay thin — game logic lives in plo_engine, wired through `engine_bridge.py`.

## What's next

The spec (`plo_spec.md`) covers the full vision. Major remaining work:
- Wire API endpoints to real engine logic (equity, hand properties, game sessions)
- Build out frontend pages (table rendering, range editor, strategy visualization)
- Hand abstraction layer (`abstraction.py`) — bucket ~270K PLO hands for tractable CFR/RL
- Game tree implementation with proper action tracking and state transitions
- CFR solver (External Sampling MCCFR, card abstraction, bet size discretization)
- RL player with state encoding from domain features, trained via Session loop
- PLO range notation DSL for human-readable range construction
