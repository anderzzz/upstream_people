"""Layer 0.5: Domain abstractions.

Strategic vocabulary for poker concepts — board textures, hand properties,
range profiles, and starting hand taxonomy.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, Flag, auto
from itertools import combinations

from plo_engine.types import (
    PLOHand, Board, HandRank, Range,
    RANK_NAMES, SUIT_NAMES, card_to_str, cards_to_str,
)
from plo_engine.hand_evaluator import evaluate_5card, best_plo_hand, category_of


# ---------------------------------------------------------------------------
# Board Texture
# ---------------------------------------------------------------------------

class FlushDraw(Enum):
    RAINBOW = auto()
    TWO_TONE = auto()
    MONOTONE = auto()


class Connectedness(Enum):
    DISCONNECTED = auto()
    SEMI_CONNECTED = auto()
    HIGHLY_CONNECTED = auto()


class Pairedness(Enum):
    UNPAIRED = auto()
    PAIRED = auto()
    DOUBLE_PAIRED = auto()
    TRIPS = auto()


class BoardHeight(Enum):
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()


@dataclass(frozen=True)
class BoardTexture:
    """Strategic classification of a community board (3-5 cards)."""

    board: Board
    flush_draw: FlushDraw
    connectedness: Connectedness
    pairedness: Pairedness
    height: BoardHeight

    suit_counts: dict[int, int]
    rank_counts: dict[int, int]
    highest_rank: int
    lowest_rank: int
    has_ace: bool
    num_broadway: int
    straight_possible: bool
    flush_possible: bool
    flush_suit: int | None
    nut_hand_description: str

    @classmethod
    def from_board(cls, board: Board) -> BoardTexture:
        if not (3 <= len(board) <= 5):
            raise ValueError(f"Board must have 3-5 cards, got {len(board)}")

        ranks = [c // 4 for c in board]
        suits = [c % 4 for c in board]

        suit_counts: dict[int, int] = {}
        for s in suits:
            suit_counts[s] = suit_counts.get(s, 0) + 1

        rank_counts: dict[int, int] = {}
        for r in ranks:
            rank_counts[r] = rank_counts.get(r, 0) + 1

        max_suit_count = max(suit_counts.values())
        highest_rank = max(ranks)
        lowest_rank = min(ranks)
        has_ace = 12 in ranks
        num_broadway = sum(1 for r in ranks if r >= 8)  # T=8, J=9, Q=10, K=11, A=12

        # Flush classification
        if max_suit_count >= 3:
            flush_draw = FlushDraw.MONOTONE
        elif max_suit_count == 2:
            flush_draw = FlushDraw.TWO_TONE
        else:
            flush_draw = FlushDraw.RAINBOW

        # Flush possible: 3+ of one suit on board means a hand can make a flush
        # (with 2 more of that suit in hand)
        flush_possible = max_suit_count >= 3
        flush_suit = None
        if flush_possible:
            flush_suit = max(suit_counts, key=suit_counts.get)  # type: ignore

        # Pairedness
        count_vals = sorted(rank_counts.values(), reverse=True)
        if count_vals[0] >= 3:
            pairedness = Pairedness.TRIPS
        elif count_vals[0] == 2 and len(count_vals) > 1 and count_vals[1] == 2:
            pairedness = Pairedness.DOUBLE_PAIRED
        elif count_vals[0] == 2:
            pairedness = Pairedness.PAIRED
        else:
            pairedness = Pairedness.UNPAIRED

        # Connectedness: based on rank spread and gaps
        unique_ranks = sorted(set(ranks))
        connectedness = _classify_connectedness(unique_ranks)

        # Straight possible: check if any 5-rank window contains 3+ board ranks
        straight_possible = _straight_possible(unique_ranks)

        # Height
        if highest_rank >= 10:  # Q or higher
            height = BoardHeight.HIGH
        elif highest_rank >= 7:  # 9 or higher
            height = BoardHeight.MEDIUM
        else:
            height = BoardHeight.LOW

        # Nut hand description
        nut_desc = _describe_nuts(board, rank_counts, flush_possible, flush_suit, pairedness)

        return cls(
            board=board,
            flush_draw=flush_draw,
            connectedness=connectedness,
            pairedness=pairedness,
            height=height,
            suit_counts=suit_counts,
            rank_counts=rank_counts,
            highest_rank=highest_rank,
            lowest_rank=lowest_rank,
            has_ace=has_ace,
            num_broadway=num_broadway,
            straight_possible=straight_possible,
            flush_possible=flush_possible,
            flush_suit=flush_suit,
            nut_hand_description=nut_desc,
        )

    def describe(self) -> str:
        parts = []
        parts.append(self.flush_draw.name.lower().replace("_", "-"))
        parts.append(self.height.name.lower())
        parts.append(self.pairedness.name.lower())
        parts.append(self.connectedness.name.lower().replace("_", "-"))
        board_str = cards_to_str(self.board)
        return f"{' '.join(parts)} ({board_str})"


def _classify_connectedness(unique_ranks: list[int]) -> Connectedness:
    """Classify connectedness based on gaps between sorted unique ranks."""
    if len(unique_ranks) < 2:
        return Connectedness.DISCONNECTED

    gaps = [unique_ranks[i + 1] - unique_ranks[i] for i in range(len(unique_ranks) - 1)]
    total_span = unique_ranks[-1] - unique_ranks[0]
    avg_gap = total_span / len(gaps) if gaps else 0

    # Also consider wrapping (A can be low)
    # Count how many pairs are within 4 of each other (can contribute to straights)
    close_pairs = sum(1 for g in gaps if g <= 2)

    if avg_gap <= 1.5 and total_span <= len(unique_ranks) + 1:
        return Connectedness.HIGHLY_CONNECTED
    elif close_pairs >= len(gaps) // 2 + 1 or total_span <= len(unique_ranks) + 3:
        return Connectedness.SEMI_CONNECTED
    else:
        return Connectedness.DISCONNECTED


def _straight_possible(unique_ranks: list[int]) -> bool:
    """Check if any hand could make a straight using these board ranks."""
    # Add ace-low (rank 12 can also act as rank -1 for wheel)
    rank_set = set(unique_ranks)
    if 12 in rank_set:
        rank_set.add(-1)

    # Check every possible 5-rank straight window
    for low in range(-1, 10):  # -1 (wheel) through 8 (broadway)
        window = set(range(low, low + 5))
        # Board contributes at least 3 cards to this window,
        # and the hand contributes at least 2
        board_in_window = len(window & rank_set)
        if board_in_window >= 3:
            return True
    return False


def _describe_nuts(
    board: Board,
    rank_counts: dict[int, int],
    flush_possible: bool,
    flush_suit: int | None,
    pairedness: Pairedness,
) -> str:
    """Generate a rough description of the nut hand on this board."""
    if flush_possible and flush_suit is not None:
        suit_name = SUIT_NAMES[flush_suit]
        return f"nut flush (A{suit_name})"

    if pairedness in (Pairedness.PAIRED, Pairedness.TRIPS):
        return "full house or quads"

    # Check for straight possibilities
    board_ranks = sorted(rank_counts.keys(), reverse=True)
    return f"top set ({RANK_NAMES[board_ranks[0]]}s)" if board_ranks else "unknown"


# ---------------------------------------------------------------------------
# Hand Properties
# ---------------------------------------------------------------------------

class DrawType(Flag):
    NONE = 0
    NUT_FLUSH_DRAW = auto()
    SECOND_NUT_FLUSH_DRAW = auto()
    FLUSH_DRAW = auto()
    OESD = auto()
    GUTSHOT = auto()
    DOUBLE_GUTSHOT = auto()
    WRAP = auto()
    COMBO_DRAW = auto()
    SET_DRAW = auto()
    FULL_HOUSE_DRAW = auto()


class MadeHandStrength(Enum):
    NOTHING = 0
    BOTTOM_PAIR = 1
    MIDDLE_PAIR = 2
    TOP_PAIR = 3
    OVERPAIR = 4
    TWO_PAIR = 5
    TOP_TWO = 6
    SET = 7
    BOTTOM_SET = 8
    MIDDLE_SET = 9
    TOP_SET = 10
    STRAIGHT = 11
    NUT_STRAIGHT = 12
    FLUSH = 13
    NUT_FLUSH = 14
    FULL_HOUSE = 15
    QUADS = 16
    STRAIGHT_FLUSH = 17


@dataclass(frozen=True)
class HandProperties:
    """Analysis of a PLO hand on a specific board."""

    hand: PLOHand
    board: Board
    board_texture: BoardTexture

    hand_rank: HandRank
    made_hand: MadeHandStrength
    is_nutted: bool

    draws: DrawType
    nut_draw_outs: int
    total_outs: int
    draw_equity_estimate: float

    blocks_nut_flush: bool
    blocks_second_nut_flush: bool
    blocks_nut_straight: bool
    blocks_sets: list[int]
    blocker_score: float

    nut_rank: int
    distance_to_nuts: int

    @classmethod
    def analyze(cls, hand: PLOHand, board: Board) -> HandProperties:
        if len(board) < 3:
            raise ValueError("Board must have at least 3 cards for analysis")
        if len(board) > 5:
            raise ValueError("Board must have at most 5 cards")

        board_texture = BoardTexture.from_board(board)

        # Evaluate hand if board is complete (5 cards)
        if len(board) == 5:
            hand_rank = best_plo_hand(hand, board)
        else:
            # For flop/turn, evaluate what we currently have
            # Use all available board cards for partial evaluation
            hand_rank = _partial_hand_rank(hand, board)

        cat = category_of(hand_rank)
        made_hand = _classify_made_hand(hand, board, board_texture, cat, hand_rank)

        # Draw analysis
        draws, nut_draw_outs, total_outs = _analyze_draws(hand, board, board_texture)

        # Combo draw detection
        has_flush_draw = bool(draws & (DrawType.NUT_FLUSH_DRAW | DrawType.SECOND_NUT_FLUSH_DRAW | DrawType.FLUSH_DRAW))
        has_straight_draw = bool(draws & (DrawType.OESD | DrawType.GUTSHOT | DrawType.DOUBLE_GUTSHOT | DrawType.WRAP))
        if has_flush_draw and has_straight_draw:
            draws = draws | DrawType.COMBO_DRAW

        draw_equity = _estimate_draw_equity(total_outs, len(board))

        # Blocker analysis
        blocks_nut_flush = False
        blocks_second_nut_flush = False
        flush_suit = board_texture.flush_suit
        if flush_suit is not None:
            hand_suits = {c % 4: c // 4 for c in hand}
            for c in hand:
                if c % 4 == flush_suit:
                    r = c // 4
                    if r == 12:  # ace
                        blocks_nut_flush = True
                    elif r == 11:  # king
                        blocks_second_nut_flush = True

        blocks_sets = _find_blocked_sets(hand, board)
        blocks_nut_straight = _blocks_nut_straight(hand, board)

        blocker_score = _compute_blocker_score(
            blocks_nut_flush, blocks_second_nut_flush,
            blocks_nut_straight, blocks_sets, board_texture,
        )

        # Nut proximity
        is_nutted = cat >= 4 and made_hand.value >= MadeHandStrength.NUT_STRAIGHT.value
        nut_rank, distance = _compute_nut_rank(hand, board, hand_rank)

        return cls(
            hand=hand,
            board=board,
            board_texture=board_texture,
            hand_rank=hand_rank,
            made_hand=made_hand,
            is_nutted=is_nutted,
            draws=draws,
            nut_draw_outs=nut_draw_outs,
            total_outs=total_outs,
            draw_equity_estimate=draw_equity,
            blocks_nut_flush=blocks_nut_flush,
            blocks_second_nut_flush=blocks_second_nut_flush,
            blocks_nut_straight=blocks_nut_straight,
            blocks_sets=blocks_sets,
            blocker_score=blocker_score,
            nut_rank=nut_rank,
            distance_to_nuts=distance,
        )

    def describe(self) -> str:
        parts = [self.made_hand.name.lower().replace("_", " ")]
        if self.draws != DrawType.NONE:
            draw_parts = [d.name.lower().replace("_", " ")
                          for d in DrawType if d in self.draws and d != DrawType.NONE]
            if draw_parts:
                parts.append("with " + ", ".join(draw_parts))
        if self.blocks_nut_flush:
            parts.append("(blocks nut flush)")
        return " ".join(parts)

    def is_good_bluff_candidate(self) -> bool:
        """Heuristic: weak made hand + good blockers + some equity."""
        weak = self.made_hand.value <= MadeHandStrength.MIDDLE_PAIR.value
        good_blockers = self.blocker_score >= 0.5
        has_equity = self.draw_equity_estimate >= 0.1
        return weak and good_blockers and has_equity


def _partial_hand_rank(hand: PLOHand, board: Board) -> HandRank:
    """Evaluate hand on an incomplete board by checking available combos."""
    best = -1
    for h2 in combinations(hand, 2):
        for b3 in combinations(board, min(3, len(board))):
            if len(h2) + len(b3) == 5:
                rank = evaluate_5card((*h2, *b3))
                if rank > best:
                    best = rank
    # For flop (3 board cards), we get C(4,2)*C(3,3) = 6 combos
    return best if best >= 0 else 0


def _classify_made_hand(
    hand: PLOHand, board: Board, bt: BoardTexture,
    cat: int, hand_rank: HandRank,
) -> MadeHandStrength:
    """Classify current made-hand strength relative to the board."""
    if cat == 8:
        return MadeHandStrength.STRAIGHT_FLUSH
    if cat == 7:
        return MadeHandStrength.QUADS
    if cat == 6:
        return MadeHandStrength.FULL_HOUSE
    if cat == 5:
        # Check if nut flush
        if bt.flush_suit is not None:
            hand_ranks_in_suit = sorted(
                [c // 4 for c in hand if c % 4 == bt.flush_suit], reverse=True
            )
            if hand_ranks_in_suit and hand_ranks_in_suit[0] == 12:
                return MadeHandStrength.NUT_FLUSH
        return MadeHandStrength.FLUSH
    if cat == 4:
        # Check if nut straight
        # For simplicity, if we have the highest possible straight, it's the nuts
        return MadeHandStrength.STRAIGHT  # simplified
    if cat == 3:
        # Set — classify as top/middle/bottom
        board_ranks = sorted([c // 4 for c in board], reverse=True)
        trips_rank = _find_trips_rank(hand, board)
        if trips_rank is not None:
            unique_board_ranks = sorted(set(board_ranks), reverse=True)
            if trips_rank == unique_board_ranks[0]:
                return MadeHandStrength.TOP_SET
            elif len(unique_board_ranks) > 1 and trips_rank == unique_board_ranks[-1]:
                return MadeHandStrength.BOTTOM_SET
            else:
                return MadeHandStrength.MIDDLE_SET
        return MadeHandStrength.SET
    if cat == 2:
        # Two pair — check if top two
        board_ranks = sorted(set(c // 4 for c in board), reverse=True)
        if len(board_ranks) >= 2:
            hand_ranks = set(c // 4 for c in hand)
            if board_ranks[0] in hand_ranks and board_ranks[1] in hand_ranks:
                return MadeHandStrength.TOP_TWO
        return MadeHandStrength.TWO_PAIR
    if cat == 1:
        # One pair — classify relative to board
        board_ranks = sorted(set(c // 4 for c in board), reverse=True)
        hand_ranks = set(c // 4 for c in hand)
        pair_rank = _find_pair_rank(hand, board)
        if pair_rank is not None:
            # Overpair: pair in hand, both cards above all board cards
            hand_pairs = [r for r in hand_ranks
                          if sum(1 for c in hand if c // 4 == r) >= 2]
            if hand_pairs and all(p > br for p in hand_pairs for br in board_ranks):
                return MadeHandStrength.OVERPAIR
            if pair_rank == board_ranks[0]:
                return MadeHandStrength.TOP_PAIR
            elif pair_rank == board_ranks[-1]:
                return MadeHandStrength.BOTTOM_PAIR
            else:
                return MadeHandStrength.MIDDLE_PAIR
        return MadeHandStrength.BOTTOM_PAIR
    return MadeHandStrength.NOTHING


def _find_trips_rank(hand: PLOHand, board: Board) -> int | None:
    """Find the rank of a set (pocket pair hitting the board)."""
    hand_ranks = [c // 4 for c in hand]
    board_ranks = [c // 4 for c in board]
    for r in set(hand_ranks):
        if hand_ranks.count(r) >= 2 and r in board_ranks:
            return r
        if hand_ranks.count(r) >= 1 and board_ranks.count(r) >= 2:
            return r
    return None


def _find_pair_rank(hand: PLOHand, board: Board) -> int | None:
    """Find the rank of a pair (hand card matching board card)."""
    hand_ranks = set(c // 4 for c in hand)
    board_ranks = [c // 4 for c in board]
    # Pair with board card
    for r in sorted(hand_ranks, reverse=True):
        if r in board_ranks:
            return r
    # Pocket pair
    hr_list = [c // 4 for c in hand]
    for r in sorted(set(hr_list), reverse=True):
        if hr_list.count(r) >= 2:
            return r
    return None


def _analyze_draws(
    hand: PLOHand, board: Board, bt: BoardTexture,
) -> tuple[DrawType, int, int]:
    """Analyze draws. Returns (draw_flags, nut_outs, total_outs).

    Tracks out *cards* as sets to avoid double-counting when a single card
    completes both a flush and a straight draw simultaneously.
    """
    draws = DrawType.NONE
    all_out_cards: set[int] = set()
    nut_out_cards: set[int] = set()

    if len(board) >= 5:
        # No draws on the river
        return draws, 0, 0

    dead_cards = set(hand) | set(board)

    # Flush draw analysis
    if bt.flush_suit is not None or any(
        v == 2 for v in bt.suit_counts.values()
    ):
        fd_result = _check_flush_draw(hand, board, bt, dead_cards)
        draws = draws | fd_result[0]
        all_out_cards |= fd_result[1]
        nut_out_cards |= fd_result[2]

    # Straight draw analysis
    sd_result = _check_straight_draws(hand, board, dead_cards)
    draws = draws | sd_result[0]
    all_out_cards |= sd_result[1]
    nut_out_cards |= sd_result[2]

    # Set draw (pocket pair)
    hand_ranks = [c // 4 for c in hand]
    for r in set(hand_ranks):
        if hand_ranks.count(r) >= 2 and r not in [c // 4 for c in board]:
            draws = draws | DrawType.SET_DRAW
            for suit in range(4):
                card = r * 4 + suit
                if card not in dead_cards:
                    all_out_cards.add(card)
            break

    # Full house draw (two pair on board, or set already)
    if category_of(_partial_hand_rank(hand, board)) == 2:
        draws = draws | DrawType.FULL_HOUSE_DRAW
        # Cards that pair any of our paired ranks
        hand_rank_set = set(hand_ranks)
        board_rank_set = set(c // 4 for c in board)
        paired_ranks = hand_rank_set & board_rank_set
        for r in paired_ranks:
            for suit in range(4):
                card = r * 4 + suit
                if card not in dead_cards:
                    all_out_cards.add(card)

    return draws, len(nut_out_cards), len(all_out_cards)


def _check_flush_draw(
    hand: PLOHand, board: Board, bt: BoardTexture, dead_cards: set[int],
) -> tuple[DrawType, set[int], set[int]]:
    """Check for flush draws. Returns (draw_type, out_cards, nut_out_cards)."""
    draws = DrawType.NONE
    out_cards: set[int] = set()
    nut_out_cards: set[int] = set()

    for suit in range(4):
        board_count = sum(1 for c in board if c % 4 == suit)
        hand_count = sum(1 for c in hand if c % 4 == suit)

        if board_count >= 2 and hand_count >= 2:
            # Flush draw: need 1 more card of this suit
            # Collect actual card ints that complete the flush
            flush_cards = {
                r * 4 + suit for r in range(13)
                if r * 4 + suit not in dead_cards
            }

            hand_ranks_in_suit = sorted(
                [c // 4 for c in hand if c % 4 == suit], reverse=True
            )
            if hand_ranks_in_suit[0] == 12:  # ace
                draws = draws | DrawType.NUT_FLUSH_DRAW
                nut_out_cards |= flush_cards
            elif hand_ranks_in_suit[0] == 11:  # king
                ace_on_board = any(c // 4 == 12 and c % 4 == suit for c in board)
                if ace_on_board:
                    draws = draws | DrawType.NUT_FLUSH_DRAW
                    nut_out_cards |= flush_cards
                else:
                    draws = draws | DrawType.SECOND_NUT_FLUSH_DRAW
            else:
                draws = draws | DrawType.FLUSH_DRAW
            out_cards |= flush_cards

    return draws, out_cards, nut_out_cards


def _check_straight_draws(
    hand: PLOHand, board: Board, dead_cards: set[int],
) -> tuple[DrawType, set[int], set[int]]:
    """Check for straight draws. Returns (draw_type, out_cards, nut_out_cards)."""
    draws = DrawType.NONE
    all_ranks = set(c // 4 for c in hand) | set(c // 4 for c in board)

    # Also consider ace as low
    if 12 in all_ranks:
        all_ranks_with_low = all_ranks | {-1}
    else:
        all_ranks_with_low = all_ranks

    out_cards: set[int] = set()
    nut_out_cards: set[int] = set()
    needed_ranks: set[int] = set()

    # Track the highest straight each needed rank can complete (for nut classification)
    best_straight_top: dict[int, int] = {}

    # Check each possible 5-card straight window
    for low in range(-1, 10):
        window = set(range(low, low + 5))
        need = window - all_ranks_with_low

        if len(need) == 1:
            needed_rank = next(iter(need))
            actual_rank = 12 if needed_rank == -1 else needed_rank
            straight_top = low + 4
            if actual_rank not in needed_ranks:
                needed_ranks.add(actual_rank)
                best_straight_top[actual_rank] = straight_top
            else:
                best_straight_top[actual_rank] = max(best_straight_top[actual_rank], straight_top)

    # Collect actual card ints for each needed rank
    for rank in needed_ranks:
        for suit in range(4):
            card = rank * 4 + suit
            if card not in dead_cards:
                out_cards.add(card)

    total_outs = len(out_cards)

    # Classify the draw type based on total outs
    if total_outs >= 13:
        draws = DrawType.WRAP
        nut_out_cards = set(out_cards)  # wraps are often nut draws
    elif total_outs >= 8:
        if len(needed_ranks) == 2:
            draws = DrawType.DOUBLE_GUTSHOT
        else:
            draws = DrawType.OESD
        # Approximate: higher-completing cards are more likely nut draws
        for rank in needed_ranks:
            if best_straight_top[rank] >= 8:  # T-high straight or better
                for suit in range(4):
                    card = rank * 4 + suit
                    if card not in dead_cards:
                        nut_out_cards.add(card)
    elif total_outs >= 4:
        draws = DrawType.GUTSHOT
    elif total_outs > 0:
        draws = DrawType.GUTSHOT

    return draws, out_cards, nut_out_cards


def _estimate_draw_equity(total_outs: int, board_cards: int) -> float:
    """Rough equity estimate from draw outs using rule of 2 and 4."""
    cards_to_come = 5 - board_cards
    if cards_to_come == 2:
        return min(total_outs * 4 / 100.0, 0.60)
    elif cards_to_come == 1:
        return min(total_outs * 2 / 100.0, 0.50)
    return 0.0


def _find_blocked_sets(hand: PLOHand, board: Board) -> list[int]:
    """Find board ranks where we hold a card, blocking opponents' sets."""
    hand_ranks = set(c // 4 for c in hand)
    board_ranks = set(c // 4 for c in board)
    return sorted(hand_ranks & board_ranks, reverse=True)


def _blocks_nut_straight(hand: PLOHand, board: Board) -> bool:
    """Check if we hold cards that block the nut straight."""
    # Simplified: check if we hold cards that would complete the highest straight
    board_ranks = sorted(set(c // 4 for c in board), reverse=True)
    hand_ranks = set(c // 4 for c in hand)

    # Find the highest straight possible on this board
    all_board = set(board_ranks)
    if 12 in all_board:
        all_board.add(-1)

    for high in range(12, -2, -1):
        window = set(range(high - 4, high + 1))
        board_in = window & all_board
        need = window - all_board
        if len(board_in) >= 3 and len(need) <= 2:
            # Check if we block any of the needed cards
            for needed_rank in need:
                actual_rank = 12 if needed_rank == -1 else needed_rank
                if actual_rank in hand_ranks:
                    return True
    return False


def _compute_blocker_score(
    blocks_nf: bool, blocks_2nf: bool, blocks_ns: bool,
    blocks_sets: list[int], bt: BoardTexture,
) -> float:
    """Composite blocker quality score (0-1) for bluffing potential."""
    score = 0.0
    if blocks_nf:
        score += 0.35
    if blocks_2nf:
        score += 0.15
    if blocks_ns:
        score += 0.20
    # Blocking top set is more valuable
    if blocks_sets:
        set_value = min(len(blocks_sets) * 0.1, 0.30)
        if bt.highest_rank in blocks_sets:
            set_value += 0.10
        score += set_value
    return min(score, 1.0)


def _compute_nut_rank(
    hand: PLOHand, board: Board, hand_rank: HandRank,
) -> tuple[int, int]:
    """Compute how close this hand is to the nuts.

    Returns (nut_rank, distance_to_nuts).
    nut_rank=1 means we have the nuts.
    """
    if len(board) < 5:
        # On flop/turn, nut rank is approximate
        cat = category_of(hand_rank)
        if cat >= 6:
            return 1, 0
        return max(1, 9 - cat), 8 - cat

    # On the river, we could enumerate all possible 2-card holdings
    # For now, use a simpler heuristic based on category
    cat = category_of(hand_rank)
    if cat == 8:
        return 1, 0  # straight flush is always nuts or near-nuts
    if cat == 7:
        return 1, 0  # quads nearly always nuts
    # Simplified — full enumeration deferred
    return max(1, 9 - cat), max(0, 8 - cat)


# ---------------------------------------------------------------------------
# Starting Hand Taxonomy
# ---------------------------------------------------------------------------

class StartingHandCategory(Enum):
    ACES = auto()
    HIGH_PAIRS = auto()
    MEDIUM_PAIRS = auto()
    LOW_PAIRS = auto()
    DOUBLE_PAIRED = auto()
    HIGH_RUNDOWN = auto()
    MEDIUM_RUNDOWN = auto()
    LOW_RUNDOWN = auto()
    GAPPED_RUNDOWN = auto()
    DOUBLE_SUITED = auto()
    SUITED_ACE = auto()
    DANGLER = auto()
    TRASH = auto()


class SuitStructure(Enum):
    DOUBLE_SUITED = auto()
    SINGLE_SUITED = auto()
    RAINBOW = auto()
    MONOTONE = auto()
    TRIP_SUITED = auto()


@dataclass(frozen=True)
class StartingHandProfile:
    """Classification of a PLO starting hand (preflop, no board)."""

    hand: PLOHand
    category: StartingHandCategory
    suit_structure: SuitStructure
    is_connected: bool
    gap_count: int
    highest_pair: int | None
    num_pairs: int
    has_ace: bool
    has_suited_ace: bool
    suits_description: str
    preflop_equity_estimate: float

    @classmethod
    def classify(cls, hand: PLOHand) -> StartingHandProfile:
        ranks = sorted([c // 4 for c in hand], reverse=True)
        suits = [c % 4 for c in hand]

        # Suit structure
        suit_counts: dict[int, int] = {}
        for s in suits:
            suit_counts[s] = suit_counts.get(s, 0) + 1
        suit_structure = _classify_suit_structure(suit_counts)

        # Pairs
        rank_counts: dict[int, int] = {}
        for r in ranks:
            rank_counts[r] = rank_counts.get(r, 0) + 1
        pairs = [r for r, c in rank_counts.items() if c >= 2]
        num_pairs = len(pairs)
        highest_pair = max(pairs) if pairs else None

        has_ace = 12 in ranks

        # Suited ace check
        has_suited_ace = False
        if has_ace:
            ace_suits = [c % 4 for c in hand if c // 4 == 12]
            for s in ace_suits:
                if suit_counts.get(s, 0) >= 2:
                    has_suited_ace = True
                    break

        # Connectedness and gaps
        unique_ranks = sorted(set(ranks), reverse=True)
        span = unique_ranks[0] - unique_ranks[-1] if len(unique_ranks) > 1 else 0
        is_connected = span <= 4 and len(unique_ranks) >= 3
        gap_count = _count_gaps(unique_ranks)

        # Category classification
        category = _classify_starting_hand(
            ranks, unique_ranks, num_pairs, highest_pair,
            has_ace, has_suited_ace, is_connected, gap_count, span,
        )

        # Suit description
        suits_desc = _describe_suits(hand, suit_counts, suit_structure)

        # Rough preflop equity estimate
        equity = _estimate_preflop_equity(category, suit_structure, num_pairs, highest_pair)

        return cls(
            hand=hand,
            category=category,
            suit_structure=suit_structure,
            is_connected=is_connected,
            gap_count=gap_count,
            highest_pair=highest_pair,
            num_pairs=num_pairs,
            has_ace=has_ace,
            has_suited_ace=has_suited_ace,
            suits_description=suits_desc,
            preflop_equity_estimate=equity,
        )

    def describe(self) -> str:
        cat = self.category.name.lower().replace("_", " ")
        hand_str = cards_to_str(self.hand)
        parts = []
        if self.suit_structure == SuitStructure.DOUBLE_SUITED:
            parts.append("double-suited")
        elif self.suit_structure == SuitStructure.SINGLE_SUITED:
            parts.append("single-suited")
        parts.append(cat)
        return f"{' '.join(parts)} ({hand_str})"


def _classify_suit_structure(suit_counts: dict[int, int]) -> SuitStructure:
    counts = sorted(suit_counts.values(), reverse=True)
    if counts[0] >= 3:
        return SuitStructure.TRIP_SUITED if counts[0] == 3 else SuitStructure.MONOTONE
    if len(counts) >= 2 and counts[0] == 2 and counts[1] == 2:
        return SuitStructure.DOUBLE_SUITED
    if counts[0] == 2:
        return SuitStructure.SINGLE_SUITED
    return SuitStructure.RAINBOW


def _count_gaps(unique_ranks_desc: list[int]) -> int:
    """Count gaps in a descending sequence of unique ranks."""
    if len(unique_ranks_desc) < 2:
        return 0
    gaps = 0
    for i in range(len(unique_ranks_desc) - 1):
        diff = unique_ranks_desc[i] - unique_ranks_desc[i + 1]
        if diff > 1:
            gaps += diff - 1
    return gaps


def _classify_starting_hand(
    ranks: list[int], unique_ranks: list[int],
    num_pairs: int, highest_pair: int | None,
    has_ace: bool, has_suited_ace: bool,
    is_connected: bool, gap_count: int, span: int,
) -> StartingHandCategory:
    # Double paired
    if num_pairs == 2:
        return StartingHandCategory.DOUBLE_PAIRED

    # Aces
    if highest_pair == 12:
        return StartingHandCategory.ACES

    # High pairs
    if highest_pair is not None and highest_pair >= 9:  # JJ+
        return StartingHandCategory.HIGH_PAIRS

    # Medium pairs
    if highest_pair is not None and highest_pair >= 5:  # 77-TT
        return StartingHandCategory.MEDIUM_PAIRS

    # Low pairs
    if highest_pair is not None:
        return StartingHandCategory.LOW_PAIRS

    # Rundowns (connected, no pairs)
    if is_connected and gap_count == 0:
        min_rank = min(unique_ranks)
        if min_rank >= 8:  # T+
            return StartingHandCategory.HIGH_RUNDOWN
        elif min_rank >= 5:  # 7+
            return StartingHandCategory.MEDIUM_RUNDOWN
        else:
            return StartingHandCategory.LOW_RUNDOWN

    if is_connected and gap_count <= 2:
        return StartingHandCategory.GAPPED_RUNDOWN

    # Suited ace
    if has_suited_ace:
        return StartingHandCategory.SUITED_ACE

    # Dangler: 3 connected + 1 unrelated
    if len(unique_ranks) == 4 and span > 4:
        sub_spans = []
        for combo in combinations(unique_ranks, 3):
            s = sorted(combo, reverse=True)
            sub_span = s[0] - s[2]
            sub_spans.append(sub_span)
        if any(s <= 3 for s in sub_spans):
            return StartingHandCategory.DANGLER

    return StartingHandCategory.TRASH


def _describe_suits(
    hand: PLOHand, suit_counts: dict[int, int], structure: SuitStructure,
) -> str:
    if structure == SuitStructure.DOUBLE_SUITED:
        suited = [SUIT_NAMES[s] for s, c in suit_counts.items() if c == 2]
        return f"double suited {'/'.join(suited)}"
    if structure == SuitStructure.SINGLE_SUITED:
        suited = [SUIT_NAMES[s] for s, c in suit_counts.items() if c >= 2]
        return f"suited {'/'.join(suited)}"
    if structure == SuitStructure.RAINBOW:
        return "rainbow"
    if structure in (SuitStructure.TRIP_SUITED, SuitStructure.MONOTONE):
        suited = [SUIT_NAMES[s] for s, c in suit_counts.items() if c >= 3]
        return f"{'monotone' if structure == SuitStructure.MONOTONE else 'trip suited'} {'/'.join(suited)}"
    return ""


def _estimate_preflop_equity(
    category: StartingHandCategory, suit_structure: SuitStructure,
    num_pairs: int, highest_pair: int | None,
) -> float:
    """Rough preflop equity vs random hand."""
    base = {
        StartingHandCategory.ACES: 0.65,
        StartingHandCategory.HIGH_PAIRS: 0.58,
        StartingHandCategory.MEDIUM_PAIRS: 0.54,
        StartingHandCategory.LOW_PAIRS: 0.50,
        StartingHandCategory.DOUBLE_PAIRED: 0.56,
        StartingHandCategory.HIGH_RUNDOWN: 0.57,
        StartingHandCategory.MEDIUM_RUNDOWN: 0.53,
        StartingHandCategory.LOW_RUNDOWN: 0.49,
        StartingHandCategory.GAPPED_RUNDOWN: 0.51,
        StartingHandCategory.SUITED_ACE: 0.54,
        StartingHandCategory.DANGLER: 0.47,
        StartingHandCategory.TRASH: 0.43,
    }.get(category, 0.45)

    # Suit bonus
    if suit_structure == SuitStructure.DOUBLE_SUITED:
        base += 0.03
    elif suit_structure == SuitStructure.SINGLE_SUITED:
        base += 0.01

    return min(base, 0.70)


# ---------------------------------------------------------------------------
# Range Profile
# ---------------------------------------------------------------------------

class RangeShape(Enum):
    POLARIZED = auto()
    MERGED = auto()
    CAPPED = auto()
    LINEAR = auto()
    CONDENSED = auto()


@dataclass
class RangeProfile:
    """Strategic summary of a Range on a given Board."""

    range_: Range
    board: Board
    board_texture: BoardTexture

    frac_nutted: float
    frac_strong: float
    frac_medium: float
    frac_weak: float

    frac_flush_draws: float
    frac_straight_draws: float
    frac_combo_draws: float
    frac_drawing_dead: float

    shape: RangeShape
    is_capped: bool
    nut_advantage: float

    avg_blocker_score: float

    mean_equity: float
    equity_std: float
    equity_percentiles: dict[int, float]

    @classmethod
    def analyze(
        cls,
        range_: Range,
        board: Board,
        opponent_range: Range | None = None,
        *,
        num_samples: int = 5000,
    ) -> RangeProfile:
        """Build a strategic profile of a range on a board.

        This is computationally expensive — it evaluates HandProperties for
        every hand in the range.
        """
        bt = BoardTexture.from_board(board)

        # Analyze all hands
        props_list: list[HandProperties] = []
        for hand in range_.hands:
            # Skip hands that conflict with the board
            if any(c in board for c in hand):
                continue
            try:
                props = HandProperties.analyze(hand, board)
                props_list.append(props)
            except Exception:
                continue

        if not props_list:
            return cls._empty(range_, board, bt)

        total = len(props_list)

        # Strength distribution
        nutted = sum(1 for p in props_list if p.is_nutted) / total
        strong = sum(1 for p in props_list
                     if p.made_hand.value >= MadeHandStrength.TOP_PAIR.value
                     and not p.is_nutted) / total
        weak = sum(1 for p in props_list
                   if p.made_hand.value <= MadeHandStrength.NOTHING.value
                   and p.draws == DrawType.NONE) / total
        medium = 1.0 - nutted - strong - weak

        # Draw distribution
        flush_draws = sum(1 for p in props_list
                         if bool(p.draws & (DrawType.NUT_FLUSH_DRAW | DrawType.SECOND_NUT_FLUSH_DRAW | DrawType.FLUSH_DRAW))) / total
        straight_draws = sum(1 for p in props_list
                            if bool(p.draws & (DrawType.OESD | DrawType.GUTSHOT | DrawType.WRAP | DrawType.DOUBLE_GUTSHOT))) / total
        combo_draws = sum(1 for p in props_list
                         if bool(p.draws & DrawType.COMBO_DRAW)) / total
        drawing_dead = sum(1 for p in props_list
                          if p.made_hand == MadeHandStrength.NOTHING and p.draws == DrawType.NONE) / total

        # Shape classification
        is_capped = nutted < 0.05
        shape = _classify_shape(nutted, strong, medium, weak)

        # Blocker analysis
        avg_blocker = sum(p.blocker_score for p in props_list) / total

        # Equity estimates (using draw equity as proxy without full equity calc)
        equities = [p.draw_equity_estimate + (p.made_hand.value / 17.0 * 0.5)
                    for p in props_list]
        mean_eq = sum(equities) / len(equities)
        variance = sum((e - mean_eq) ** 2 for e in equities) / len(equities)
        std_eq = variance ** 0.5

        sorted_eq = sorted(equities)
        percentiles = {}
        for pct in [10, 25, 50, 75, 90]:
            idx = int(len(sorted_eq) * pct / 100)
            idx = min(idx, len(sorted_eq) - 1)
            percentiles[pct] = sorted_eq[idx]

        nut_advantage = nutted - 0.10  # relative to a "typical" range

        return cls(
            range_=range_,
            board=board,
            board_texture=bt,
            frac_nutted=nutted,
            frac_strong=strong,
            frac_medium=medium,
            frac_weak=weak,
            frac_flush_draws=flush_draws,
            frac_straight_draws=straight_draws,
            frac_combo_draws=combo_draws,
            frac_drawing_dead=drawing_dead,
            shape=shape,
            is_capped=is_capped,
            nut_advantage=nut_advantage,
            avg_blocker_score=avg_blocker,
            mean_equity=mean_eq,
            equity_std=std_eq,
            equity_percentiles=percentiles,
        )

    @classmethod
    def _empty(cls, range_: Range, board: Board, bt: BoardTexture) -> RangeProfile:
        return cls(
            range_=range_, board=board, board_texture=bt,
            frac_nutted=0, frac_strong=0, frac_medium=0, frac_weak=1,
            frac_flush_draws=0, frac_straight_draws=0, frac_combo_draws=0, frac_drawing_dead=1,
            shape=RangeShape.CONDENSED, is_capped=True, nut_advantage=-1,
            avg_blocker_score=0, mean_equity=0, equity_std=0,
            equity_percentiles={10: 0, 25: 0, 50: 0, 75: 0, 90: 0},
        )

    def describe(self) -> str:
        parts = [
            f"{self.shape.name.lower()} range",
            f"{self.frac_nutted:.0%} nutted, {self.frac_strong:.0%} strong, "
            f"{self.frac_medium:.0%} medium, {self.frac_weak:.0%} weak",
        ]
        if self.frac_flush_draws > 0.1:
            parts.append(f"flush draw density: {self.frac_flush_draws:.0%}")
        if self.is_capped:
            parts.append("capped (few nut combos)")
        return ". ".join(parts)

    def compare_to(self, other: RangeProfile) -> str:
        lines = []
        if self.nut_advantage > other.nut_advantage + 0.05:
            lines.append("Range A has nut advantage")
        elif other.nut_advantage > self.nut_advantage + 0.05:
            lines.append("Range B has nut advantage")

        if self.is_capped and not other.is_capped:
            lines.append("Range A is capped; Range B has more nut combos")
        elif other.is_capped and not self.is_capped:
            lines.append("Range B is capped; Range A has more nut combos")

        eq_diff = self.mean_equity - other.mean_equity
        if abs(eq_diff) > 0.05:
            better = "A" if eq_diff > 0 else "B"
            lines.append(f"Range {better} has higher average equity")

        return ". ".join(lines) if lines else "Ranges are similar in profile"


def _classify_shape(
    nutted: float, strong: float, medium: float, weak: float,
) -> RangeShape:
    if nutted > 0.15 and weak > 0.30 and medium < 0.25:
        return RangeShape.POLARIZED
    if nutted < 0.05:
        if medium > 0.50:
            return RangeShape.CONDENSED
        return RangeShape.CAPPED
    if abs(nutted - strong) < 0.10 and abs(strong - medium) < 0.10:
        return RangeShape.LINEAR
    return RangeShape.MERGED
