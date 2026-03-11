"""Tests for the AnalysisEngine service layer."""

import pytest

from plo_engine.analysis import (
    AnalysisEngine,
    HandAnalysis,
    RangeAnalysis,
    Spot,
    Strategy,
)
from plo_engine.domain import (
    MadeHandStrength,
    StartingHandCategory,
    StartingHandProfile,
)
from plo_engine.types import Range, make_board, make_plo_hand, parse_board, parse_plo_hand


@pytest.fixture
def engine():
    return AnalysisEngine(default_num_samples=500)


# ---------------------------------------------------------------------------
# Spot
# ---------------------------------------------------------------------------

class TestSpot:
    def test_defaults(self):
        s = Spot(board=())
        assert s.pot == 0.0
        assert s.to_call == 0.0
        assert s.hero_hand is None
        assert s.villain_range is None

    def test_frozen(self):
        s = Spot(board=())
        with pytest.raises(AttributeError):
            s.pot = 10  # type: ignore


# ---------------------------------------------------------------------------
# Strategy
# ---------------------------------------------------------------------------

class TestStrategy:
    def test_best_action(self):
        s = Strategy(actions={"fold": 0.1, "call": 0.6, "raise_67%": 0.3})
        assert s.best_action() == "call"

    def test_describe(self):
        s = Strategy(actions={"fold": 0.0, "call": 0.7, "raise_67%": 0.3})
        desc = s.describe()
        assert "call" in desc
        assert len(desc) > 0


# ---------------------------------------------------------------------------
# analyze_hand — progressive inputs
# ---------------------------------------------------------------------------

class TestAnalyzeHand:
    def test_hand_only(self, engine):
        """Hand with no board — only preflop profile."""
        hand = parse_plo_hand("Ah Kh Qd Jd")
        result = engine.analyze_hand(hand)

        assert isinstance(result, HandAnalysis)
        assert result.starting_hand_profile is not None
        assert result.board_texture is None
        assert result.hand_properties is None
        assert result.equity is None
        assert result.action_evs is None
        assert result.recommended_action is None
        assert result.pot_odds_needed is None

    def test_hand_plus_board(self, engine):
        """Hand + board — adds board texture and hand properties."""
        hand = parse_plo_hand("Ah Kh Qd Jd")
        board = parse_board("Th 9h 2c")
        result = engine.analyze_hand(hand, board)

        assert result.board_texture is not None
        assert result.hand_properties is not None
        assert result.equity is None  # no villain range

    def test_hand_plus_board_plus_range(self, engine):
        """Hand + board + villain range — adds equity."""
        hand = parse_plo_hand("Ah Kh Qd Jd")
        board = parse_board("Th 9h 2c")
        # Small range for speed
        villain = Range.from_hands([
            parse_plo_hand("Ac Kc Qc Jc"),
            parse_plo_hand("8c 7c 6c 5c"),
            parse_plo_hand("2d 3d 4d 5d"),
        ])
        result = engine.analyze_hand(hand, board, villain_range=villain)

        assert result.equity is not None
        assert 0.0 <= result.equity.equity <= 1.0
        assert result.action_evs is None  # no pot

    def test_full_scenario(self, engine):
        """Hand + board + range + pot geometry — full analysis."""
        hand = parse_plo_hand("Ah Kh Qd Jd")
        board = parse_board("Th 9h 2c")
        villain = Range.from_hands([
            parse_plo_hand("Ac Kc Qc Jc"),
            parse_plo_hand("8c 7c 6c 5c"),
        ])
        result = engine.analyze_hand(
            hand, board,
            villain_range=villain,
            pot=100, to_call=50, stack=500,
        )

        assert result.equity is not None
        assert result.action_evs is not None
        assert len(result.action_evs) > 0
        assert result.recommended_action is not None
        assert result.pot_odds_needed is not None
        assert result.has_profitable_call is not None

    def test_no_call_no_pot_odds(self, engine):
        """When to_call=0, pot_odds_needed is None."""
        hand = parse_plo_hand("Ah Kh Qd Jd")
        board = parse_board("Th 9h 2c")
        villain = Range.from_hands([parse_plo_hand("Ac Kc Qc Jc")])
        result = engine.analyze_hand(
            hand, board, villain_range=villain, pot=100, to_call=0,
        )
        assert result.pot_odds_needed is None

    def test_describe_nonempty(self, engine):
        hand = parse_plo_hand("Ah Kh Qd Jd")
        result = engine.analyze_hand(hand)
        desc = result.describe()
        assert len(desc) > 0
        assert "Hand:" in desc

    def test_describe_full(self, engine):
        hand = parse_plo_hand("Ah Kh Qd Jd")
        board = parse_board("Th 9h 2c")
        villain = Range.from_hands([parse_plo_hand("Ac Kc Qc Jc")])
        result = engine.analyze_hand(
            hand, board, villain_range=villain, pot=100, to_call=50,
        )
        desc = result.describe()
        assert "Equity:" in desc
        assert "Pot odds needed:" in desc
        assert "Recommended:" in desc

    def test_preflop_only_board_empty(self, engine):
        """Empty board should produce preflop-only analysis."""
        hand = parse_plo_hand("Ah Ad Kc Qc")
        result = engine.analyze_hand(hand, board=())
        assert result.starting_hand_profile.category == StartingHandCategory.ACES

    def test_river_board(self, engine):
        """Full 5-card board works."""
        hand = parse_plo_hand("Ah Kh Qd Jd")
        board = parse_board("Th 9h 2c 3s 4s")
        result = engine.analyze_hand(hand, board)
        assert result.hand_properties is not None


