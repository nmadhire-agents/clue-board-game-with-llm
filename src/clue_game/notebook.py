"""
Detective Notebook - Deterministic tracking for Clue game deductions.

This is the CRUCIAL tool that prevents LLM hallucination by maintaining
a hard-coded grid of card ownership. The LLM queries this tool instead
of trying to remember card locations from conversation history.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

# Import TOON utilities for token-efficient output
from clue_game.toon_utils import to_toon, TOON_ENABLED


class CardStatus(Enum):
    """Status of a card in relation to a player/envelope."""
    UNKNOWN = "?"      # Don't know if they have it
    HAS = "✓"          # Confirmed they have this card
    NOT_HAS = "✗"      # Confirmed they don't have this card


@dataclass
class NotebookEntry:
    """An entry tracking one card's status across all players."""
    card_name: str
    card_type: str  # 'suspect', 'weapon', 'room'
    # Maps player name -> CardStatus
    player_status: dict[str, CardStatus] = field(default_factory=dict)
    envelope_status: CardStatus = CardStatus.UNKNOWN
    
    def is_solved(self) -> bool:
        """Returns True if we know where this card is."""
        if self.envelope_status == CardStatus.HAS:
            return True
        return any(s == CardStatus.HAS for s in self.player_status.values())
    
    def get_owner(self) -> Optional[str]:
        """Get who owns this card, if known."""
        if self.envelope_status == CardStatus.HAS:
            return "ENVELOPE"
        for player, status in self.player_status.items():
            if status == CardStatus.HAS:
                return player
        return None


