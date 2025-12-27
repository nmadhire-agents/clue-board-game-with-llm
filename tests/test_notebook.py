"""
Tests for Detective Notebook
Tests deterministic tracking to prevent LLM "forgetting".
"""

import pytest
from clue_game.notebook import (
    DetectiveNotebook,
    CardStatus,
    get_notebook,
    reset_notebook,
    reset_all_notebooks,
    update_all_notebooks_card_shown,
)
from clue_game.game_state import Room, Suspect, Weapon


class TestNotebookInitialization:
    """Test notebook setup."""
    
    def test_create_notebook(self):
        """Should create a notebook for a player."""
        notebook = DetectiveNotebook("Test", ["P1", "P2", "P3"])
        assert notebook.owner_name == "Test"
        assert "P1" in notebook.all_players
        assert "P2" in notebook.all_players
        assert "P3" in notebook.all_players
    
    def test_all_cards_tracked(self):
        """All 21 cards should be in the notebook."""
        notebook = DetectiveNotebook("Test", ["P1"])
        
        # 6 suspects + 6 weapons + 9 rooms = 21
        assert len(notebook.entries) == 21
    
    def test_initial_status_unknown(self):
        """All cards should start as UNKNOWN."""
        notebook = DetectiveNotebook("Test", ["P1", "P2"])
        
        for card_name, entry in notebook.entries.items():
            for player in notebook.all_players:
                status = entry.player_status[player]
                assert status == CardStatus.UNKNOWN


class TestMarkingCards:
    """Test card marking functionality."""
    
    def test_mark_player_has_card(self):
        """Should mark a player as having a card."""
        notebook = DetectiveNotebook("Test", ["P1", "P2"])
        notebook.mark_card("Miss Scarlet", "P1")
        
        assert notebook.entries["Miss Scarlet"].player_status["P1"] == CardStatus.HAS
    
    def test_mark_has_sets_others_to_not_has(self):
        """If player HAS a card, others should NOT have it."""
        notebook = DetectiveNotebook("Test", ["P1", "P2", "P3"])
        notebook.mark_card("Miss Scarlet", "P1")
        
        assert notebook.entries["Miss Scarlet"].player_status["P1"] == CardStatus.HAS
        assert notebook.entries["Miss Scarlet"].player_status["P2"] == CardStatus.NOT_HAS
        assert notebook.entries["Miss Scarlet"].player_status["P3"] == CardStatus.NOT_HAS
        assert notebook.entries["Miss Scarlet"].envelope_status == CardStatus.NOT_HAS
    
    def test_mark_not_has(self):
        """Should mark a player as NOT having a card."""
        notebook = DetectiveNotebook("Test", ["P1", "P2"])
        notebook.mark_not_has("Miss Scarlet", "P1")
        
        assert notebook.entries["Miss Scarlet"].player_status["P1"] == CardStatus.NOT_HAS


class TestRecordingMyCards:
    """Test recording the player's own cards."""
    
    def test_record_my_cards(self):
        """Should record all cards the player holds."""
        notebook = DetectiveNotebook("Test", ["Test", "P2", "P3"])
        my_cards = ["Miss Scarlet", "Knife", "Library"]
        notebook.record_my_cards(my_cards)
        
        for card in my_cards:
            assert notebook.entries[card].player_status["Test"] == CardStatus.HAS
            assert notebook.entries[card].envelope_status == CardStatus.NOT_HAS


class TestDeduction:
    """Test deduction logic."""
    
    def test_get_unknown_cards_returns_string(self):
        """Should return unknown cards as formatted string."""
        notebook = DetectiveNotebook("Test", ["Test", "P2"])
        notebook.mark_card("Miss Scarlet", "Test")
        notebook.mark_card("Colonel Mustard", "P2")
        
        unknown = notebook.get_unknown_cards()
        
        # Should be a string with unknown cards listed
        assert isinstance(unknown, str)
        assert "Miss Scarlet" not in unknown  # Known cards excluded
    
    def test_get_possible_solution_returns_string(self):
        """Should return possible solution as formatted string."""
        notebook = DetectiveNotebook("Test", ["Test", "P2"])
        
        # Mark some cards as definitely NOT in envelope
        notebook.mark_card("Miss Scarlet", "Test")
        
        possible = notebook.get_possible_solution()
        
        # Should be a string
        assert isinstance(possible, str)