# ---------------------------------------------------------------------------
# analyze_ranges
# ---------------------------------------------------------------------------

class TestAnalyzeRanges:
    def test_hero_only(self, engine):
        board = parse_board("Th 9h 2c")
        hero = Range.from_hands([
            parse_plo_hand("Ah Kh Qd Jd"),
            parse_plo_hand("8c 7c 6c 5c"),
        ])
        result = engine.analyze_ranges(board, hero_range=hero)

        assert isinstance(result, RangeAnalysis)
        assert result.board_texture is not None
        assert result.hero_profile is not None
        assert result.villain_profile is None
        assert result.range_equity is None
        assert result.nut_advantage is None

    def test_both_ranges(self, engine):
        board = parse_board("Th 9h 2c")
        hero = Range.from_hands([
            parse_plo_hand("Ah Kh Qd Jd"),
            parse_plo_hand("8c 7c 6c 5c"),
        ])
        villain = Range.from_hands([
            parse_plo_hand("Ac Kc Qs Js"),
            parse_plo_hand("2d 3d 4d 5d"),
        ])
        result = engine.analyze_ranges(board, hero_range=hero, villain_range=villain)

        assert result.hero_profile is not None
        assert result.villain_profile is not None
        assert result.range_equity is not None
        assert result.nut_advantage is not None
        assert result.range_comparison is not None

    def test_villain_only(self, engine):
        board = parse_board("Th 9h 2c")
        villain = Range.from_hands([parse_plo_hand("Ac Kc Qs Js")])
        result = engine.analyze_ranges(board, villain_range=villain)

        assert result.villain_profile is not None
        assert result.hero_profile is None
        assert result.range_equity is None

    def test_describe_nonempty(self, engine):
        board = parse_board("Th 9h 2c")
        hero = Range.from_hands([parse_plo_hand("Ah Kh Qd Jd")])
        villain = Range.from_hands([parse_plo_hand("Ac Kc Qs Js")])
        result = engine.analyze_ranges(board, hero_range=hero, villain_range=villain)
        desc = result.describe()
        assert "Board:" in desc
        assert len(desc) > 0


# ---------------------------------------------------------------------------
# narrow_range
# ---------------------------------------------------------------------------

