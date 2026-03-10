"""Tests for domain abstractions (Layer 0.5)."""
import pytest

from plo_engine.types import parse_plo_hand, parse_board, make_plo_hand, Range
from plo_engine.domain import (
    BoardTexture, FlushDraw, Connectedness, Pairedness, BoardHeight,
    HandProperties, MadeHandStrength, DrawType,
    StartingHandProfile, StartingHandCategory, SuitStructure,
)


class TestBoardTexture:
    def test_monotone_flop(self):
        board = parse_board("Ks Ts 5s")
        bt = BoardTexture.from_board(board)
        assert bt.flush_draw == FlushDraw.MONOTONE
        assert bt.flush_possible is True
        assert bt.flush_suit == 3  # spades

    def test_two_tone_flop(self):
        board = parse_board("Ks Ts 5h")
        bt = BoardTexture.from_board(board)
        assert bt.flush_draw == FlushDraw.TWO_TONE
        assert bt.flush_possible is False

    def test_rainbow_flop(self):
        board = parse_board("Kh Td 5c")
        bt = BoardTexture.from_board(board)
        assert bt.flush_draw == FlushDraw.RAINBOW

    def test_paired_board(self):
        board = parse_board("Kh Kd 5c")
        bt = BoardTexture.from_board(board)
        assert bt.pairedness == Pairedness.PAIRED

    def test_unpaired_board(self):
        board = parse_board("Kh Qd 5c")
        bt = BoardTexture.from_board(board)
        assert bt.pairedness == Pairedness.UNPAIRED

    def test_trips_board(self):
        board = parse_board("Kh Kd Kc")
        bt = BoardTexture.from_board(board)
        assert bt.pairedness == Pairedness.TRIPS

    def test_high_board(self):
        board = parse_board("Ah Kd Qc")
        bt = BoardTexture.from_board(board)
        assert bt.height == BoardHeight.HIGH
        assert bt.has_ace is True
        assert bt.num_broadway == 3

    def test_low_board(self):
        board = parse_board("5h 3d 2c")
        bt = BoardTexture.from_board(board)
        assert bt.height == BoardHeight.LOW
        assert bt.has_ace is False

    def test_connected_board(self):
        board = parse_board("Jh Td 9c")
        bt = BoardTexture.from_board(board)
        assert bt.connectedness == Connectedness.HIGHLY_CONNECTED
        assert bt.straight_possible is True

    def test_disconnected_board(self):
        board = parse_board("Ah 7d 2c")
        bt = BoardTexture.from_board(board)
        assert bt.connectedness == Connectedness.DISCONNECTED

    def test_5card_board(self):
        board = parse_board("Ah Kd Qc Js Th")
        bt = BoardTexture.from_board(board)
        assert bt.straight_possible is True

    def test_describe(self):
        board = parse_board("Ks Ts 5s")
        bt = BoardTexture.from_board(board)
        desc = bt.describe()
        assert "monotone" in desc
        assert "Ks" in desc or "5s" in desc

    def test_invalid_board_size(self):
        with pytest.raises(ValueError):
            BoardTexture.from_board(parse_board("Ah Kd"))


class TestHandProperties:
    def test_top_set(self):
        hand = parse_plo_hand("Ah Ad Kh 2c")
        board = parse_board("As 5c 8d Jc Td")
        props = HandProperties.analyze(hand, board)
        assert props.made_hand == MadeHandStrength.TOP_SET

    def test_flush(self):
        hand = parse_plo_hand("Ah Kh 2c 3d")
        board = parse_board("Qh Jh 9h 5c 2d")
        props = HandProperties.analyze(hand, board)
        assert props.made_hand == MadeHandStrength.NUT_FLUSH

    def test_nothing(self):
        hand = parse_plo_hand("2c 3d 4h 6s")
        board = parse_board("Kh Qd Js Tc 8c")
        props = HandProperties.analyze(hand, board)
        assert props.made_hand == MadeHandStrength.NOTHING

    def test_flush_draw_on_flop(self):
        hand = parse_plo_hand("Ah Kh 2c 3d")
        board = parse_board("Qh 5h 9c")
        props = HandProperties.analyze(hand, board)
        assert DrawType.NUT_FLUSH_DRAW in props.draws
        assert props.total_outs > 0

    def test_blocks_nut_flush(self):
        hand = parse_plo_hand("Ah 2c 3d 4s")
        board = parse_board("Kh Qh 5h 9c 2d")
        props = HandProperties.analyze(hand, board)
        assert props.blocks_nut_flush is True

    def test_blocker_score_with_nut_blocker(self):
        hand = parse_plo_hand("Ah 2c 3d 4s")
        board = parse_board("Kh Qh 5h 9c 2d")
        props = HandProperties.analyze(hand, board)
        assert props.blocker_score > 0.0

    def test_good_bluff_candidate(self):
        # Weak hand with nut flush blocker
        hand = parse_plo_hand("Ah 2c 3d 4s")
        board = parse_board("Kh Qh 5h 9c 7d")
        props = HandProperties.analyze(hand, board)
        # Has ace of hearts (blocks nut flush), weak made hand
        assert props.blocks_nut_flush is True

    def test_describe(self):
        hand = parse_plo_hand("Ah Ad Kh 2c")
        board = parse_board("As 5c 8d Jc Td")
        props = HandProperties.analyze(hand, board)
        desc = props.describe()
        assert "top set" in desc

    def test_two_pair(self):
        hand = parse_plo_hand("Ah Kd 7c 2s")
        board = parse_board("As Kc 5h 9d 3c")
        props = HandProperties.analyze(hand, board)
        assert props.made_hand == MadeHandStrength.TOP_TWO

    def test_overpair(self):
        hand = parse_plo_hand("Ah Ad Kh Kd")
        board = parse_board("Qc Jh 5s 2c 3d")
        props = HandProperties.analyze(hand, board)
        assert props.made_hand == MadeHandStrength.OVERPAIR


