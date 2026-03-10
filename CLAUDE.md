# PLO Engine

Pot-Limit Omaha poker analysis engine. The goal is a system that combines game-theoretically sound computation with human-comprehensible strategic concepts to help players develop stronger PLO strategy.

## Architecture

Layered design — each layer depends only on layers below it:

- **Foundation** (`types.py`): Card ints 0-51, PLOHand, Board, HandRank, Range
- **Layer 0** (`hand_evaluator.py`, `hand_evaluator_jax.py`): 5-card evaluation, PLO best-hand extraction (exactly 2 hole + 3 board)
- **Layer 0.5** (`domain.py`): Strategic vocabulary — BoardTexture, HandProperties, StartingHandProfile, RangeProfile
- **Layer 1** (`equity.py`): Equity calculation — exhaustive enumeration and Monte Carlo
- **Layer 2** (`ev.py`): Pot odds, implied odds, action EV
- **Layer 3** (`game_tree.py`, `cfr.py`): Game tree and CFR solver — stubs only

## Tech stack

Python 3.11+, JAX for numerical computation. No other runtime dependencies. pytest for tests.

## Working with the code

- Run tests: `python -m pytest tests/ -v`
- Run example: `PYTHONPATH=. python examples/basic_analysis.py`
- Run benchmarks: `PYTHONPATH=. python benchmarks/bench_evaluator.py`

## Conventions

- Correctness first, performance second. The pure Python evaluator is the reference — JAX must match it exactly.
- Cards are always raw ints (0-51) in computation. The `Card` class is only for human interaction.
- Hands and boards are sorted ascending tuples.
- HandRank is a single int: higher = better. Bits 20-23 encode category (0=high card..8=straight flush), bits 0-19 encode kickers.
- JAX code must be branchless inside `jit` — use `jnp.where`, not Python `if/else` on array values.
- Plain Python for anything with dynamic/recursive structure (game tree, parsing, display).

## What's next

The spec (`plo_spec.md`) covers the full vision. Major remaining work:
- Game tree implementation with proper action tracking and state transitions
- CFR solver (variant selection, card abstraction, bet size discretization)
- Lookup-table evaluator if JAX batch performance proves insufficient
- PLO range notation DSL for human-readable range construction
- GPU acceleration for large-scale computation