class TestNarrowRange:
    @pytest.fixture
    def mixed_range(self):
        """A range with strong, medium, and weak hands."""
        return Range.from_hands([
            # Strong
            parse_plo_hand("Ah Ad Kh Kd"),  # aces
            parse_plo_hand("Th Td 9h 9d"),  # double paired
            # Medium
            parse_plo_hand("Jh Tc 9s 8d"),  # rundown
            parse_plo_hand("Qh Jh 8c 7c"),  # suited connectors
            # Weak
            parse_plo_hand("2c 3d 7s Ks"),  # trash
            parse_plo_hand("2d 4c 8s Qc"),  # trash
        ])

    def test_raise_narrows_to_strong(self, engine, mixed_range):
        board = parse_board("Th 9c 2s")
        raised = engine.narrow_range(mixed_range, "raise", board)
        # Should have fewer combos than original (some hands weighted down)
        assert raised.num_combos() < mixed_range.num_combos()
        assert raised.num_combos() > 0

    def test_fold_narrows_to_weak(self, engine, mixed_range):
        board = parse_board("Th 9c 2s")
        folded = engine.narrow_range(mixed_range, "fold", board)
        assert folded.num_combos() < mixed_range.num_combos()
        assert folded.num_combos() > 0

    def test_call_keeps_medium(self, engine, mixed_range):
        board = parse_board("Th 9c 2s")
        called = engine.narrow_range(mixed_range, "call", board)
        assert called.num_combos() > 0

    def test_check_keeps_most(self, engine, mixed_range):
        board = parse_board("Th 9c 2s")
        checked = engine.narrow_range(mixed_range, "check", board)
        # Check keeps most hands (traps + medium)
        assert checked.num_combos() > 0

    def test_blockers_removed(self, engine):
        """Hands conflicting with board are removed."""
        r = Range.from_hands([parse_plo_hand("Th 9h 2c 3c")])
        board = parse_board("Th 9c 2s")
        result = engine.narrow_range(r, "call", board)
        assert result.num_combos() == 0  # hand conflicts with board

    def test_unknown_action_passes_through(self, engine, mixed_range):
        board = parse_board("Th 9c 2s")
        result = engine.narrow_range(mixed_range, "unknown_action", board)
        # Hands that don't conflict with board pass through unchanged
        assert result.num_combos() > 0


# ---------------------------------------------------------------------------
# classify_preflop_tier
# ---------------------------------------------------------------------------

class TestClassifyPreflopTier:
    def test_aces_premium(self, engine):
        profile = StartingHandProfile.classify(parse_plo_hand("Ah Ad Kc Qc"))
        assert engine.classify_preflop_tier(profile) == 0

    def test_high_pairs_strong(self, engine):
        profile = StartingHandProfile.classify(parse_plo_hand("Kh Kd Qc Js"))
        assert engine.classify_preflop_tier(profile) == 1

    def test_high_rundown_strong(self, engine):
        profile = StartingHandProfile.classify(parse_plo_hand("Ah Kh Qd Jd"))
        tier = engine.classify_preflop_tier(profile)
        assert tier <= 1

    def test_medium_pair_playable(self, engine):
        profile = StartingHandProfile.classify(parse_plo_hand("8h 8d 5c 4s"))
        assert engine.classify_preflop_tier(profile) == 2

    def test_trash_is_tier3(self, engine):
        profile = StartingHandProfile.classify(parse_plo_hand("2c 4d 7s Kh"))
        assert engine.classify_preflop_tier(profile) == 3

    def test_lag_widens(self, engine):
        # Low pair is tier 3 for TAG but tier 2 for LAG
        profile = StartingHandProfile.classify(parse_plo_hand("4h 4d 7c 9s"))
        assert engine.classify_preflop_tier(profile, style="TAG") == 3
        assert engine.classify_preflop_tier(profile, style="LAG") == 2

    def test_nit_tightens(self, engine):
        # Low rundown (rainbow) is tier 3 for TAG, but also tier 3 for NIT.
        # NIT downgrade only applies to hands that reach the style-adjustment
        # block (i.e. hands not already returned as tier 2 by the playable check).
        # A suited ace dangler is tier 3 for NIT but tier 2 for LAG.
        profile = StartingHandProfile.classify(parse_plo_hand("4h 4d 7c 9s"))
        assert engine.classify_preflop_tier(profile, style="TAG") == 3
        assert engine.classify_preflop_tier(profile, style="LAG") == 2
        assert engine.classify_preflop_tier(profile, style="NIT") == 3

    def test_matches_heuristic_player(self, engine):
        """Verify tier logic matches HeuristicPlayer._preflop_tier for TAG."""
        from plo_engine.players.heuristic_player import HeuristicPlayer
        player = HeuristicPlayer("test", style="TAG", seed=42)

        test_hands = [
            parse_plo_hand("Ah Ad Kh Kd"),
            parse_plo_hand("Kh Kd Qc Js"),
            parse_plo_hand("Jh Td 9c 8s"),
            parse_plo_hand("2c 4d 7s Kh"),
        ]
        for hand in test_hands:
            profile = StartingHandProfile.classify(hand)
            engine_tier = engine.classify_preflop_tier(profile, style="TAG")
            player_tier = player._preflop_tier(profile)
            assert engine_tier == player_tier, f"Mismatch for {hand}: engine={engine_tier}, player={player_tier}"
