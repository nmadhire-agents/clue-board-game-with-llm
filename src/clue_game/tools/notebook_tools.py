"""
Detective Notebook Tools - CrewAI tools for the deterministic notebook.

These tools allow agents to interact with their Detective Notebook,
which maintains a hard-coded grid of card ownership instead of relying
on LLM memory (which degrades over time).
"""

from crewai.tools import tool
from clue_game.notebook import get_notebook, DetectiveNotebook
from clue_game.game_state import get_game_state


@tool("Initialize My Notebook")
def initialize_notebook(player_name: str) -> str:
    """
    Initialize your detective notebook at the start of the game.
    This records your hand cards and sets up tracking for all cards.
    CALL THIS FIRST at the start of your first turn!
    
    Args:
        player_name: Your player name
    
    Returns:
        Confirmation of notebook initialization with your cards recorded
    """
    game_state = get_game_state()
    player = game_state.get_player_by_name(player_name)
    
    if not player:
        return f"Error: Player {player_name} not found"
    
    all_players = [p.name for p in game_state.players]
    notebook = get_notebook(player_name, all_players)
    
    # Record my own cards
    my_card_names = [c.name for c in player.cards]
    notebook.record_my_cards(my_card_names)
    
    result = f"✓ Notebook initialized for {player_name}\n\n"
    result += f"Your cards ({len(my_card_names)} total):\n"
    for card in player.cards:
        result += f"  - {card.name} ({card.card_type})\n"
    result += "\nThese cards are marked as YOURS and eliminated from the solution."
    result += "\n\nUse 'View Notebook Grid' to see your full deduction grid."
    
    return result


@tool("Mark Player Has Card")
def mark_player_has_card(player_name: str, card_name: str, owner_player: str) -> str:
    """
    Mark that a specific player HAS a card. Use this when:
    - Someone shows you a card to disprove your suggestion
    - You deduce that a player must have a specific card
    
    Args:
        player_name: YOUR player name (notebook owner)
        card_name: The card name (e.g., "Candlestick", "Miss Scarlet", "Kitchen")
        owner_player: The player who has this card
    
    Returns:
        Confirmation and any new deductions made
    """
    notebook = get_notebook(player_name)
    result = notebook.mark_card(card_name, owner_player)
    
    # Check if this leads to any solution deductions
    possible = notebook.get_possible_solution()
    if "CONFIRMED" in possible or "only possibility" in possible:
        result += "\n\n⚡ This deduction may have narrowed the solution!\n"
        result += possible
    
    return result


@tool("Mark Player Does Not Have Card")
def mark_player_not_has_card(player_name: str, card_name: str, other_player: str) -> str:
    """
    Mark that a player does NOT have a card. Use this when:
    - A player passes (can't disprove) on a suggestion containing this card
    
    Args:
        player_name: YOUR player name (notebook owner)
        card_name: The card name
        other_player: The player who doesn't have this card
    
    Returns:
        Confirmation and any new deductions made
    """
    notebook = get_notebook(player_name)
    return notebook.mark_not_has(card_name, other_player)


@tool("Record Suggestion In Notebook")
def record_suggestion_in_notebook(
    player_name: str,
    suggester: str,
    suspect: str,
    weapon: str,
    room: str,
    disprover: str = "",
    card_shown: str = "",
    players_who_passed: str = ""
) -> str:
    """
    Record a suggestion and all resulting information in your notebook.
    This is the MAIN tool for tracking game events!
    
    Args:
        player_name: YOUR player name (notebook owner)
        suggester: Who made the suggestion
        suspect: The suspected person
        weapon: The suspected weapon
        room: The room where suggestion was made
        disprover: Who disproved it (empty if not disproved)
        card_shown: The card shown to YOU (only if you were the suggester)
        players_who_passed: Comma-separated list of players who couldn't disprove
    
    Returns:
        Summary of all deductions made from this suggestion
    """
    game_state = get_game_state()
    notebook = get_notebook(player_name)
    
    passed_list = [p.strip() for p in players_who_passed.split(",") if p.strip()]
    
    result = notebook.record_suggestion(
        turn_number=game_state.turn_number,
        suggester=suggester,
        suspect=suspect,
        weapon=weapon,
        room=room,
        disprover=disprover if disprover else None,
        card_shown=card_shown if card_shown else None,
        players_who_passed=passed_list
    )
    
    return result