class DetectiveNotebook:
    """
    A deterministic notebook that tracks card ownership.
    
    This is the key tool for effective Clue AI - instead of relying on
    the LLM's context memory (which degrades), we maintain a hard-coded
    grid that the LLM queries for accurate information.
    
    Grid structure:
    - Rows: All cards (6 suspects, 6 weapons, 9 rooms = 21 cards)
    - Columns: Each player + "Envelope" (the solution)
    """
    
    def __init__(self, owner_name: str, all_player_names: list[str]):
        """
        Initialize notebook for a specific player.
        
        Args:
            owner_name: The player who owns this notebook
            all_player_names: List of all player names in the game
        """
        self.owner_name = owner_name
        self.all_players = all_player_names
        self.entries: dict[str, NotebookEntry] = {}
        self.suggestion_log: list[dict] = []
        self.turn_log: list[str] = []  # Log of all events
        
        # Initialize all cards
        self._init_cards()
    
    def _init_cards(self):
        """Initialize all card entries."""
        suspects = [
            "Miss Scarlet", "Colonel Mustard", "Mrs. White",
            "Mr. Green", "Mrs. Peacock", "Professor Plum"
        ]
        weapons = [
            "Candlestick", "Knife", "Lead Pipe",
            "Revolver", "Rope", "Wrench"
        ]
        rooms = [
            "Kitchen", "Ballroom", "Conservatory", "Billiard Room",
            "Library", "Study", "Hall", "Lounge", "Dining Room"
        ]
        
        for card in suspects:
            self._add_card(card, "suspect")
        for card in weapons:
            self._add_card(card, "weapon")
        for card in rooms:
            self._add_card(card, "room")
    
    def _add_card(self, card_name: str, card_type: str):
        """Add a card entry to the notebook."""
        entry = NotebookEntry(
            card_name=card_name,
            card_type=card_type,
            player_status={p: CardStatus.UNKNOWN for p in self.all_players}
        )
        self.entries[card_name] = entry
    
    def mark_card(self, card_name: str, player_name: str) -> str:
        """
        Mark that a player HAS a specific card.
        Also marks all other players as NOT having this card.
        
        Args:
            card_name: The card name (e.g., "Candlestick", "Miss Scarlet")
            player_name: The player who has this card
        
        Returns:
            Confirmation message
        """
        if card_name not in self.entries:
            return f"Error: Unknown card '{card_name}'"
        
        entry = self.entries[card_name]
        
        # Mark this player as having the card
        if player_name in entry.player_status:
            entry.player_status[player_name] = CardStatus.HAS
        elif player_name.upper() == "ENVELOPE":
            entry.envelope_status = CardStatus.HAS
        else:
            return f"Error: Unknown player '{player_name}'"
        
        # Mark all OTHER players as NOT having this card
        for other_player in self.all_players:
            if other_player != player_name:
                entry.player_status[other_player] = CardStatus.NOT_HAS
        
        # If a player has it, it's not in the envelope
        if player_name != "ENVELOPE":
            entry.envelope_status = CardStatus.NOT_HAS
        
        self._log(f"MARKED: {player_name} HAS '{card_name}'")
        self._check_deductions()
        
        return f"✓ Marked: {player_name} has '{card_name}'"
    
    def mark_not_has(self, card_name: str, player_name: str) -> str:
        """
        Mark that a player does NOT have a specific card.
        
        Args:
            card_name: The card name
            player_name: The player who doesn't have this card
        
        Returns:
            Confirmation message
        """
        if card_name not in self.entries:
            return f"Error: Unknown card '{card_name}'"
        
        entry = self.entries[card_name]
        
        if player_name in entry.player_status:
            entry.player_status[player_name] = CardStatus.NOT_HAS
        else:
            return f"Error: Unknown player '{player_name}'"
        
        self._log(f"MARKED: {player_name} does NOT have '{card_name}'")
        self._check_deductions()
        
        return f"✗ Marked: {player_name} does NOT have '{card_name}'"
    
    def record_my_cards(self, my_cards: list[str]) -> str:
        """
        Record the cards in my own hand at game start.
        
        Args:
            my_cards: List of card names I was dealt
        
        Returns:
            Confirmation message
        """
        results = []
        for card in my_cards:
            result = self.mark_card(card, self.owner_name)
            results.append(result)
        
        self._log(f"GAME START: Recorded {len(my_cards)} cards in my hand")
        return f"Recorded {len(my_cards)} cards in your hand:\n" + "\n".join(results)
    
    def record_suggestion(
        self,
        turn_number: int,
        suggester: str,
        suspect: str,
        weapon: str,
        room: str,
        disprover: Optional[str] = None,
        card_shown: Optional[str] = None,
        players_who_passed: list[str] = None
    ) -> str:
        """
        Record a suggestion and update the notebook accordingly.
        
        Args:
            turn_number: The turn number
            suggester: Who made the suggestion
            suspect: Suggested suspect
            weapon: Suggested weapon
            room: Suggested room (where suggestion was made)
            disprover: Who disproved it (if any)
            card_shown: The card shown (only if shown to me)
            players_who_passed: Players who couldn't disprove
        
        Returns:
            Summary of deductions made
        """
        suggestion_record = {
            "turn": turn_number,
            "suggester": suggester,
            "suspect": suspect,
            "weapon": weapon,
            "room": room,
            "disprover": disprover,
            "card_shown": card_shown,
            "players_passed": players_who_passed or []
        }
        self.suggestion_log.append(suggestion_record)
        
        deductions = []
        
        # If someone showed ME a card, mark it
        if card_shown and disprover:
            self.mark_card(card_shown, disprover)
            deductions.append(f"✓ {disprover} has '{card_shown}'")
        
        # Players who passed don't have ANY of the suggested cards
        if players_who_passed:
            for player in players_who_passed:
                for card in [suspect, weapon, room]:
                    if self.entries[card].player_status.get(player) == CardStatus.UNKNOWN:
                        self.mark_not_has(card, player)
                        deductions.append(f"✗ {player} doesn't have '{card}' (passed)")
        
        self._log(f"SUGGESTION #{len(self.suggestion_log)}: {suggester} suggested {suspect}/{weapon}/{room}")
        if disprover:
            self._log(f"  -> Disproved by {disprover}" + (f" with '{card_shown}'" if card_shown else ""))
        else:
            self._log(f"  -> NOT DISPROVED! Strong lead!")
        
        self._check_deductions()
        
        result = f"Recorded suggestion #{len(self.suggestion_log)}\n"
        if deductions:
            result += "Deductions made:\n" + "\n".join(deductions)
        else:
            result += "No new deductions from this suggestion."
        
        return result
    
    def _check_deductions(self):
        """
        Run deduction logic to infer new information.
        Called after any update to check for new conclusions.
        """
        changed = True
        while changed:
            changed = False
            
            for card_name, entry in self.entries.items():
                # Deduction 1: If all players marked NOT_HAS, card is in ENVELOPE
                if entry.envelope_status == CardStatus.UNKNOWN:
                    all_not_has = all(
                        s == CardStatus.NOT_HAS 
                        for s in entry.player_status.values()
                    )
                    if all_not_has:
                        entry.envelope_status = CardStatus.HAS
                        self._log(f"DEDUCED: '{card_name}' is in the ENVELOPE!")
                        changed = True
                
                # Deduction 2: If envelope has card, no player has it
                if entry.envelope_status == CardStatus.HAS:
                    for player in self.all_players:
                        if entry.player_status[player] != CardStatus.NOT_HAS:
                            entry.player_status[player] = CardStatus.NOT_HAS
                            changed = True
    
    def get_unknown_cards(self) -> str:
        """
        Get all cards whose location is still unknown.
        Use this when deciding what to suggest.
        
        Returns:
            List of unknown cards grouped by type (TOON or text format)
        """
        unknown = {"suspect": [], "weapon": [], "room": []}
        
        for card_name, entry in self.entries.items():
            if not entry.is_solved():
                unknown[entry.card_type].append(card_name)
        
        if TOON_ENABLED:
            return to_toon({
                "unknown": {
                    "s": unknown["suspect"],
                    "w": unknown["weapon"],
                    "r": unknown["room"]
                },
                "counts": {
                    "s": len(unknown["suspect"]),
                    "w": len(unknown["weapon"]),
                    "r": len(unknown["room"])
                }
            })
        
        result = "UNKNOWN CARDS\n"
        result += f"Suspects({len(unknown['suspect'])}): "
        result += ", ".join(unknown['suspect']) if unknown['suspect'] else "none"
        result += f"\nWeapons({len(unknown['weapon'])}): "
        result += ", ".join(unknown['weapon']) if unknown['weapon'] else "none"
        result += f"\nRooms({len(unknown['room'])}): "
        result += ", ".join(unknown['room']) if unknown['room'] else "none"
        
        return result
    
    def get_possible_solution(self) -> str:
        """
        Get the cards that could possibly be in the envelope (the solution).
        
        Returns:
            Possible solution cards and confidence level (TOON or text format)
        """
        possible = {"suspect": [], "weapon": [], "room": []}
        confirmed = {"suspect": None, "weapon": None, "room": None}
        
        for card_name, entry in self.entries.items():
            # If confirmed in envelope
            if entry.envelope_status == CardStatus.HAS:
                confirmed[entry.card_type] = card_name
            # If not confirmed held by anyone, it COULD be in envelope
            elif entry.envelope_status != CardStatus.NOT_HAS:
                if not any(s == CardStatus.HAS for s in entry.player_status.values()):
                    possible[entry.card_type].append(card_name)
        
        # Check if we can make an accusation
        can_accuse = (
            (confirmed["suspect"] or len(possible["suspect"]) == 1) and
            (confirmed["weapon"] or len(possible["weapon"]) == 1) and
            (confirmed["room"] or len(possible["room"]) == 1)
        )
        
        if TOON_ENABLED:
            final_suspect = confirmed["suspect"] or (possible["suspect"][0] if len(possible["suspect"]) == 1 else None)
            final_weapon = confirmed["weapon"] or (possible["weapon"][0] if len(possible["weapon"]) == 1 else None)
            final_room = confirmed["room"] or (possible["room"][0] if len(possible["room"]) == 1 else None)
            
            data = {
                "can_accuse": can_accuse,
                "confirmed": {k: v for k, v in {"s": confirmed["suspect"], "w": confirmed["weapon"], "r": confirmed["room"]}.items() if v},
                "possible": {
                    "s": possible["suspect"] if len(possible["suspect"]) > 1 else [],
                    "w": possible["weapon"] if len(possible["weapon"]) > 1 else [],
                    "r": possible["room"] if len(possible["room"]) > 1 else []
                }
            }
            if can_accuse:
                data["accuse"] = {"s": final_suspect, "w": final_weapon, "r": final_room}
            return to_toon(data)
        
        result = "POSSIBLE SOLUTION\n"
        
        # Suspect
        if confirmed["suspect"]:
            result += f"S: {confirmed['suspect']} (CONFIRMED)\n"
        elif len(possible["suspect"]) == 1:
            result += f"S: {possible['suspect'][0]} (only 1)\n"
        else:
            result += f"S: {len(possible['suspect'])} options - {', '.join(possible['suspect'])}\n"
        
        # Weapon
        if confirmed["weapon"]:
            result += f"W: {confirmed['weapon']} (CONFIRMED)\n"
        elif len(possible["weapon"]) == 1:
            result += f"W: {possible['weapon'][0]} (only 1)\n"
        else:
            result += f"W: {len(possible['weapon'])} options - {', '.join(possible['weapon'])}\n"
        
        # Room
        if confirmed["room"]:
            result += f"R: {confirmed['room']} (CONFIRMED)\n"
        elif len(possible["room"]) == 1:
            result += f"R: {possible['room'][0]} (only 1)\n"
        else:
            result += f"R: {len(possible['room'])} options - {', '.join(possible['room'])}\n"
        
        if can_accuse:
            final_suspect = confirmed["suspect"] or possible["suspect"][0]
            final_weapon = confirmed["weapon"] or possible["weapon"][0]
            final_room = confirmed["room"] or possible["room"][0]
            result += f"CAN ACCUSE: {final_suspect}, {final_weapon}, {final_room}"
        
        return result
    
    def get_accusation_recommendation(self) -> dict:
        """
        Get the recommended accusation based on notebook deductions.
        
        Returns:
            Dict with 'can_accuse', 'suspect', 'weapon', 'room', and 'reason'
        """
        possible = {"suspect": [], "weapon": [], "room": []}
        confirmed = {"suspect": None, "weapon": None, "room": None}
        
        for card_name, entry in self.entries.items():
            # If confirmed in envelope
            if entry.envelope_status == CardStatus.HAS:
                confirmed[entry.card_type] = card_name
            # If not confirmed held by anyone, it COULD be in envelope
            elif entry.envelope_status != CardStatus.NOT_HAS:
                if not any(s == CardStatus.HAS for s in entry.player_status.values()):
                    possible[entry.card_type].append(card_name)
        
        # Check if we can make an accusation
        can_accuse = (
            (confirmed["suspect"] or len(possible["suspect"]) == 1) and
            (confirmed["weapon"] or len(possible["weapon"]) == 1) and
            (confirmed["room"] or len(possible["room"]) == 1)
        )
        
        if can_accuse:
            return {
                "can_accuse": True,
                "suspect": confirmed["suspect"] or possible["suspect"][0],
                "weapon": confirmed["weapon"] or possible["weapon"][0],
                "room": confirmed["room"] or possible["room"][0],
                "reason": "All three categories narrowed to one option"
            }
        else:
            reasons = []
            if not confirmed["suspect"] and len(possible["suspect"]) != 1:
                reasons.append(f"{len(possible['suspect'])} suspect possibilities remain")
            if not confirmed["weapon"] and len(possible["weapon"]) != 1:
                reasons.append(f"{len(possible['weapon'])} weapon possibilities remain")
            if not confirmed["room"] and len(possible["room"]) != 1:
                reasons.append(f"{len(possible['room'])} room possibilities remain")
            
            return {
                "can_accuse": False,
                "suspect": None,
                "weapon": None,
                "room": None,
                "possible_suspects": possible["suspect"],
                "possible_weapons": possible["weapon"],
                "possible_rooms": possible["room"],
                "reason": "; ".join(reasons) if reasons else "Need more information"
            }
    
    def validate_accusation(self, suspect: str, weapon: str, room: str) -> dict:
        """
        Validate if an accusation makes sense based on notebook knowledge.
        
        Args:
            suspect: The suspect to accuse
            weapon: The weapon to accuse
            room: The room to accuse
            
        Returns:
            Dict with 'valid', 'warnings', and 'recommendation'
        """
        warnings = []
        
        # Check each card against notebook knowledge
        for card_name, card_type in [(suspect, "suspect"), (weapon, "weapon"), (room, "room")]:
            if card_name in self.entries:
                entry = self.entries[card_name]
                
                # If someone has this card, it's definitely NOT the solution
                if any(s == CardStatus.HAS for s in entry.player_status.values()):
                    owner = entry.get_owner()
                    warnings.append(f"❌ {card_name} is held by {owner} - CANNOT be in envelope!")
                
                # If envelope is marked as NOT having it
                if entry.envelope_status == CardStatus.NOT_HAS:
                    warnings.append(f"❌ {card_name} is marked as NOT in envelope!")
        
        recommendation = self.get_accusation_recommendation()
        
        if warnings:
            return {
                "valid": False,
                "warnings": warnings,
                "recommendation": recommendation,
                "message": "Your notebook shows this accusation is WRONG!"
            }
        else:
            return {
                "valid": True,
                "warnings": [],
                "recommendation": recommendation,
                "message": "Accusation is consistent with your notebook knowledge"
            }
    
    def validate_suggestion(self, suspect: str, weapon: str, room: str) -> dict:
        """
        Validate if a suggestion makes strategic sense based on notebook knowledge.
        Suggesting cards that are already known (crossed out) wastes a turn!
        
        Args:
            suspect: The suspect to suggest
            weapon: The weapon to suggest
            room: The room (your current room)
            
        Returns:
            Dict with 'valid', 'warnings', 'wasted_cards', and 'better_alternatives'
        """
        warnings = []
        wasted_cards = []
        alternatives = {"suspect": [], "weapon": [], "room": []}
        
        # Check each card against notebook knowledge
        for card_name, card_type in [(suspect, "suspect"), (weapon, "weapon"), (room, "room")]:
            if card_name in self.entries:
                entry = self.entries[card_name]
                
                # If someone has this card, suggesting it is wasteful
                if any(s == CardStatus.HAS for s in entry.player_status.values()):
                    owner = entry.get_owner()
                    wasted_cards.append(card_name)
                    warnings.append(f"⚠️ {card_name} is already known to be held by {owner} - suggesting it won't give you new info!")
                
                # If envelope is confirmed to NOT have it, also wasteful
                elif entry.envelope_status == CardStatus.NOT_HAS:
                    wasted_cards.append(card_name)
                    warnings.append(f"⚠️ {card_name} is already eliminated from the solution!")
        
        # Find better alternatives (cards still unknown)
        for card_name, entry in self.entries.items():
            if not entry.is_solved() and entry.envelope_status != CardStatus.NOT_HAS:
                if not any(s == CardStatus.HAS for s in entry.player_status.values()):
                    alternatives[entry.card_type].append(card_name)
        
        if warnings:
            return {
                "valid": False,
                "warnings": warnings,
                "wasted_cards": wasted_cards,
                "better_suspects": alternatives["suspect"],
                "better_weapons": alternatives["weapon"],
                "message": "This suggestion includes cards you already know about!"
            }
        else:
            return {
                "valid": True,
                "warnings": [],
                "wasted_cards": [],
                "message": "Good suggestion - all cards are still unknown"
            }

    def get_notebook_grid(self) -> str:
        """
        Get the notebook grid showing all deductions.
        
        Returns:
            Formatted grid of card statuses (TOON or text format)
        """
        if TOON_ENABLED:
            # Build compact TOON representation
            grid_data = []
            for card_type in ["suspect", "weapon", "room"]:
                for card_name, entry in self.entries.items():
                    if entry.card_type == card_type:
                        row = {
                            "c": card_name[:12],  # card (abbreviated)
                            "t": card_type[0]      # type: s/w/r
                        }
                        for player in self.all_players:
                            row[player[:3]] = entry.player_status[player].value
                        row["env"] = entry.envelope_status.value
                        grid_data.append(row)
            return to_toon({"grid": grid_data})
        
        # Compact text format
        result = f"NOTEBOOK ({self.owner_name})\n"
        
        # Header - short names
        header = "Card".ljust(14)
        for player in self.all_players:
            header += player[:3].center(5)
        header += "ENV".center(5)
        result += header + "\n"
        
        for card_type in ["suspect", "weapon", "room"]:
            result += f"[{card_type[0].upper()}]\n"
            for card_name, entry in self.entries.items():
                if entry.card_type == card_type:
                    row = card_name[:13].ljust(14)
                    for player in self.all_players:
                        row += entry.player_status[player].value.center(5)
                    row += entry.envelope_status.value.center(5)
                    result += row + "\n"
        
        return result
    
    def get_suggestion_history(self) -> str:
        """
        Get the history of all suggestions.
        
        Returns:
            Formatted suggestion history (TOON or text format)
        """
        if not self.suggestion_log:
            return "No suggestions recorded."
        
        if TOON_ENABLED:
            # Compact TOON format
            history = []
            for sugg in self.suggestion_log:
                entry = {
                    "t": sugg['turn'],
                    "by": sugg['suggester'][:3],
                    "s": sugg['suspect'],
                    "w": sugg['weapon'],
                    "r": sugg['room']
                }
                if sugg['disprover']:
                    entry["disproved"] = sugg['disprover'][:3]
                if sugg['card_shown']:
                    entry["shown"] = sugg['card_shown']
                if sugg['players_passed']:
                    entry["passed"] = [p[:3] for p in sugg['players_passed']]
                history.append(entry)
            return to_toon({"history": history})
        
        result = "SUGGESTION HISTORY\n"
        for sugg in self.suggestion_log:
            line = f"T{sugg['turn']}:{sugg['suggester'][:3]}>{sugg['suspect'][:8]},{sugg['weapon'][:8]},{sugg['room'][:8]}"
            if sugg['disprover']:
                line += f"|disp:{sugg['disprover'][:3]}"
            else:
                line += "|NOT_DISPROVED"
            result += line + "\n"
        
        return result
    
    def get_turn_log(self) -> str:
        """
        Get the log of all events.
        
        Returns:
            Event log (TOON or text format)
        """
        if not self.turn_log:
            return "No events."
        
        if TOON_ENABLED:
            return to_toon({"events": self.turn_log[-20:]})  # Last 20 events
        
        result = "EVENTS\n"
        for event in self.turn_log[-20:]:  # Last 20
            result += f"- {event}\n"
        
        return result
    
    def _log(self, message: str):
        """Add an event to the log."""
        self.turn_log.append(message)
    
    def get_strategic_suggestion(self, current_room: str) -> str:
        """
        Get a strategic suggestion based on current knowledge.
        Suggests cards that are still unknown to gather information.
        
        Args:
            current_room: The room you're currently in
        
        Returns:
            Recommended suggestion (TOON or text format)
        """
        unknown = {"suspect": [], "weapon": []}
        
        for card_name, entry in self.entries.items():
            if entry.card_type in ["suspect", "weapon"] and not entry.is_solved():
                unknown[entry.card_type].append(card_name)
        
        recommend_s = unknown["suspect"][0] if unknown["suspect"] else None
        recommend_w = unknown["weapon"][0] if unknown["weapon"] else None
        
        if TOON_ENABLED:
            data = {
                "room": current_room,
                "unknown_s": unknown["suspect"],
                "unknown_w": unknown["weapon"]
            }
            if recommend_s and recommend_w:
                data["suggest"] = {"s": recommend_s, "w": recommend_w, "r": current_room}
            return to_toon(data)
        
        result = f"STRATEGIC SUGGESTION ({current_room})\n"
        
        if not unknown["suspect"]:
            result += "All suspects known\n"
        else:
            result += f"Unknown S: {', '.join(unknown['suspect'])}\n"
            result += f"Recommend S: {recommend_s}\n"
        
        if not unknown["weapon"]:
            result += "All weapons known\n"
        else:
            result += f"Unknown W: {', '.join(unknown['weapon'])}\n"
            result += f"Recommend W: {recommend_w}\n"
        
        if recommend_s and recommend_w:
            result += f"SUGGEST: {recommend_s}, {recommend_w}, {current_room}"
        
        return result


