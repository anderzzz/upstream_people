"""Service layer: AnalysisEngine.

Single entry point that composes domain, equity, and EV layers into
structured analysis results. Two primary modes:
  1. Hand Analysis — specific hand + board + scenario
  2. Range Analysis — ranges + board characterization
"""
from __future__ import annotations

from dataclasses import dataclass

from plo_engine.types import PLOHand, Board, Range, cards_to_str
from plo_engine.domain import (
    BoardTexture,
    DrawType,
    HandProperties,
    MadeHandStrength,
    RangeProfile,
    StartingHandCategory,
    StartingHandProfile,
    SuitStructure,
)
from plo_engine.equity import EquityResult, equity_hand_vs_range, equity_range_vs_range
from plo_engine.ev import ActionEV, evaluate_actions, pot_odds


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Spot:
    """Decision point descriptor (input container)."""

    board: Board
    pot: float = 0.0
    to_call: float = 0.0
    stacks: tuple[float, ...] = ()
    hero_hand: PLOHand | None = None
    hero_range: Range | None = None
    villain_range: Range | None = None
    position: str | None = None  # "IP" / "OOP"
    bb_size: float = 1.0


@dataclass(frozen=True)
class HandAnalysis:
    """Mode 1 result: everything we can say about a specific hand."""

    hand: PLOHand
    board: Board
    starting_hand_profile: StartingHandProfile
    board_texture: BoardTexture | None
    hand_properties: HandProperties | None
    equity: EquityResult | None
    action_evs: list[ActionEV] | None
    recommended_action: str | None
    pot_odds_needed: float | None
    has_profitable_call: bool | None

    def describe(self) -> str:
        parts: list[str] = []
        parts.append(f"Hand: {cards_to_str(self.hand)}")
        parts.append(f"Preflop: {self.starting_hand_profile.describe()}")

        if self.board:
            parts.append(f"Board: {cards_to_str(self.board)}")

        if self.board_texture is not None:
            parts.append(f"Texture: {self.board_texture.describe()}")

        if self.hand_properties is not None:
            parts.append(f"Hand strength: {self.hand_properties.describe()}")

        if self.equity is not None:
            parts.append(
                f"Equity: {self.equity.equity:.1%} "
                f"(W {self.equity.win_pct:.1%} / T {self.equity.tie_pct:.1%} / L {self.equity.loss_pct:.1%})"
            )

        if self.pot_odds_needed is not None:
            parts.append(f"Pot odds needed: {self.pot_odds_needed:.1%}")

        if self.has_profitable_call is not None:
            verdict = "YES" if self.has_profitable_call else "NO"
            parts.append(f"Profitable call: {verdict}")

        if self.action_evs:
            parts.append("Action EVs:")
            for aev in sorted(self.action_evs, key=lambda a: a.ev, reverse=True):
                parts.append(f"  {aev.action}: {aev.ev:+.1f} ({aev.ev_bb:+.1f} BB)")

        if self.recommended_action is not None:
            parts.append(f"Recommended: {self.recommended_action}")

        return "\n".join(parts)


@dataclass(frozen=True)
class RangeAnalysis:
    """Mode 2 result: range vs range characterization."""

    spot: Spot
    board_texture: BoardTexture
    hero_profile: RangeProfile | None
    villain_profile: RangeProfile | None
    range_equity: EquityResult | None
    nut_advantage: float | None
    range_comparison: str | None

    def describe(self) -> str:
        parts: list[str] = []
        parts.append(f"Board: {self.board_texture.describe()}")

        if self.hero_profile is not None:
            parts.append(f"Hero range: {self.hero_profile.describe()}")

        if self.villain_profile is not None:
            parts.append(f"Villain range: {self.villain_profile.describe()}")

        if self.range_equity is not None:
            parts.append(f"Range equity: {self.range_equity.equity:.1%}")

        if self.nut_advantage is not None:
            if self.nut_advantage > 0.02:
                parts.append(f"Hero has nut advantage: +{self.nut_advantage:.1%}")
            elif self.nut_advantage < -0.02:
                parts.append(f"Villain has nut advantage: {self.nut_advantage:.1%}")
            else:
                parts.append("Nut advantage is roughly even")

        if self.range_comparison is not None:
            parts.append(f"Comparison: {self.range_comparison}")

        return "\n".join(parts)