@tool("Get Unknown Cards")
def get_unknown_cards(player_name: str) -> str:
    """
    Get all cards whose location is still UNKNOWN.
    Use this when deciding what to suggest - suggest unknown cards to gather info!
    
    Args:
        player_name: YOUR player name
    
    Returns:
        List of unknown cards grouped by type (suspect/weapon/room)
    """
    notebook = get_notebook(player_name)
    return notebook.get_unknown_cards()


@tool("Get Possible Solution")
def get_possible_solution(player_name: str) -> str:
    """
    Get the cards that could possibly be in the envelope (the solution).
    Shows which suspects, weapons, and rooms haven't been eliminated.
    
    IMPORTANT: If each category has only ONE possibility, you should ACCUSE!
    
    Args:
        player_name: YOUR player name
    
    Returns:
        Possible solution cards and whether you can make an accusation
    """
    notebook = get_notebook(player_name)
    return notebook.get_possible_solution()


@tool("View Notebook Grid")
def view_notebook_grid(player_name: str) -> str:
    """
    View your complete detective notebook grid.
    Shows the status of every card for every player.
    
    Legend:
    - ✓ = Player HAS this card
    - ✗ = Player does NOT have this card  
    - ? = Unknown
    
    Args:
        player_name: YOUR player name
    
    Returns:
        Full notebook grid with all deductions
    """
    notebook = get_notebook(player_name)
    return notebook.get_notebook_grid()


@tool("Get Suggestion History From Notebook")
def get_notebook_suggestion_history(player_name: str) -> str:
    """
    Get the history of all suggestions recorded in your notebook.
    
    Args:
        player_name: YOUR player name
    
    Returns:
        Complete suggestion history with outcomes
    """
    notebook = get_notebook(player_name)
    return notebook.get_suggestion_history()


@tool("Get Strategic Suggestion")
def get_strategic_suggestion(player_name: str, current_room: str) -> str:
    """
    Get a recommended suggestion based on your current knowledge.
    The notebook analyzes which cards are still unknown and suggests
    ones that will give you the most information.
    
    Args:
        player_name: YOUR player name
        current_room: The room you're currently in
    
    Returns:
        Recommended suspect and weapon to suggest in your current room
    """
    notebook = get_notebook(player_name)
    return notebook.get_strategic_suggestion(current_room)


@tool("Get Accusation Recommendation")
def get_accusation_recommendation(player_name: str) -> str:
    """
    Check if you have enough information to make an accusation.
    Analyzes your notebook to determine which cards are NOT crossed out
    and could be the solution.
    
    IMPORTANT: Only accuse when this returns 'can_accuse: True'!
    Accusing cards that are crossed out in your notebook will be BLOCKED.
    
    Args:
        player_name: YOUR player name
    
    Returns:
        Whether you can accuse, and if so, the recommended accusation
    """
    notebook = get_notebook(player_name)
    rec = notebook.get_accusation_recommendation()
    
    if rec["can_accuse"]:
        result = "🎯 YOU CAN MAKE AN ACCUSATION!\n\n"
        result += f"Based on your notebook, the solution is:\n"
        result += f"  SUSPECT: {rec['suspect']}\n"
        result += f"  WEAPON: {rec['weapon']}\n"
        result += f"  ROOM: {rec['room']}\n\n"
        result += "Use 'Make Accusation' with these exact values to win!"
    else:
        result = "⚠️ NOT READY TO ACCUSE YET\n\n"
        result += f"Reason: {rec['reason']}\n\n"
        if rec.get("possible_suspects"):
            result += f"Possible suspects: {', '.join(rec['possible_suspects'])}\n"
        if rec.get("possible_weapons"):
            result += f"Possible weapons: {', '.join(rec['possible_weapons'])}\n"
        if rec.get("possible_rooms"):
            result += f"Possible rooms: {', '.join(rec['possible_rooms'])}\n"
        result += "\nKeep making suggestions to narrow down the possibilities!"
    
    return result


@tool("Get Event Log")
def get_event_log(player_name: str) -> str:
    """
    Get the complete event log from your notebook.
    Shows all deductions and markings made throughout the game.
    
    Args:
        player_name: YOUR player name
    
    Returns:
        Complete chronological event log
    """
    notebook = get_notebook(player_name)
    return notebook.get_turn_log()
