"""
TOON Format Utilities - Token-efficient output formatting.

TOON (Token-Oriented Object Notation) reduces token usage by 30-60% vs JSON.
This module provides utilities to format notebook and game tool outputs
in TOON format for more efficient LLM communication.

See: https://github.com/toon-format/toon
"""

import os
from typing import Any

# Check if TOON formatting is enabled (default: enabled)
TOON_ENABLED = os.environ.get("CLUE_TOON_ENABLED", "true").lower() in ("1", "true", "yes")

try:
    from toon_format import encode as toon_encode
    TOON_AVAILABLE = True
except ImportError:
    TOON_AVAILABLE = False
    toon_encode = None


def to_toon(data: Any, fallback_str: str = None) -> str:
    """
    Convert data to TOON format for token-efficient LLM output.
    
    Args:
        data: Dict, list, or other serializable data
        fallback_str: Optional string to return if TOON encoding fails
        
    Returns:
        TOON-formatted string (or fallback/original if TOON unavailable)
    """
    if not TOON_AVAILABLE or not TOON_ENABLED:
        if fallback_str is not None:
            return fallback_str
        # Return simple string representation if no fallback
        return str(data) if not isinstance(data, str) else data
    
    try:
        return toon_encode(data)
    except Exception:
        # Fallback to simple representation on encoding error
        if fallback_str is not None:
            return fallback_str
        return str(data) if not isinstance(data, str) else data


def format_notebook_status(
    owner: str,
    possible_solution: dict,
    unknown_counts: dict,
    can_accuse: bool
) -> str:
    """
    Format notebook status in compact TOON format.
    
    Args:
        owner: Player name
        possible_solution: Dict with suspect/weapon/room possibilities
        unknown_counts: Dict with counts of unknown cards per type
        can_accuse: Whether player can make an accusation
        
    Returns:
        TOON-formatted status string
    """
    data = {
        "owner": owner,
        "status": "READY_TO_ACCUSE" if can_accuse else "INVESTIGATING",
        "unknown": unknown_counts,
        "possible": possible_solution
    }
    return to_toon(data)


def format_suggestion_result(
    suggester: str,
    suspect: str,
    weapon: str,
    room: str,
    disprover: str = None,
    card_shown: str = None,
    passed: list = None
) -> str:
    """
    Format suggestion result in compact TOON format.
    
    Returns:
        TOON-formatted result
    """
    data = {
        "by": suggester,
        "s": suspect,  # suspect (abbreviated)
        "w": weapon,   # weapon
        "r": room,     # room
    }
    if disprover:
        data["disproved_by"] = disprover
    if card_shown:
        data["shown"] = card_shown
    if passed:
        data["passed"] = passed
        
    return to_toon(data)


def format_card_grid(cards_by_type: dict, players: list) -> str:
    """
    Format the notebook card grid in TOON's tabular array format.
    
    Args:
        cards_by_type: Dict mapping card_type -> list of card dicts
        players: List of player names
        
    Returns:
        TOON-formatted grid
    """
    # Build tabular data for efficient TOON encoding
    rows = []
    for card_type in ["suspect", "weapon", "room"]:
        for card in cards_by_type.get(card_type, []):
            row = {"card": card["name"][:12], "type": card_type[0]}
            for p in players:
                row[p[:3]] = card["status"].get(p, "?")
            row["ENV"] = card.get("envelope", "?")
            rows.append(row)
    
    return to_toon({"grid": rows})


def format_strategic_suggestion(
    room: str,
    recommend_suspect: str = None,
    recommend_weapon: str = None,
    unknown_suspects: list = None,
    unknown_weapons: list = None
) -> str:
    """
    Format strategic suggestion recommendation in TOON format.
    """
    data = {
        "room": room,
        "recommend": {}
    }
    if recommend_suspect:
        data["recommend"]["suspect"] = recommend_suspect
    if recommend_weapon:
        data["recommend"]["weapon"] = recommend_weapon
    if unknown_suspects:
        data["unknown_suspects"] = unknown_suspects
    if unknown_weapons:
        data["unknown_weapons"] = unknown_weapons
        
    return to_toon(data)


def format_accusation_recommendation(
    can_accuse: bool,
    suspect: str = None,
    weapon: str = None,
    room: str = None,
    reason: str = None,
    possible_suspects: list = None,
    possible_weapons: list = None,
    possible_rooms: list = None
) -> str:
    """
    Format accusation recommendation in TOON format.
    """
    if can_accuse:
        return to_toon({
            "can_accuse": True,
            "accuse": {"s": suspect, "w": weapon, "r": room}
        })
    else:
        data = {"can_accuse": False, "reason": reason}
        if possible_suspects:
            data["possible_s"] = possible_suspects
        if possible_weapons:
            data["possible_w"] = possible_weapons
        if possible_rooms:
            data["possible_r"] = possible_rooms
        return to_toon(data)


def format_game_status(
    turn: int,
    current_player: str,
    players_status: list,
    winner: str = None,
    game_over: bool = False
) -> str:
    """
    Format game status in TOON format.
    """
    data = {
        "turn": turn,
        "current": current_player,
        "players": players_status
    }
    if winner:
        data["winner"] = winner
    if game_over:
        data["game_over"] = True
    return to_toon(data)


def format_available_moves(
    current_location: str,
    dice_roll: int = None,
    reachable_rooms: list = None,
    secret_passage: str = None,
    recommended: list = None,
    avoid: list = None
) -> str:
    """
    Format available moves in TOON format.
    """
    data = {
        "at": current_location,
        "moves": reachable_rooms or []
    }
    if dice_roll:
        data["dice"] = dice_roll
    if secret_passage:
        data["passage"] = secret_passage
    if recommended:
        data["recommended"] = recommended
    if avoid:
        data["avoid"] = avoid
    return to_toon(data)