class TestStartingHandProfile:
    def test_aces(self):
        hand = parse_plo_hand("Ah Ad Kh 2c")
        profile = StartingHandProfile.classify(hand)
        assert profile.category == StartingHandCategory.ACES
        assert profile.has_ace is True
        assert profile.highest_pair == 12

    def test_high_rundown_ds(self):
        hand = parse_plo_hand("Kh Qh Js Ts")
        profile = StartingHandProfile.classify(hand)
        assert profile.category == StartingHandCategory.HIGH_RUNDOWN
        assert profile.suit_structure == SuitStructure.DOUBLE_SUITED
        assert profile.is_connected is True
        assert profile.gap_count == 0

    def test_medium_rundown(self):
        hand = parse_plo_hand("Th 9d 8c 7s")
        profile = StartingHandProfile.classify(hand)
        assert profile.category == StartingHandCategory.MEDIUM_RUNDOWN
        assert profile.suit_structure == SuitStructure.RAINBOW

    def test_low_rundown(self):
        hand = parse_plo_hand("6h 5d 4c 3s")
        profile = StartingHandProfile.classify(hand)
        assert profile.category == StartingHandCategory.LOW_RUNDOWN

    def test_double_paired(self):
        hand = parse_plo_hand("Kh Kd Qh Qd")
        profile = StartingHandProfile.classify(hand)
        assert profile.category == StartingHandCategory.DOUBLE_PAIRED
        assert profile.num_pairs == 2

    def test_suited_ace(self):
        hand = parse_plo_hand("Ah 5h 9c 2d")
        profile = StartingHandProfile.classify(hand)
        assert profile.has_suited_ace is True

    def test_trash(self):
        hand = parse_plo_hand("Kh 9d 4c 2s")
        profile = StartingHandProfile.classify(hand)
        assert profile.category == StartingHandCategory.TRASH

    def test_describe(self):
        hand = parse_plo_hand("Kh Qh Js Ts")
        profile = StartingHandProfile.classify(hand)
        desc = profile.describe()
        assert "rundown" in desc.lower() or "suited" in desc.lower()

    def test_preflop_equity_aces_highest(self):
        aces = StartingHandProfile.classify(parse_plo_hand("Ah Ad Kh 2c"))
        trash = StartingHandProfile.classify(parse_plo_hand("Kh 9d 4c 2s"))
        assert aces.preflop_equity_estimate > trash.preflop_equity_estimate

    def test_gapped_rundown(self):
        hand = parse_plo_hand("Kh Qd Jc 9s")
        profile = StartingHandProfile.classify(hand)
        assert profile.category == StartingHandCategory.GAPPED_RUNDOWN
        assert profile.gap_count > 0

    def test_high_pair(self):
        hand = parse_plo_hand("Kh Kd 5c 2s")
        profile = StartingHandProfile.classify(hand)
        assert profile.category == StartingHandCategory.HIGH_PAIRS

    def test_medium_pair(self):
        hand = parse_plo_hand("9h 9d 5c 2s")
        profile = StartingHandProfile.classify(hand)
        assert profile.category == StartingHandCategory.MEDIUM_PAIRS

    def test_low_pair(self):
        hand = parse_plo_hand("3h 3d Kc 9s")
        profile = StartingHandProfile.classify(hand)
        assert profile.category == StartingHandCategory.LOW_PAIRS