class TestStrategicSuggestions:
    """Test strategic suggestion generation."""
    
    def test_suggests_unknown_cards(self):
        """Should suggest cards that are still unknown."""
        notebook = DetectiveNotebook("Test", ["Test", "P2"])
        notebook.mark_card("Miss Scarlet", "Test")
        
        suggestion = notebook.get_strategic_suggestion("Library")
        
        # Should return a formatted string with suggestions
        assert isinstance(suggestion, str)


class TestGlobalNotebookManagement:
    """Test global notebook functions."""
    
    def test_get_notebook_creates_new(self):
        """get_notebook should create if doesn't exist."""
        reset_all_notebooks()
        notebook = get_notebook("NewPlayer", ["NewPlayer", "P2"])
        assert notebook.owner_name == "NewPlayer"
    
    def test_get_notebook_returns_existing(self):
        """get_notebook should return same instance."""
        reset_all_notebooks()
        nb1 = get_notebook("Test", ["Test", "P2"])
        nb1.mark_card("Miss Scarlet", "Test")
        
        nb2 = get_notebook("Test", ["Test", "P2"])
        assert nb2.entries["Miss Scarlet"].player_status["Test"] == CardStatus.HAS
    
    def test_reset_notebook(self):
        """reset_notebook should clear a specific notebook."""
        reset_all_notebooks()
        nb = get_notebook("Test", ["Test", "P2"])
        nb.mark_card("Miss Scarlet", "Test")
        
        reset_notebook("Test")
        nb2 = get_notebook("Test", ["Test", "P2"])
        
        assert nb2.entries["Miss Scarlet"].player_status["Test"] == CardStatus.UNKNOWN
    
    def test_reset_all_notebooks(self):
        """reset_all_notebooks should clear all notebooks."""
        nb1 = get_notebook("P1", ["P1", "P2"])
        nb2 = get_notebook("P2", ["P1", "P2"])
        
        nb1.mark_card("Miss Scarlet", "P1")
        nb2.mark_card("Knife", "P2")
        
        reset_all_notebooks()
        
        # Getting notebooks again should give fresh ones
        new_nb1 = get_notebook("P1", ["P1", "P2"])
        assert new_nb1.entries["Miss Scarlet"].player_status["P1"] == CardStatus.UNKNOWN


class TestNotebookOutput:
    """Test notebook display functions."""
    
    def test_get_grid_as_string(self):
        """Should generate a readable grid string."""
        notebook = DetectiveNotebook("Test", ["Test", "P2"])
        notebook.mark_card("Miss Scarlet", "Test")
        
        grid_str = notebook.get_notebook_grid()
        
        assert "Miss Scarlet" in grid_str
        assert "✓" in grid_str


class TestAutoDeduction:
    """Test automatic deduction when all players marked."""
    
    def test_auto_deduce_envelope(self):
        """If all players don't have a card, it's in the envelope."""
        notebook = DetectiveNotebook("Test", ["P1", "P2"])
        
        # Mark both players as NOT having Miss Scarlet
        notebook.mark_not_has("Miss Scarlet", "P1")
        notebook.mark_not_has("Miss Scarlet", "P2")
        
        # Should auto-deduce ENVELOPE has it (after _check_deductions runs)
        assert notebook.entries["Miss Scarlet"].envelope_status == CardStatus.HAS


