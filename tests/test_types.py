"""Tests for core data types."""
import pytest

from plo_engine.types import (
    Card,
    card_to_str,
    cards_to_str,
    parse_card,
    parse_cards,
    parse_plo_hand,
    parse_board,
    make_plo_hand,
    make_board,
    Range,
)


class TestCard:
    def test_card_creation(self):
        c = Card(0)
        assert c.rank == 0  # 2
        assert c.suit == 0  # clubs
        assert str(c) == "2c"

    def test_card_aces(self):
        for suit_idx, suit_char in enumerate("cdhs"):
            c = Card(48 + suit_idx)
            assert c.rank == 12
            assert str(c) == f"A{suit_char}"

    def test_card_from_str(self):
        assert Card.from_str("Ah").id == 50
        assert Card.from_str("2c").id == 0
        assert Card.from_str("Ks").id == 47
        assert Card.from_str("Td").id == 33

    def test_card_roundtrip(self):
        for i in range(52):
            c = Card(i)
            assert Card.from_str(str(c)).id == i

    def test_card_invalid(self):
        with pytest.raises(ValueError):
            Card(-1)
        with pytest.raises(ValueError):
            Card(52)

    def test_card_from_str_invalid(self):
        with pytest.raises(ValueError):
            Card.from_str("X")
        with pytest.raises(ValueError):
            Card.from_str("Ahh")


class TestUtilityFunctions:
    def test_card_to_str(self):
        assert card_to_str(0) == "2c"
        assert card_to_str(50) == "Ah"
        assert card_to_str(51) == "As"

    def test_cards_to_str(self):
        assert cards_to_str((50, 47, 33)) == "Ah Ks Td"

    def test_parse_card(self):
        assert parse_card("Ah") == 50
        assert parse_card("2c") == 0

    def test_parse_cards_spaces(self):
        result = parse_cards("Ah Kd Tc 2s")
        assert result == (50, 45, 32, 3)

    def test_parse_cards_no_spaces(self):
        result = parse_cards("AhKdTc2s")
        assert result == (50, 45, 32, 3)

    def test_parse_cards_empty(self):
        assert parse_cards("") == ()

    def test_parse_cards_roundtrip(self):
        original = (50, 45, 32, 3)
        s = cards_to_str(original)
        assert parse_cards(s) == original


class TestMakeHand:
    def test_make_plo_hand_sorts(self):
        hand = make_plo_hand(50, 3, 32, 45)
        assert hand == (3, 32, 45, 50)

    def test_make_plo_hand_wrong_count(self):
        with pytest.raises(ValueError):
            make_plo_hand(1, 2, 3)

    def test_make_plo_hand_duplicate(self):
        with pytest.raises(ValueError):
            make_plo_hand(1, 1, 2, 3)

    def test_make_board(self):
        board = make_board(50, 32, 3)
        assert board == (3, 32, 50)

    def test_make_board_empty(self):
        assert make_board() == ()

    def test_make_board_too_many(self):
        with pytest.raises(ValueError):
            make_board(0, 1, 2, 3, 4, 5)

    def test_parse_plo_hand(self):
        hand = parse_plo_hand("Ah Kd Tc 2s")
        assert len(hand) == 4
        assert hand == tuple(sorted(hand))

    def test_parse_board(self):
        board = parse_board("Ah Kd Tc")
        assert len(board) == 3
        assert board == tuple(sorted(board))

    def test_parse_board_empty(self):
        assert parse_board("") == ()


class TestRange:
    def test_from_hands(self):
        h1 = make_plo_hand(0, 4, 8, 12)
        h2 = make_plo_hand(1, 5, 9, 13)
        r = Range.from_hands([h1, h2])
        assert len(r) == 2
        assert h1 in r
        assert r.num_combos() == 2.0

    def test_remove_blockers(self):
        h1 = make_plo_hand(0, 4, 8, 12)
        h2 = make_plo_hand(1, 5, 9, 13)
        r = Range.from_hands([h1, h2])
        filtered = r.remove_blockers({0})
        assert len(filtered) == 1
        assert h1 not in filtered
        assert h2 in filtered

    def test_normalize(self):
        h1 = make_plo_hand(0, 4, 8, 12)
        h2 = make_plo_hand(1, 5, 9, 13)
        r = Range({h1: 3.0, h2: 1.0})
        norm = r.normalize()
        assert abs(norm.hands[h1] - 0.75) < 1e-9
        assert abs(norm.hands[h2] - 0.25) < 1e-9

    def test_filter(self):
        h1 = make_plo_hand(0, 4, 8, 12)
        h2 = make_plo_hand(1, 5, 9, 13)
        r = Range({h1: 1.0, h2: 0.5})
        filtered = r.filter(lambda h, w: w == 1.0)
        assert len(filtered) == 1

    def test_full_range_size(self):
        r = Range.full()
        assert len(r) == 270725

    def test_from_filter(self):
        # All hands containing the ace of spades
        r = Range.from_filter(lambda h: 51 in h)
        assert all(51 in h for h in r.hands)
        assert len(r) > 0
