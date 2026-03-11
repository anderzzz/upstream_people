"""PLO Poker CLI -- play against AI opponents."""

from __future__ import annotations

import argparse
import sys

from plo_engine.player import HumanPlayer, RandomPlayer, CallingStation
from plo_engine.tournament import Session, SessionConfig, SessionMode
from plo_engine.table import BlindLevel, BlindStructure
from plo_engine.hand_history import build_hand_history
from cli.display import display_welcome, display_hand_result, display_standings, clear_screen
from cli.input_handler import get_human_action


def parse_blinds(blinds_str: str) -> BlindStructure:
    """Parse 'SB/BB' string into a single-level BlindStructure."""
    parts = blinds_str.split("/")
    sb, bb = float(parts[0]), float(parts[1])
    return BlindStructure(levels=[BlindLevel(small_blind=sb, big_blind=bb, ante=0)])


def create_bots(bot_type: str, count: int) -> list:
    """Create AI opponents of the specified type."""
    bots = []
    for i in range(count):
        name = f"Bot-{i + 1}"
        if bot_type == "random":
            bots.append(RandomPlayer(name, seed=42 + i))
        elif bot_type == "calling":
            bots.append(CallingStation(name))
        elif bot_type == "heuristic":
            try:
                from plo_engine.players.heuristic_player import HeuristicPlayer
                bots.append(HeuristicPlayer(name, seed=42 + i))
            except ImportError:
                print(f"  Heuristic player not available, using random for {name}")
                bots.append(RandomPlayer(name, seed=42 + i))
        else:
            bots.append(RandomPlayer(name, seed=42 + i))
    return bots


def main():
    parser = argparse.ArgumentParser(description="PLO Poker -- Play against AI opponents")
    parser.add_argument("--opponents", type=int, default=2,
                        help="Number of opponents (1-5)")
    parser.add_argument("--bot-type", choices=["random", "calling", "heuristic"],
                        default="random", help="AI opponent type")
    parser.add_argument("--stack", type=float, default=1000,
                        help="Starting stack")
    parser.add_argument("--blinds", type=str, default="5/10",
                        help="Blinds as SB/BB")
    parser.add_argument("--hands", type=int, default=None,
                        help="Number of hands (None=unlimited)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")
    args = parser.parse_args()

    num_opponents = max(1, min(5, args.opponents))

    human = HumanPlayer("You", input_callback=get_human_action)
    bots = create_bots(args.bot_type, num_opponents)
    players = [human] + bots

    blind_structure = parse_blinds(args.blinds)
    config = SessionConfig(
        mode=SessionMode.CASH_GAME,
        num_seats=len(players),
        starting_stack=args.stack,
        blind_structure=blind_structure,
        num_hands=args.hands,
        master_seed=args.seed,
    )
    session = Session(config, players)

    display_welcome()
    print(f"  Playing {num_opponents} opponent(s) ({args.bot_type}), "
          f"blinds {args.blinds}, stack ${args.stack:.0f}\n")

    hand_num = 0
    try:
        while True:
            hand_num += 1
            clear_screen()
            print(f"\n  {'=' * 50}")
            print(f"    Hand #{hand_num}")
            print(f"  {'=' * 50}\n")

            history = session.run_one_hand()

            # Show result
            print(f"\n  {'=' * 50}")
            display_hand_result(history)
            print()
            display_standings(session.standings())

            # Check if session should stop
            if session._should_stop():
                print("  Session complete!")
                break

            # Prompt to continue
            try:
                resp = input("  Press Enter to continue (q to quit): ")
                if resp.strip().lower() == "q":
                    break
            except (EOFError, KeyboardInterrupt):
                break
    except KeyboardInterrupt:
        pass

    print("\n  Thanks for playing!")
    display_standings(session.standings())


if __name__ == "__main__":
    main()
