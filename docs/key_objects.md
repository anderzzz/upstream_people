# Key Objects

## Foundation

### Card representation
Cards are ints 0-51. Rank = `card // 4` (0=2, 1=3, ..., 12=A). Suit = `card % 4` (0=clubs, 1=diamonds, 2=hearts, 3=spades).

### PLOHand
`tuple[int, int, int, int]` — sorted ascending. A player's four hole cards.

### Board
`tuple[int, ...]` — sorted ascending, 0-5 cards. The community cards.

### HandRank
`int` — higher is better. Bits 20-23 encode category (0=high card through 8=straight flush), bits 0-19 encode kickers for tiebreaking.

### Range
Dict mapping `PLOHand -> float` weight. Represents a probability distribution over hands a player might hold. Key methods: `remove_blockers()`, `normalize()`, `sample_hand()`, `filter()`.

## Domain Abstractions (`domain.py`)

### BoardTexture
Strategic classification of a 3-5 card board: `flush_draw` (rainbow/two-tone/monotone), `connectedness`, `pairedness`, `height`, plus detailed suit/rank counts and nut hand description.

### HandProperties
Analysis of a specific hand on a specific board. Contains:
- `made_hand: MadeHandStrength` — 18-level enum from NOTHING to STRAIGHT_FLUSH
- `draws: DrawType` — flag enum (nut flush draw, OESD, wrap, combo draw, etc.)
- `blocker_score: float` — 0-1 composite score of how well the hand blocks opponent nut hands
- `nut_rank: int` — how close to the nuts (1 = nuts)
- `is_good_bluff_candidate()` — heuristic combining weak made hand + good blockers + some equity

### StartingHandProfile
Preflop hand classification: `category` (13 types: ACES, HIGH_RUNDOWN, SUITED_ACE, TRASH, etc.), `suit_structure` (double-suited, single-suited, rainbow, etc.), `preflop_equity_estimate`.

## Game Simulation

### Action
Immutable. Fields: `action_type` (FOLD/CHECK/CALL/BET/RAISE), `player_seat`, `amount` (total chips put in this round), `is_all_in`.

### PlayerView
What a player can see when it's their turn. Frozen dataclass containing:
- `my_hole_cards`, `my_stack`, `my_chips_in_pot`
- `board`, `pot_total`, `current_bet`, `min_raise`, `pot_limit_max`
- `opponents: list[OpponentView]`
- `hand_phase`, `action_history`, `blind_level`, `button_position`
- `legal_actions: list[Action]` — pre-computed by the engine

### Player (ABC)
Abstract base with one required method:
```python
def get_action(self, view: PlayerView) -> Action
```
Optional notification callbacks: `notify_deal()`, `notify_action()`, `notify_board()`, `notify_showdown()`.

### HandResult
Outcome of a single hand: `showdown_results` (per-pot winners), `net_profit` (dict: seat -> chips won/lost), `went_to_showdown`, `winning_seat`.

### Table
Persistent across hands. Holds `seats` (each with a Player and stack), `blind_structure`, `button_position`, `hand_number`.

### Session
Runs multiple hands. Handles button advancement, blind escalation, player elimination (tournament), rebuys. Entry point: `run_one_hand() -> HandHistory` or `run() -> list[HandHistory]`.

## AI Players

### OpponentStats
Per-opponent accumulated statistics: `vpip`, `pfr`, `aggression_factor`, `fold_to_bet`, `cbet`. Returns sensible defaults when no data is available.

### OpponentModel
Container for `OpponentStats` across all opponents. Tracks stats via `observe_action(seat, action, board_len)`. Phase is inferred from board length.

### HeuristicPlayer
Rule-based player with configurable `style` (TAG/LAG/NIT). Decision flow:
- **Preflop:** `StartingHandProfile.classify()` assigns hand to a tier (premium/strong/playable/trash). Style shifts the tier boundaries.
- **Postflop:** `HandProperties.analyze()` drives a priority chain — nutted hands get value-bet, strong draws get semi-bluffed, bluff candidates get bet based on blocker quality and style-dependent frequency, trash gets folded.