class TestAccusationValidation:
    """Test notebook-based accusation validation."""
    
    def test_validate_accusation_with_crossed_out_card(self):
        """Accusing a card that someone has should be invalid."""
        notebook = DetectiveNotebook("Test", ["Test", "P2"])
        
        # Mark that P2 has Miss Scarlet
        notebook.mark_card("Miss Scarlet", "P2")
        
        # Trying to accuse Miss Scarlet should be invalid
        result = notebook.validate_accusation("Miss Scarlet", "Knife", "Kitchen")
        
        assert result["valid"] == False
        assert len(result["warnings"]) > 0
        assert "Miss Scarlet" in result["warnings"][0]
    
    def test_validate_accusation_with_valid_cards(self):
        """Accusing cards not crossed out should be valid."""
        notebook = DetectiveNotebook("Test", ["Test", "P2"])
        
        # Don't mark anything - all cards are unknown/possible
        result = notebook.validate_accusation("Miss Scarlet", "Knife", "Kitchen")
        
        assert result["valid"] == True
        assert len(result["warnings"]) == 0
    
    def test_get_accusation_recommendation_not_ready(self):
        """Should not recommend accusation when too many possibilities."""
        notebook = DetectiveNotebook("Test", ["Test", "P2"])
        
        # With no deductions, shouldn't be ready
        rec = notebook.get_accusation_recommendation()
        
        assert rec["can_accuse"] == False
        assert rec["suspect"] is None
    
    def test_get_accusation_recommendation_ready(self):
        """Should recommend accusation when one option in each category."""
        notebook = DetectiveNotebook("Test", ["Test", "P2"])
        
        # Mark all suspects except Miss Scarlet as held by players
        for suspect in ["Colonel Mustard", "Mrs. White", "Mr. Green", "Mrs. Peacock", "Professor Plum"]:
            notebook.mark_card(suspect, "P2")
        
        # Mark all weapons except Knife as held by players
        for weapon in ["Candlestick", "Lead Pipe", "Revolver", "Rope", "Wrench"]:
            notebook.mark_card(weapon, "Test")
        
        # Mark all rooms except Kitchen as held by players
        for room in ["Ballroom", "Conservatory", "Billiard Room", "Library", "Study", "Hall", "Lounge", "Dining Room"]:
            notebook.mark_card(room, "P2")
        
        rec = notebook.get_accusation_recommendation()
        
        assert rec["can_accuse"] == True
        assert rec["suspect"] == "Miss Scarlet"
        assert rec["weapon"] == "Knife"
        assert rec["room"] == "Kitchen"


class TestSuggestionValidation:
    """Test notebook-based suggestion validation."""
    
    def test_validate_suggestion_with_known_card(self):
        """Suggesting a card that someone has should warn."""
        notebook = DetectiveNotebook("Test", ["Test", "P2"])
        
        # Mark that P2 has Miss Scarlet
        notebook.mark_card("Miss Scarlet", "P2")
        
        # Suggesting Miss Scarlet should be flagged as wasteful
        result = notebook.validate_suggestion("Miss Scarlet", "Knife", "Kitchen")
        
        assert result["valid"] == False
        assert len(result["warnings"]) > 0
        assert "Miss Scarlet" in result["warnings"][0]
        assert "Miss Scarlet" in result["wasted_cards"]
    
    def test_validate_suggestion_with_unknown_cards(self):
        """Suggesting unknown cards should be valid."""
        notebook = DetectiveNotebook("Test", ["Test", "P2"])
        
        # Don't mark anything - all cards are unknown
        result = notebook.validate_suggestion("Miss Scarlet", "Knife", "Kitchen")
        
        assert result["valid"] == True
        assert len(result["warnings"]) == 0
        assert len(result["wasted_cards"]) == 0
    
    def test_validate_suggestion_provides_alternatives(self):
        """Should suggest better alternatives when cards are known."""
        notebook = DetectiveNotebook("Test", ["Test", "P2"])
        
        # Mark Miss Scarlet and Knife as held
        notebook.mark_card("Miss Scarlet", "P2")
        notebook.mark_card("Knife", "Test")
        
        result = notebook.validate_suggestion("Miss Scarlet", "Knife", "Kitchen")
        
        assert result["valid"] == False
        # Should have alternatives that don't include Miss Scarlet or Knife
        assert len(result["better_suspects"]) > 0
        assert "Miss Scarlet" not in result["better_suspects"]
        assert len(result["better_weapons"]) > 0
        assert "Knife" not in result["better_weapons"]


