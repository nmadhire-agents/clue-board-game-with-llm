"""
Clue Board Game with LLM Agents
A multi-agent CrewAI implementation of the classic Clue/Cluedo board game.
"""

from clue_game.game_state import GameState, get_game_state, reset_game_state
from clue_game.crew import ClueGameCrew

__all__ = [
    "GameState",
    "get_game_state",
    "reset_game_state",
    "ClueGameCrew",
]


def main() -> None:
    """Entry point for the clue game."""
    from clue_game.main import main as run_main
    run_main()
