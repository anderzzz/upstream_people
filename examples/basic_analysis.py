"""Demo: analyze a PLO hand on a board, show properties and equity."""
from plo_engine.types import parse_plo_hand, parse_board, Range
from plo_engine.domain import (
    BoardTexture, HandProperties, StartingHandProfile,
)
from plo_engine.equity import equity_hand_vs_range
from plo_engine.ev import pot_odds, evaluate_actions
from plo_engine.utils import format_equity, format_hand_board


def main():
    # Scenario: We hold Ah Ad Kh Ts on a Ks Qh Jc flop
    hand = parse_plo_hand("Ah Ad Kh Ts")
    board = parse_board("Ks Qh Jc")

    print("=" * 60)
    print("PLO Engine — Basic Analysis Demo")
    print("=" * 60)
    print()

    # Starting hand profile
    profile = StartingHandProfile.classify(hand)
    print(f"Starting hand: {profile.describe()}")
    print(f"  Category: {profile.category.name}")
    print(f"  Suit structure: {profile.suit_structure.name}")
    print(f"  Preflop equity estimate: {profile.preflop_equity_estimate:.1%}")
    print()

    # Board texture
    bt = BoardTexture.from_board(board)
    print(f"Board: {bt.describe()}")
    print(f"  Flush draw: {bt.flush_draw.name}")
    print(f"  Connectedness: {bt.connectedness.name}")
    print(f"  Pairedness: {bt.pairedness.name}")
    print(f"  Straight possible: {bt.straight_possible}")
    print()

    # Hand properties on this board
    props = HandProperties.analyze(hand, board)
    print(f"Hand analysis: {props.describe()}")
    print(f"  Made hand: {props.made_hand.name}")
    print(f"  Draws: {props.draws}")
    print(f"  Total outs: {props.total_outs}")
    print(f"  Blocker score: {props.blocker_score:.2f}")
    print(f"  Blocks nut flush: {props.blocks_nut_flush}")
    print()

    # Equity vs a small opponent range
    opp_hands = [
        "Qd Jd 9c 8c",   # two pair + straight draw
        "Th 9h 8d 7d",   # wrap draw
        "Kd Qc 5h 2c",   # top two pair
        "Ac Tc 9d 4s",   # nut straight draw
    ]
    opp_range = Range.from_hands([parse_plo_hand(h) for h in opp_hands])

    print(f"Equity vs {len(opp_range)} opponent combos:")
    result = equity_hand_vs_range(hand, opp_range, board, num_samples=5000)
    print(f"  {format_equity(result)}")
    print()

    # Action EV
    pot = 100.0
    to_call = 75.0
    stack = 500.0

    print(f"Pot: {pot}, To call: {to_call}, Stack: {stack}")
    print(f"Pot odds needed: {pot_odds(pot, to_call):.1%}")
    print()

    actions = evaluate_actions(
        hand, board, opp_range, pot, to_call, stack, num_samples=2000,
    )
    print("Action EVs:")
    for a in actions:
        print(f"  {a.action:>15}: EV = {a.ev:+.1f} chips ({a.ev_bb:+.1f} BB)")


if __name__ == "__main__":
    main()