class TestUpdateAllNotebooksCardShown:
    """Test the update_all_notebooks_card_shown function."""
    
    def test_updates_all_player_notebooks(self):
        """Should update all players' notebooks when a card is shown."""
        reset_all_notebooks()
        
        # Create notebooks for multiple players
        players = ["Miss Scarlet", "Colonel Mustard", "Mrs. White"]
        nb1 = get_notebook("Miss Scarlet", players)
        nb2 = get_notebook("Colonel Mustard", players)
        nb3 = get_notebook("Mrs. White", players)
        
        # Call update_all_notebooks_card_shown
        update_all_notebooks_card_shown("Knife", "Colonel Mustard")
        
        # All notebooks should now show Colonel Mustard has the Knife
        assert nb1.entries["Knife"].player_status["Colonel Mustard"] == CardStatus.HAS
        assert nb2.entries["Knife"].player_status["Colonel Mustard"] == CardStatus.HAS
        assert nb3.entries["Knife"].player_status["Colonel Mustard"] == CardStatus.HAS
        
        # Other players should be marked as NOT having the Knife
        assert nb1.entries["Knife"].player_status["Miss Scarlet"] == CardStatus.NOT_HAS
        assert nb1.entries["Knife"].player_status["Mrs. White"] == CardStatus.NOT_HAS
    
    def test_marks_card_not_in_envelope(self):
        """Card shown should be marked as not in envelope for all players."""
        reset_all_notebooks()
        
        players = ["Miss Scarlet", "Colonel Mustard"]
        nb1 = get_notebook("Miss Scarlet", players)
        nb2 = get_notebook("Colonel Mustard", players)
        
        update_all_notebooks_card_shown("Library", "Miss Scarlet")
        
        # Both notebooks should show Library is NOT in the envelope
        assert nb1.entries["Library"].envelope_status == CardStatus.NOT_HAS
        assert nb2.entries["Library"].envelope_status == CardStatus.NOT_HAS
    
    def test_handles_empty_notebooks(self):
        """Should handle case where no notebooks exist yet."""
        reset_all_notebooks()
        
        # This should not raise an error even with no notebooks
        update_all_notebooks_card_shown("Knife", "Colonel Mustard")
    
    def test_updates_after_suggestion_disproval_scenario(self):
        """Simulate a suggestion disproval and verify all notebooks updated."""
        reset_all_notebooks()
        
        players = ["Miss Scarlet", "Colonel Mustard", "Mrs. White", "Mr. Green"]
        
        # Create all player notebooks (as would happen in a real game)
        for player in players:
            get_notebook(player, players)
        
        # Simulate: Miss Scarlet suggests, Colonel Mustard shows Knife
        update_all_notebooks_card_shown("Knife", "Colonel Mustard")
        
        # All four players should have updated notebooks
        for player in players:
            nb = get_notebook(player, players)
            assert nb.entries["Knife"].player_status["Colonel Mustard"] == CardStatus.HAS
            assert nb.entries["Knife"].envelope_status == CardStatus.NOT_HAS
    
    def test_updates_after_magnifying_glass_clue_scenario(self):
        """Simulate a magnifying glass clue and verify all notebooks updated."""
        reset_all_notebooks()
        
        players = ["Miss Scarlet", "Colonel Mustard", "Mrs. White"]
        
        for player in players:
            get_notebook(player, players)
        
        # Simulate: Player rolls magnifying glass and gets clue about Mrs. White having Revolver
        update_all_notebooks_card_shown("Revolver", "Mrs. White")
        
        # All three players should know Mrs. White has the Revolver
        for player in players:
            nb = get_notebook(player, players)
            assert nb.entries["Revolver"].player_status["Mrs. White"] == CardStatus.HAS
            # And other players don't have it
            assert nb.entries["Revolver"].player_status["Miss Scarlet"] == CardStatus.NOT_HAS
            assert nb.entries["Revolver"].player_status["Colonel Mustard"] == CardStatus.NOT_HAS
    
    def test_multiple_cards_revealed_progressively(self):
        """Test that multiple card reveals accumulate correctly."""
        reset_all_notebooks()
        
        players = ["Miss Scarlet", "Colonel Mustard", "Mrs. White"]
        
        for player in players:
            get_notebook(player, players)
        
        # First card revealed
        update_all_notebooks_card_shown("Knife", "Colonel Mustard")
        
        # Second card revealed
        update_all_notebooks_card_shown("Library", "Mrs. White")
        
        # Third card revealed
        update_all_notebooks_card_shown("Miss Scarlet", "Miss Scarlet")
        
        # All notebooks should have all three pieces of information
        for player in players:
            nb = get_notebook(player, players)
            assert nb.entries["Knife"].player_status["Colonel Mustard"] == CardStatus.HAS
            assert nb.entries["Library"].player_status["Mrs. White"] == CardStatus.HAS
            assert nb.entries["Miss Scarlet"].player_status["Miss Scarlet"] == CardStatus.HAS
