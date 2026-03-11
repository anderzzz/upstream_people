"""Rule-based PLO player using domain analysis for decisions."""

from __future__ import annotations

import random as pyrandom

from plo_engine.betting import Action, ActionType, HandPhase
from plo_engine.domain import (
    BoardTexture,
    DrawType,
    HandProperties,
    MadeHandStrength,
    StartingHandCategory,
    StartingHandProfile,
    SuitStructure,
)
from plo_engine.ev import pot_odds
from plo_engine.opponent_model import OpponentModel
from plo_engine.player import Player, PlayerView
from plo_engine.types import Board, PLOHand


class HeuristicPlayer(Player):
    """
    A rule-based PLO player that uses domain analysis to make decisions.

    Uses StartingHandProfile for preflop decisions and HandProperties
    for postflop decisions. Considers pot odds, draw equity, blocker
    quality, and opponent tendencies.

    style controls aggression and hand selection thresholds:
      - TAG: tight-aggressive (default) — selective preflop, aggressive postflop
      - LAG: loose-aggressive — wider preflop range, more bluffs
      - NIT: very tight — only premium hands, rarely bluffs
    """

    def __init__(self, name: str, style: str = "TAG", seed: int | None = None):
        super().__init__(name)
        self._style = style.upper()
        self._rng = pyrandom.Random(seed)
        self._opponent_model = OpponentModel()
        self._my_cards: PLOHand | None = None
        self._board: Board = ()

    def notify_deal(self, hole_cards: PLOHand) -> None:
        self._my_cards = hole_cards
        self._board = ()
        self._opponent_model.new_hand()

    def notify_board(self, board: Board) -> None:
        self._board = board

    def notify_action(self, seat: int, action: Action) -> None:
        self._opponent_model.observe_action(seat, action, len(self._board))

    def get_action(self, view: PlayerView) -> Action:
        if view.hand_phase == HandPhase.PREFLOP_BETTING:
            return self._preflop_action(view)
        return self._postflop_action(view)

    # ------------------------------------------------------------------
    # Preflop
    # ------------------------------------------------------------------

    def _preflop_action(self, view: PlayerView) -> Action:
        profile = StartingHandProfile.classify(view.my_hole_cards)
        facing_bet = view.current_bet > view.my_chips_in_pot

        # Determine hand quality tier
        tier = self._preflop_tier(profile)

        if tier == 0:
            # Premium — raise or re-raise
            return self._pick_aggressive(view)
        elif tier == 1:
            # Strong — raise if unopened, call a raise
            if not facing_bet or view.current_bet <= view.blind_level.big_blind:
                return self._pick_aggressive(view)
            return self._pick_passive(view)
        elif tier == 2:
            # Playable — call if cheap, fold to big raises
            if facing_bet and view.current_bet > 4 * view.blind_level.big_blind:
                return self._pick_fold(view)
            return self._pick_passive(view)
        else:
            # Trash — fold
            return self._pick_fold(view)

    def _preflop_tier(self, profile: StartingHandProfile) -> int:
        """Classify starting hand into tiers (0=premium, 3=trash)."""
        cat = profile.category
        ss = profile.suit_structure

        # Tier 0: Premium
        premium = {StartingHandCategory.ACES}
        if cat in premium:
            return 0

        # Tier 1: Strong
        strong = {
            StartingHandCategory.HIGH_PAIRS,
            StartingHandCategory.HIGH_RUNDOWN,
            StartingHandCategory.DOUBLE_PAIRED,
        }
        if cat in strong:
            return 1
        # Double-suited medium rundowns are strong
        if cat == StartingHandCategory.MEDIUM_RUNDOWN and ss == SuitStructure.DOUBLE_SUITED:
            return 1

        # Tier 2: Playable
        playable = {
            StartingHandCategory.MEDIUM_PAIRS,
            StartingHandCategory.MEDIUM_RUNDOWN,
            StartingHandCategory.GAPPED_RUNDOWN,
            StartingHandCategory.SUITED_ACE,
        }
        if cat in playable:
            return 2
        if cat == StartingHandCategory.LOW_RUNDOWN and ss in (SuitStructure.DOUBLE_SUITED, SuitStructure.SINGLE_SUITED):
            return 2

        # Style adjustments
        if self._style == "LAG":
            if cat == StartingHandCategory.LOW_PAIRS:
                return 2
            if cat == StartingHandCategory.LOW_RUNDOWN:
                return 2
            if cat == StartingHandCategory.DANGLER and ss == SuitStructure.DOUBLE_SUITED:
                return 2
        elif self._style == "NIT":
            # Downgrade tier 2 to tier 3 for nits
            if cat in playable:
                return 3

        # Tier 3: Trash
        return 3

    # ------------------------------------------------------------------
    # Postflop
    # ------------------------------------------------------------------

    def _postflop_action(self, view: PlayerView) -> Action:
        props = HandProperties.analyze(view.my_hole_cards, view.board)
        facing_bet = view.current_bet > view.my_chips_in_pot
        to_call = view.current_bet - view.my_chips_in_pot

        # Pot odds for calling
        odds = pot_odds(view.pot_total, to_call) if to_call > 0 else 0.0

        strength = props.made_hand.value
        has_draw = props.draws != DrawType.NONE
        draw_eq = props.draw_equity_estimate

        # 1. Nutted hands — value bet/raise
        if strength >= MadeHandStrength.NUT_STRAIGHT.value:
            return self._pick_aggressive(view)

        # 2. Very strong — bet for value, raise facing bet
        if strength >= MadeHandStrength.TOP_SET.value:
            return self._pick_aggressive(view)

        # 3. Strong hands — bet if checked to, call if facing bet
        if strength >= MadeHandStrength.TOP_TWO.value:
            if facing_bet:
                return self._pick_passive(view)
            return self._pick_aggressive(view)

        # 4. Strong draws — semi-bluff or call based on pot odds
        if has_draw and draw_eq >= 0.25:
            if not facing_bet:
                # Semi-bluff with strong draws
                if self._should_bluff(props, view):
                    return self._pick_aggressive(view)
                return self._pick_check(view)
            # Facing bet — call if getting correct odds
            if draw_eq >= odds:
                return self._pick_passive(view)
            # Not getting odds but draw is strong enough for implied odds
            if draw_eq >= odds * 0.7 and strength >= MadeHandStrength.MIDDLE_PAIR.value:
                return self._pick_passive(view)
            return self._pick_fold(view)

        # 5. Medium hands (top pair, overpair, two pair)
        if strength >= MadeHandStrength.TOP_PAIR.value:
            if not facing_bet:
                # Bet for thin value sometimes
                if self._rng.random() < 0.5:
                    return self._pick_bet_small(view)
                return self._pick_check(view)
            # Facing bet — call one street, fold to big bets
            if to_call <= view.pot_total * 0.6:
                return self._pick_passive(view)
            return self._pick_fold(view)

        # 6. Weak draws
        if has_draw and draw_eq > 0:
            if not facing_bet:
                if self._should_bluff(props, view):
                    return self._pick_bet_small(view)
                return self._pick_check(view)
            if draw_eq >= odds:
                return self._pick_passive(view)
            return self._pick_fold(view)

        # 7. Good bluff candidates (weak hand + good blockers)
        if not facing_bet and props.is_good_bluff_candidate():
            if self._should_bluff(props, view):
                return self._pick_aggressive(view)

        # 8. Bottom pair or worse
        if not facing_bet:
            return self._pick_check(view)
        return self._pick_fold(view)

    def _should_bluff(self, props: HandProperties, view: PlayerView) -> bool:
        """Decide whether to bluff based on style and blocker quality."""
        base_freq = {
            "TAG": 0.30,
            "LAG": 0.50,
            "NIT": 0.10,
        }.get(self._style, 0.30)

        # Adjust for blocker quality
        freq = base_freq + props.blocker_score * 0.2

        return self._rng.random() < freq

    # ------------------------------------------------------------------
    # Action selection helpers
    # ------------------------------------------------------------------

    def _pick_aggressive(self, view: PlayerView) -> Action:
        """Pick the best aggressive action (bet or raise)."""
        aggressive = [
            a for a in view.legal_actions
            if a.action_type in (ActionType.BET, ActionType.RAISE)
        ]
        if not aggressive:
            return self._pick_passive(view)

        # Prefer 50-75% pot bets typically
        target_idx = len(aggressive) // 2
        # Add some randomness
        idx = max(0, min(len(aggressive) - 1, target_idx + self._rng.randint(-1, 1)))
        return aggressive[idx]

    def _pick_bet_small(self, view: PlayerView) -> Action:
        """Pick a small bet (33-50% pot)."""
        bets = [
            a for a in view.legal_actions
            if a.action_type in (ActionType.BET, ActionType.RAISE)
        ]
        if not bets:
            return self._pick_check(view)
        return bets[0]  # smallest available bet

    def _pick_passive(self, view: PlayerView) -> Action:
        """Pick call or check."""
        for a in view.legal_actions:
            if a.action_type == ActionType.CALL:
                return a
            if a.action_type == ActionType.CHECK:
                return a
        return self._pick_fold(view)

    def _pick_check(self, view: PlayerView) -> Action:
        """Pick check if available, otherwise call."""
        for a in view.legal_actions:
            if a.action_type == ActionType.CHECK:
                return a
        return self._pick_passive(view)

    def _pick_fold(self, view: PlayerView) -> Action:
        """Pick fold, but check instead if possible."""
        for a in view.legal_actions:
            if a.action_type == ActionType.CHECK:
                return a
        for a in view.legal_actions:
            if a.action_type == ActionType.FOLD:
                return a
        return view.legal_actions[0]
