# Architecture

## Layered Design

Each layer depends only on layers below it.

```
Layer 3:  Game Tree / CFR Solver          [stubs]
Layer 2:  EV & Decision Engine            ev.py
Layer 1:  Equity Calculation              equity.py
Layer 0.5: Domain Abstractions            domain.py
Layer 0:  Hand Evaluation                 hand_evaluator.py, hand_evaluator_jax.py
Foundation: Types                         types.py

Game Simulation (orthogonal):
  hand_state.py, betting.py, table.py, player.py,
  showdown.py, tournament.py, deck.py, hand_history.py

AI Players (consume all layers):
  players/heuristic_player.py, opponent_model.py

CLI (top-level, outside plo_engine):
  cli/app.py, cli/display.py, cli/input_handler.py
```

## Module Dependency Graph

```
types.py
  <- hand_evaluator.py
      <- hand_evaluator_jax.py  (JAX mirror of hand_evaluator)
      <- domain.py              (BoardTexture, HandProperties, StartingHandProfile)
          <- equity.py          (hand vs range, range vs range)
              <- ev.py          (pot odds, action EV)

betting.py                      (Action, ActionType, HandPhase, pot-limit rules, side pots)
  <- table.py                   (Table, Seat, BlindStructure)
  <- player.py                  (Player ABC, PlayerView, HumanPlayer, RandomPlayer)
  <- hand_state.py              (HandState, run_hand — orchestrates a single hand)
  <- showdown.py                (resolve_showdown, HandResult)
  <- tournament.py              (Session — runs multiple hands)
  <- hand_history.py            (HandHistory — recording and replay)

deck.py                         (Deck with JAX PRNG)

opponent_model.py               (OpponentModel, OpponentStats)
players/heuristic_player.py     (HeuristicPlayer — uses domain.py + ev.py + opponent_model)
```

## Key Design Decisions

**Cards are ints.** All computation uses raw ints 0-51. The `Card` class exists only for human-facing display and parsing. This keeps the hot paths simple and JAX-compatible.

**Player ABC is the integration point.** Every player type (human, random, heuristic, future CFR/RL) implements `Player.get_action(view: PlayerView) -> Action`. The game simulation never needs to know what kind of player it's dealing with.

**Game simulation is stateless per hand.** `Table` persists across hands (stacks, button, blinds). `HandState` is created fresh for each hand by `run_hand()`. This makes hand execution deterministic given a `Table` and `Deck`.

**Domain analysis as shared vocabulary.** `domain.py` provides poker-meaningful abstractions (board texture, hand strength, draw types, blocker scores) that are used by the heuristic player, will be used for hand bucketing in CFR, and serve as feature inputs for RL.
