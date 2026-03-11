"""Human action input from stdin."""

from __future__ import annotations

from plo_engine.player import PlayerView
from plo_engine.betting import Action
from cli.display import display_table, display_actions


def get_human_action(view: PlayerView) -> Action:
    """Display state and prompt for action selection.

    This is the callback for HumanPlayer.
    """
    display_table(view)
    display_actions(view.legal_actions)

    while True:
        try:
            raw = input("\n  Your action [1-{}]: ".format(len(view.legal_actions)))
            choice = int(raw.strip())
            if 1 <= choice <= len(view.legal_actions):
                return view.legal_actions[choice - 1]
        except (ValueError, EOFError):
            pass
        print("  Invalid choice. Try again.")