@dataclass(frozen=True)
class Strategy:
    """Action probability map."""

    actions: dict[str, float]

    def best_action(self) -> str:
        return max(self.actions, key=self.actions.get)  # type: ignore

    def describe(self) -> str:
        parts = [f"{act}: {prob:.0%}" for act, prob in
                 sorted(self.actions.items(), key=lambda x: x[1], reverse=True)]
        return ", ".join(parts)


# ---------------------------------------------------------------------------
# AnalysisEngine
# ---------------------------------------------------------------------------


class AnalysisEngine:
    """Stateless service that composes domain, equity, and EV layers."""

    def __init__(self, default_num_samples: int = 5000):
        self._default_num_samples = default_num_samples

    def analyze_hand(
        self,
        hand: PLOHand,
        board: Board = (),
        *,
        villain_range: Range | None = None,
        pot: float | None = None,
        to_call: float = 0.0,
        stack: float | None = None,
        bb_size: float = 1.0,
        num_samples: int | None = None,
    ) -> HandAnalysis:
        samples = num_samples or self._default_num_samples

        # 1. Always: starting hand profile
        profile = StartingHandProfile.classify(hand)

        # 2. Board texture + hand properties if board >= 3
        board_texture: BoardTexture | None = None
        hand_props: HandProperties | None = None
        if len(board) >= 3:
            hand_props = HandProperties.analyze(hand, board)
            board_texture = hand_props.board_texture

        # 3. Equity if villain range given
        equity: EquityResult | None = None
        if villain_range is not None:
            equity = equity_hand_vs_range(
                hand, villain_range, board, num_samples=samples,
            )

        # 4. Action EVs if pot geometry given
        action_evs: list[ActionEV] | None = None
        recommended_action: str | None = None
        if villain_range is not None and pot is not None:
            effective_stack = stack if stack is not None else pot * 5
            action_evs = evaluate_actions(
                hand, board, villain_range, pot, to_call, effective_stack,
                bb_size=bb_size, num_samples=samples,
            )
            if action_evs:
                recommended_action = max(action_evs, key=lambda a: a.ev).action

        # 5. Pot odds
        pot_odds_needed: float | None = None
        has_profitable_call: bool | None = None
        if to_call > 0 and pot is not None:
            pot_odds_needed = pot_odds(pot, to_call)
            if equity is not None:
                has_profitable_call = equity.equity >= pot_odds_needed

        return HandAnalysis(
            hand=hand,
            board=board,
            starting_hand_profile=profile,
            board_texture=board_texture,
            hand_properties=hand_props,
            equity=equity,
            action_evs=action_evs,
            recommended_action=recommended_action,
            pot_odds_needed=pot_odds_needed,
            has_profitable_call=has_profitable_call,
        )

    def analyze_ranges(
        self,
        board: Board,
        *,
        hero_range: Range | None = None,
        villain_range: Range | None = None,
        num_samples: int | None = None,
    ) -> RangeAnalysis:
        samples = num_samples or self._default_num_samples

        # 1. Board texture
        board_texture = BoardTexture.from_board(board)

        # 2. Range profiles
        hero_profile: RangeProfile | None = None
        villain_profile: RangeProfile | None = None
        if hero_range is not None:
            hero_profile = RangeProfile.analyze(hero_range, board, num_samples=samples)
        if villain_range is not None:
            villain_profile = RangeProfile.analyze(villain_range, board, num_samples=samples)

        # 3. Range vs range equity
        range_equity: EquityResult | None = None
        if hero_range is not None and villain_range is not None:
            range_equity = equity_range_vs_range(
                hero_range, villain_range, board, num_samples=samples,
            )

        # 4. Nut advantage and comparison
        nut_advantage: float | None = None
        range_comparison: str | None = None
        if hero_profile is not None and villain_profile is not None:
            nut_advantage = hero_profile.frac_nutted - villain_profile.frac_nutted
            range_comparison = hero_profile.compare_to(villain_profile)

        spot = Spot(board=board, hero_range=hero_range, villain_range=villain_range)
        return RangeAnalysis(
            spot=spot,
            board_texture=board_texture,
            hero_profile=hero_profile,
            villain_profile=villain_profile,
            range_equity=range_equity,
            nut_advantage=nut_advantage,
            range_comparison=range_comparison,
        )

    def narrow_range(
        self,
        range_: Range,
        action: str,
        board: Board,
        pot: float = 0.0,
        bet_size: float = 0.0,
    ) -> Range:
        """Heuristic range narrowing based on action taken.

        Adjusts weights rather than hard-filtering so the range narrows
        but doesn't collapse. This is explicitly a heuristic — proper
        range evolution requires CFR.
        """
        new_hands: dict[PLOHand, float] = {}
        action_lower = action.lower()

        for hand, weight in range_.hands.items():
            if any(c in board for c in hand):
                continue
            try:
                props = HandProperties.analyze(hand, board)
            except Exception:
                continue

            strength = props.made_hand.value
            has_draw = props.draws != DrawType.NONE
            draw_eq = props.draw_equity_estimate
            blocker = props.blocker_score

            if action_lower == "fold":
                # Keep weak hands: medium pair and below, no strong draws
                if strength <= MadeHandStrength.MIDDLE_PAIR.value and not (has_draw and draw_eq >= 0.20):
                    new_hands[hand] = weight
                elif strength <= MadeHandStrength.TOP_PAIR.value and not (has_draw and draw_eq >= 0.15):
                    new_hands[hand] = weight * 0.3
                # Strong hands almost never fold
                elif strength >= MadeHandStrength.TWO_PAIR.value:
                    new_hands[hand] = weight * 0.02

            elif action_lower == "check":
                # Medium hands, some draws, some traps
                if strength <= MadeHandStrength.TOP_PAIR.value:
                    new_hands[hand] = weight
                elif has_draw and draw_eq < 0.25:
                    new_hands[hand] = weight * 0.8
                elif strength >= MadeHandStrength.TOP_TWO.value:
                    # Trapping with strong hands sometimes
                    new_hands[hand] = weight * 0.3
                else:
                    new_hands[hand] = weight * 0.6

            elif action_lower == "call":
                # Medium-strong hands and drawing hands
                if strength >= MadeHandStrength.TOP_PAIR.value and strength <= MadeHandStrength.TOP_TWO.value:
                    new_hands[hand] = weight
                elif has_draw and draw_eq >= 0.15:
                    new_hands[hand] = weight * 0.8
                elif strength >= MadeHandStrength.SET.value:
                    # Slow-playing monsters sometimes
                    new_hands[hand] = weight * 0.4
                elif strength >= MadeHandStrength.MIDDLE_PAIR.value:
                    new_hands[hand] = weight * 0.5
                elif strength < MadeHandStrength.MIDDLE_PAIR.value:
                    new_hands[hand] = weight * 0.1

            elif action_lower in ("bet", "raise"):
                # Nutted + strong draws + bluff candidates
                if props.is_nutted or strength >= MadeHandStrength.TOP_SET.value:
                    new_hands[hand] = weight
                elif has_draw and draw_eq >= 0.25:
                    # Strong semi-bluffs
                    new_hands[hand] = weight * 0.7
                elif blocker >= 0.5 and strength <= MadeHandStrength.MIDDLE_PAIR.value:
                    # Bluff candidates with good blockers
                    new_hands[hand] = weight * 0.4
                elif strength >= MadeHandStrength.TOP_TWO.value:
                    new_hands[hand] = weight * 0.6
                elif strength >= MadeHandStrength.TOP_PAIR.value:
                    new_hands[hand] = weight * 0.2
                else:
                    new_hands[hand] = weight * 0.05
            else:
                new_hands[hand] = weight

        return Range(new_hands)

    def classify_preflop_tier(
        self,
        profile: StartingHandProfile,
        style: str = "TAG",
    ) -> int:
        """Classify starting hand into tiers (0=premium, 3=trash).

        Extracted from HeuristicPlayer._preflop_tier() logic.
        """
        cat = profile.category
        ss = profile.suit_structure
        style = style.upper()

        # Tier 0: Premium
        if cat == StartingHandCategory.ACES:
            return 0

        # Tier 1: Strong
        strong = {
            StartingHandCategory.HIGH_PAIRS,
            StartingHandCategory.HIGH_RUNDOWN,
            StartingHandCategory.DOUBLE_PAIRED,
        }
        if cat in strong:
            return 1
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
        if cat == StartingHandCategory.LOW_RUNDOWN and ss in (
            SuitStructure.DOUBLE_SUITED, SuitStructure.SINGLE_SUITED
        ):
            return 2

        # Style adjustments
        if style == "LAG":
            if cat == StartingHandCategory.LOW_PAIRS:
                return 2
            if cat == StartingHandCategory.LOW_RUNDOWN:
                return 2
            if cat == StartingHandCategory.DANGLER and ss == SuitStructure.DOUBLE_SUITED:
                return 2
        elif style == "NIT":
            if cat in playable:
                return 3

        # Tier 3: Trash
        return 3
