"""ASCII table rendering for the PLO CLI."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from plo_engine.types import cards_to_str
from plo_engine.betting import ActionType, HandPhase

if TYPE_CHECKING:
    from plo_engine.player import PlayerView, OpponentView
    from plo_engine.betting import Action
    from plo_engine.hand_history import HandHistory


# ---------------------------------------------------------------------------
# ANSI helpers
# ---------------------------------------------------------------------------

SUIT_COLORS = {
    "c": "\033[32m",   # clubs = green
    "d": "\033[34m",   # diamonds = blue
    "h": "\033[31m",   # hearts = red
    "s": "\033[37m",   # spades = white/default
}
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


def _colorize_cards(card_str: str) -> str:
    """Add ANSI color codes to card strings based on suit."""
    tokens = card_str.split()
    colored = []
    for tok in tokens:
        if len(tok) == 2:
            suit_char = tok[1]
            color = SUIT_COLORS.get(suit_char, "")
            colored.append(f"{BOLD}{color}{tok}{RESET}")
        else:
            colored.append(tok)
    return " ".join(colored)


def clear_screen() -> None:
    """Clear the terminal screen."""
    print("\033[2J\033[H", end="")


# ---------------------------------------------------------------------------
# Table display
# ---------------------------------------------------------------------------

def display_table(view: PlayerView) -> None:
    """Render the full table state as ASCII art."""
    width = 56

    # Phase label
    phase_labels = {
        HandPhase.PREFLOP_BETTING: "PREFLOP",
        HandPhase.FLOP_BETTING: "FLOP",
        HandPhase.TURN_BETTING: "TURN",
        HandPhase.RIVER_BETTING: "RIVER",
        HandPhase.SHOWDOWN: "SHOWDOWN",
    }
    phase_str = phase_labels.get(view.hand_phase, view.hand_phase.name)

    # Top border
    print(f"\n{'':>2}{BOLD}{'':=<{width}}{RESET}")
    print(f"{'':>2}|{'PLO TABLE':^{width - 2}}|")
    print(f"{'':>2}|{phase_str:^{width - 2}}|")
    print(f"{'':>2}|{'':─<{width - 2}}|")

    # Board
    if view.board:
        board_str = _colorize_cards(cards_to_str(view.board))
        # For centering, use the raw length (without ANSI codes)
        raw_board = cards_to_str(view.board)
        board_display = f"[ {board_str} ]"
        # Pad manually since ANSI codes break centering
        raw_len = len(f"[ {raw_board} ]")
        pad_left = (width - 2 - raw_len) // 2
        pad_right = width - 2 - raw_len - pad_left
        print(f"{'':>2}|{' ' * pad_left}{board_display}{' ' * pad_right}|")
    else:
        print(f"{'':>2}|{'[ no board ]':^{width - 2}}|")

    # Pot
    pot_str = f"Pot: ${view.pot_total:.0f}"
    print(f"{'':>2}|{pot_str:^{width - 2}}|")
    print(f"{'':>2}|{'':─<{width - 2}}|")

    # Opponents
    for opp in view.opponents:
        _render_opponent(opp, width)

    # Separator
    print(f"{'':>2}|{'':─<{width - 2}}|")

    # Human player (hero)
    hero_cards = _colorize_cards(cards_to_str(view.my_hole_cards))
    raw_hero = cards_to_str(view.my_hole_cards)

    arrow = f"{BOLD}->  You{RESET}"
    stack_str = f"${view.my_stack:.0f}"
    chips_str = f"(in pot: ${view.my_chips_in_pot:.0f})" if view.my_chips_in_pot > 0 else ""

    # Line 1: name + stack
    hero_line = f"->  You    {stack_str}  {chips_str}"
    raw_hero_line_len = len(hero_line)
    # Rebuild with bold arrow
    hero_line_display = f"{BOLD}->{RESET}  {BOLD}You{RESET}    {stack_str}  {chips_str}"
    pad = width - 2 - raw_hero_line_len
    print(f"{'':>2}|{hero_line_display}{' ' * max(0, pad)}|")

    # Line 2: cards
    card_line = f"    [{raw_hero}]"
    card_line_display = f"    [{hero_cards}]"
    raw_len = len(card_line)
    pad = width - 2 - raw_len
    print(f"{'':>2}|{card_line_display}{' ' * max(0, pad)}|")

    # Bottom border
    print(f"{'':>2}{'':=<{width}}")

    # Blinds info
    bl = view.blind_level
    print(f"{'':>2}  Blinds: {bl.small_blind:.0f}/{bl.big_blind:.0f}"
          f"   |   To call: ${view.current_bet - view.my_chips_in_pot:.0f}"
          f"   |   Pot limit: ${view.pot_limit_max:.0f}")
    print()


def _render_opponent(opp: OpponentView, width: int) -> None:
    """Render a single opponent row."""
    # Status flags
    if opp.is_folded:
        status = f"{DIM}[folded]{RESET}"
        status_raw = "[folded]"
    elif opp.is_all_in:
        status = f"{BOLD}[ALL-IN]{RESET}"
        status_raw = "[ALL-IN]"
    else:
        status = ""
        status_raw = ""

    # Cards
    if opp.hole_cards is not None:
        # Showdown — reveal cards
        card_str = _colorize_cards(cards_to_str(opp.hole_cards))
        raw_card = cards_to_str(opp.hole_cards)
        cards_display = f"[{card_str}]"
        raw_cards = f"[{raw_card}]"
    else:
        cards_display = "[## ## ## ##]"
        raw_cards = "[## ## ## ##]"

    stack_str = f"${opp.stack:.0f}"
    chips_str = f"(${opp.chips_in_pot:.0f})" if opp.chips_in_pot > 0 else ""

    # Build line
    raw_line = f"    {opp.name:<10} {stack_str:>8}  {chips_str:<8} {raw_cards}  {status_raw}"
    display_line = f"    {opp.name:<10} {stack_str:>8}  {chips_str:<8} {cards_display}  {status}"

    raw_len = len(raw_line)
    pad = width - 2 - raw_len
    print(f"{'':>2}|{display_line}{' ' * max(0, pad)}|")


# ---------------------------------------------------------------------------
# Action display
# ---------------------------------------------------------------------------

def display_actions(actions: list[Action]) -> None:
    """Show numbered list of legal actions."""
    print(f"  {BOLD}Legal actions:{RESET}")
    for i, action in enumerate(actions, 1):
        desc = _describe_action(action)
        print(f"    {BOLD}{i}{RESET}. {desc}")


def _describe_action(action: Action) -> str:
    """Human-friendly description of an action."""
    at = action.action_type

    if at == ActionType.FOLD:
        return "Fold"
    elif at == ActionType.CHECK:
        return "Check"
    elif at == ActionType.CALL:
        suffix = " (all-in)" if action.is_all_in else ""
        return f"Call ${action.amount:.0f}{suffix}"
    elif at == ActionType.BET:
        suffix = " (all-in)" if action.is_all_in else ""
        return f"Bet ${action.amount:.0f}{suffix}"
    elif at == ActionType.RAISE:
        suffix = " (all-in)" if action.is_all_in else ""
        return f"Raise to ${action.amount:.0f}{suffix}"
    else:
        return action.describe()


# ---------------------------------------------------------------------------
# Results and standings
# ---------------------------------------------------------------------------

def display_hand_result(history: HandHistory) -> None:
    """Show hand outcome."""
    print(f"  {BOLD}Hand Result{RESET}")
    print(f"  {'':─<40}")

    # Use describe() for the full narrative
    desc = history.describe()
    # Extract just the results section for brevity
    in_results = False
    for line in desc.split("\n"):
        if "*** RESULTS ***" in line:
            in_results = True
            continue
        if in_results:
            # Color profit/loss
            if "+" in line and any(c.isdigit() for c in line):
                print(f"  \033[32m{line}\033[0m")  # green for profit
            elif line.strip().startswith("Seat") and "-" in line:
                print(f"  \033[31m{line}\033[0m")  # red for loss
            else:
                print(f"  {line}")

    # Show board if there was one
    if history.board_cards:
        board_str = _colorize_cards(cards_to_str(history.board_cards))
        print(f"\n  Board: [{board_str}]")

    # Show net profit for hero (seat 0 assumed)
    for seat, profit in sorted(history.result.net_profit.items()):
        name = history.table_config.get("names", {}).get(str(seat), f"Seat {seat}")
        if name == "You":
            if profit > 0:
                print(f"\n  \033[32m{BOLD}You won ${profit:.0f}!{RESET}\033[0m")
            elif profit < 0:
                print(f"\n  \033[31mYou lost ${abs(profit):.0f}.{RESET}\033[0m")
            else:
                print(f"\n  You broke even.")
            break


def display_standings(standings: list[tuple[str, float]]) -> None:
    """Show player chip counts as a leaderboard."""
    print(f"  {BOLD}Standings{RESET}")
    print(f"  {'':─<30}")
    for i, (name, stack) in enumerate(standings, 1):
        marker = " <--" if name == "You" else ""
        print(f"  {i}. {name:<12} ${stack:>8.0f}{marker}")
    print()


def display_welcome() -> None:
    """Print welcome banner."""
    print()
    print(f"  {BOLD}{'':=<44}{RESET}")
    print(f"  {BOLD}|{'PLO POKER':^42}|{RESET}")
    print(f"  {BOLD}|{'Pot-Limit Omaha':^42}|{RESET}")
    print(f"  {BOLD}{'':=<44}{RESET}")
    print()
    print("  Welcome to PLO Poker!")
    print("  You will be dealt 4 hole cards. Use exactly 2 hole cards")
    print("  and 3 board cards to make the best 5-card hand.")
    print("  Betting is pot-limit: max raise = size of the pot.")
    print()
