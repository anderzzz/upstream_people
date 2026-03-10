"""Tests for the hand evaluator — correctness is paramount."""
import pytest

from plo_engine.types import parse_cards, parse_plo_hand, parse_board
from plo_engine.hand_evaluator import evaluate_5card, best_plo_hand, category_of


def parse(s: str) -> tuple[int, ...]:
    """Shorthand for tests."""
    return parse_cards(s)


# ---------------------------------------------------------------------------
# Category detection
# ---------------------------------------------------------------------------

class TestCategoryDetection:
    def test_straight_flush_royal(self):
        # Royal flush is a straight flush
        rank = evaluate_5card(parse("Ah Kh Qh Jh Th"))
        assert category_of(rank) == 8

    def test_straight_flush_suits_dont_matter(self):
        assert evaluate_5card(parse("Ah Kh Qh Jh Th")) == evaluate_5card(parse("As Ks Qs Js Ts"))

    def test_straight_flush_ranking(self):
        assert evaluate_5card(parse("Kh Qh Jh Th 9h")) > evaluate_5card(parse("6c 5c 4c 3c 2c"))

    def test_wheel_straight_flush(self):
        rank = evaluate_5card(parse("5h 4h 3h 2h Ah"))
        assert category_of(rank) == 8
        # 6-high SF beats wheel SF
        assert evaluate_5card(parse("6c 5c 4c 3c 2c")) > evaluate_5card(parse("5h 4h 3h 2h Ah"))

    def test_four_of_a_kind(self):
        rank = evaluate_5card(parse("Ah Ac Ad As Kh"))
        assert category_of(rank) == 7

    def test_four_of_a_kind_kicker(self):
        assert evaluate_5card(parse("Ah Ac Ad As Kh")) > evaluate_5card(parse("Ah Ac Ad As Qh"))

    def test_full_house(self):
        rank = evaluate_5card(parse("3h 3c 3d Ah Ac"))
        assert category_of(rank) == 6

    def test_full_house_trips_rank_dominates(self):
        assert evaluate_5card(parse("3h 3c 3d Ah Ac")) > evaluate_5card(parse("2h 2c 2d Kh Kc"))

    def test_flush(self):
        rank = evaluate_5card(parse("Ah Th 7h 4h 3h"))
        assert category_of(rank) == 5

    def test_flush_kicker_comparison(self):
        assert evaluate_5card(parse("Ah Th 7h 4h 3h")) > evaluate_5card(parse("Ah Th 7h 4h 2h"))

    def test_straight(self):
        rank = evaluate_5card(parse("Ah Kd Qc Js Th"))
        assert category_of(rank) == 4

    def test_straight_ranking(self):
        assert evaluate_5card(parse("Ah Kd Qc Js Th")) > evaluate_5card(parse("Kh Qd Jc Ts 9h"))

    def test_wheel_straight(self):
        rank = evaluate_5card(parse("5d 4c 3h 2s Ad"))
        assert category_of(rank) == 4
        # 6-high straight beats wheel
        assert evaluate_5card(parse("6d 5c 4h 3s 2d")) > evaluate_5card(parse("5d 4c 3h 2s Ad"))

    def test_three_of_a_kind(self):
        rank = evaluate_5card(parse("Ah Ac Ad 4h 3c"))
        assert category_of(rank) == 3

    def test_two_pair(self):
        rank = evaluate_5card(parse("Ah Ac Kd Kc 3h"))
        assert category_of(rank) == 2

    def test_two_pair_high_pair_dominates(self):
        assert evaluate_5card(parse("Ah Ac 3d 3c Kh")) > evaluate_5card(parse("Kh Kc Qd Qc Ah"))

    def test_one_pair(self):
        rank = evaluate_5card(parse("Ah Ac Kd Qc 3h"))
        assert category_of(rank) == 1

    def test_high_card(self):
        rank = evaluate_5card(parse("Ah Kd Qc Jh 9c"))
        assert category_of(rank) == 0


# ---------------------------------------------------------------------------
# Category ordering: SF > 4K > FH > FL > ST > 3K > 2P > 1P > HC
# ---------------------------------------------------------------------------

