# AI Player Design

## Player Type Roadmap

| Player | Strategy | Status | Key Dependency |
|--------|----------|--------|----------------|
| RandomPlayer | Weighted random from legal actions | Complete | — |
| CallingStation | Always check/call | Complete | — |
| HeuristicPlayer | Rule-based using domain analysis | Complete | domain.py, ev.py, opponent_model.py |
| CFR Player | Offline-trained strategy lookup | Planned | game_tree.py, abstraction.py |
| RL Player | Neural net trained via self-play | Planned | abstraction.py, training harness |

All players implement `Player.get_action(view: PlayerView) -> Action`.

## Shared Infrastructure (planned)

### Hand Abstraction (`abstraction.py`)
PLO has ~270,725 starting hands. For CFR and RL to be tractable, similar hands must be grouped into buckets.

Planned abstractions:
- **PreflopAbstraction** — buckets from `StartingHandProfile.classify()` (category x suit structure, ~65 buckets)
- **PostflopAbstraction** — buckets from `HandProperties.analyze()` (made hand strength x draw type x board texture, ~100-200 buckets)
- **EquityBucketAbstraction** — equity vs uniform range mapped to percentile buckets (more expensive, more accurate)

### Bet Abstraction
Selects a subset from `legal_actions()` output (which already generates standard pot-fraction sizes). Reduces the continuous bet space to 3-5 discrete options per decision point.

## HeuristicPlayer Detail

### Preflop Tiers
- **Tier 0 (Premium):** Aces
- **Tier 1 (Strong):** High pairs, high rundowns, double-paired; double-suited medium rundowns
- **Tier 2 (Playable):** Medium pairs, medium rundowns, gapped rundowns, suited aces; suited low rundowns
- **Tier 3 (Trash):** Everything else

Style shifts: LAG promotes low pairs, low rundowns, double-suited danglers to tier 2. NIT demotes tier 2 to trash.

### Postflop Priority Chain
1. Nutted (nut straight+) -> value bet/raise
2. Very strong (top set+) -> value bet/raise
3. Strong (top two+) -> bet if checked to, call if facing bet
4. Strong draws (equity >= 25%) -> semi-bluff or call based on pot odds
5. Medium hands (top pair+) -> thin value bet sometimes, call small bets
6. Weak draws -> bluff or call if pot odds justify
7. Good bluff candidates -> bet based on style-dependent frequency and blocker quality
8. Trash -> check or fold

## CFR Player (planned)

### Training Pipeline
1. Build game tree for a specific spot (e.g., heads-up postflop, single-raised pot)
2. Apply hand abstraction to group ~270K hands into ~100-200 buckets
3. Apply bet abstraction to limit actions to 3-5 per node
4. Run External Sampling MCCFR until strategy converges
5. Save converged strategy as a `CFRBlueprint` file

### Online Play
- Load blueprint at construction
- On each decision: bucket hand, encode action history, look up strategy distribution, sample action
- Fall back to check/fold for unvisited information sets

## RL Player (planned)

### State Encoding (~60-80 dimensions)
- Hand features from StartingHandProfile / HandProperties
- Board texture from BoardTexture
- Pot/stack ratios (pot odds, SPR)
- Opponent stats from OpponentModel
- Phase one-hot

### Training
- Uses `Session.run_one_hand()` as the environment
- Reward = `net_profit` from HandResult
- Standard RL algorithm (policy gradient or DQN)
