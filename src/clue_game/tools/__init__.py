"""Clue Game Tools Package - Based on Official Clue/Cluedo Rules"""

from clue_game.tools.game_tools import (
    get_my_cards,
    get_current_location,
    get_available_moves,
    roll_dice,
    move_to_room,
    make_suggestion,
    make_accusation,
    get_game_status,
    get_suggestion_history,
    get_my_knowledge,
    get_valid_options,
)

from clue_game.tools.notebook_tools import (
    initialize_notebook,
    mark_player_has_card,
    mark_player_not_has_card,
    record_suggestion_in_notebook,
    get_unknown_cards,
    get_possible_solution,
    view_notebook_grid,
    get_notebook_suggestion_history,
    get_strategic_suggestion,
    get_event_log,
)

__all__ = [
    # Game tools (official rules)
    "get_my_cards",
    "get_current_location",
    "get_available_moves",
    "roll_dice",
    "move_to_room",
    "make_suggestion",
    "make_accusation",
    "get_game_status",
    "get_suggestion_history",
    "get_my_knowledge",
    "get_valid_options",
    # Notebook tools (deterministic tracking)
    "initialize_notebook",
    "mark_player_has_card",
    "mark_player_not_has_card",
    "record_suggestion_in_notebook",
    "get_unknown_cards",
    "get_possible_solution",
    "view_notebook_grid",
    "get_notebook_suggestion_history",
    "get_strategic_suggestion",
    "get_event_log",
]