class TestCategoryOrdering:
    def test_straight_flush_beats_quads(self):
        assert evaluate_5card(parse("6h 5h 4h 3h 2h")) > evaluate_5card(parse("Ah Ac Ad As Kh"))

    def test_quads_beats_full_house(self):
        assert evaluate_5card(parse("2h 2c 2d 2s 3h")) > evaluate_5card(parse("Ah Ac Ad Kh Kc"))

    def test_full_house_beats_flush(self):
        assert evaluate_5card(parse("Ah Ac Ad Kh Kc")) > evaluate_5card(parse("Ah Kh Qh Jh 9h"))

    def test_flush_beats_straight(self):
        assert evaluate_5card(parse("Ah Kh Qh Jh 9h")) > evaluate_5card(parse("Ah Kd Qc Js Th"))

    def test_straight_beats_trips(self):
        assert evaluate_5card(parse("Ah Kd Qc Js Th")) > evaluate_5card(parse("Ah Ac Ad 4h 3c"))

    def test_trips_beats_two_pair(self):
        assert evaluate_5card(parse("Ah Ac Ad 4h 3c")) > evaluate_5card(parse("Ah Ac Kd Kc 3h"))

    def test_two_pair_beats_one_pair(self):
        assert evaluate_5card(parse("Ah Ac Kd Kc 3h")) > evaluate_5card(parse("Ah Ac Kd Qc 3h"))

    def test_one_pair_beats_high_card(self):
        assert evaluate_5card(parse("Ah Ac Kd Qc 3h")) > evaluate_5card(parse("Ah Kd Qc Jh 9c"))


# ---------------------------------------------------------------------------
# PLO-specific: must use exactly 2 hole cards
# ---------------------------------------------------------------------------

class TestPLOBestHand:
    def test_basic_evaluation(self):
        hole = parse_plo_hand("Ah Kh Qh Jh")
        board = parse_board("Th 9h 8h 2c 3d")
        rank = best_plo_hand(hole, board)
        # Best: Ah Kh + Th 9h 8h = A-high flush (or Ah + Th 9h 8h = straight flush? No, need exactly 2)
        # Ah Kh from hole, Th 9h 8h from board => AhKhTh9h8h = flush (A-high)
        # But also Qh Jh from hole + Th 9h 8h from board => QhJhTh9h8h = straight flush Q-high!
        # And Kh Qh from hole + Th 9h 8h = KhQhTh9h8h = flush
        # Jh Th... wait Jh is hole, Th is board... Jh + another hole card + 3 board
        # Best is actually: Qh Jh (hole) + Th 9h 8h (board) = Q-high straight flush
        assert category_of(rank) == 8  # straight flush

    def test_cannot_play_the_board(self):
        # Board has A-K-Q-J-T straight but player must use 2 hole cards
        hole = parse_plo_hand("2c 3d 7s 8c")
        board = parse_board("Ts Jh Qd Ks Ad")
        rank = best_plo_hand(hole, board)
        # Player must use 2 of {2c, 3d, 7s, 8c} and 3 of {Ts, Jh, Qd, Ks, Ad}
        # Best possible: 7s 8c + Ts Jh Qd? = not a straight (7,8,T,J,Q has gaps)
        # 7s 8c + 9? no 9 on board
        # This is just a high-card or pair hand at best
        assert category_of(rank) < 4  # certainly not a straight or better

    def test_four_hearts_not_auto_flush(self):
        # 4 hearts in hand but flush requires exactly 2 hole + 3 board
        hole = parse_plo_hand("Ah Kh Qh 2h")
        board = parse_board("9h 5c 3d Jc Td")
        rank = best_plo_hand(hole, board)
        # Only 1 heart on board (9h), can't make flush with 2 hole + 3 board
        # (would need 3 hearts on board to pair with 2 from hand)
        assert category_of(rank) != 5  # not a flush

    def test_plo_hand_wrong_size(self):
        with pytest.raises(ValueError):
            best_plo_hand((0, 1, 2), (3, 4, 5, 6, 7))  # type: ignore

    def test_board_wrong_size(self):
        with pytest.raises(ValueError):
            best_plo_hand((0, 1, 2, 3), (4, 5, 6))  # type: ignore

    def test_set_detection(self):
        # Pocket pair makes a set
        hole = parse_plo_hand("Ah Ad Kh 2c")
        board = parse_board("As 5c 8d Jc Td")
        rank = best_plo_hand(hole, board)
        assert category_of(rank) == 3  # three of a kind (set of aces)

    def test_two_pair_from_both(self):
        hole = parse_plo_hand("Ah Kd 7c 2s")
        board = parse_board("As Kc 5h 9d 3c")
        rank = best_plo_hand(hole, board)
        assert category_of(rank) == 2  # two pair (aces and kings)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_all_same_rank_hands_equal(self):
        # Pair of aces with same kickers, different suits => same rank
        r1 = evaluate_5card(parse("Ah Ac Kd Qc 3h"))
        r2 = evaluate_5card(parse("Ad As Ks Qh 3c"))
        assert r1 == r2

    def test_flush_tie_all_kickers(self):
        # Identical flush ranks, different suits => equal
        r1 = evaluate_5card(parse("Ah Kh Qh Jh 9h"))
        r2 = evaluate_5card(parse("As Ks Qs Js 9s"))
        assert r1 == r2