# Global storage for player notebooks
_player_notebooks: dict[str, DetectiveNotebook] = {}


def get_notebook(player_name: str, all_players: list[str] = None) -> DetectiveNotebook:
    """Get or create a player's notebook."""
    global _player_notebooks
    if player_name not in _player_notebooks:
        if all_players is None:
            all_players = ["Scarlet", "Mustard", "Green", "Peacock", "Plum", "White"]
        _player_notebooks[player_name] = DetectiveNotebook(player_name, all_players)
    return _player_notebooks[player_name]


def reset_notebook(player_name: str):
    """Reset a specific player's notebook."""
    global _player_notebooks
    if player_name in _player_notebooks:
        del _player_notebooks[player_name]


def reset_all_notebooks():
    """Reset all notebooks for a new game."""
    global _player_notebooks
    _player_notebooks = {}


def update_all_notebooks_card_shown(card_name: str, card_holder: str) -> None:
    """
    Update all player notebooks when a card is revealed.
    
    This is called when:
    - A suggestion is disproved and a card is shown
    - A magnifying glass clue reveals who holds a card
    
    All players will mark that the card holder has this card,
    which means it's not in the solution envelope.
    
    Args:
        card_name: The name of the card that was shown
        card_holder: The name of the player who holds this card
    """
    global _player_notebooks
    for player_name, notebook in _player_notebooks.items():
        try:
            notebook.mark_card(card_name, card_holder)
        except Exception:
            # If notebook doesn't have this card tracked yet, skip
            pass
