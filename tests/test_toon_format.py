"""
Tests for TOON format utilities and integration.

These tests verify that TOON format is properly applied to tool outputs
and that the format produces valid, token-efficient results.
"""

import os
import pytest
from unittest.mock import patch

from clue_game.game_state import reset_game_state, Room
from clue_game.notebook import reset_all_notebooks, get_notebook, DetectiveNotebook
from clue_game.toon_utils import (
    to_toon, TOON_AVAILABLE, TOON_ENABLED,
    format_notebook_status, format_suggestion_result,
    format_strategic_suggestion, format_accusation_recommendation,
    format_game_status, format_available_moves
)


class TestToonUtilsBasic:
    """Test basic TOON utility functions."""
    
    def test_toon_availability_check(self):
        """TOON_AVAILABLE flag should be boolean."""
        assert isinstance(TOON_AVAILABLE, bool)
        # If TOON library is not installed, we gracefully degrade
        # This test passes regardless of installation status
    
    def test_toon_enabled_by_default(self):
        """TOON should be enabled by default."""
        # Check environment doesn't explicitly disable it
        env_val = os.environ.get("CLUE_TOON_ENABLED", "true").lower()
        expected = env_val in ("1", "true", "yes")
        assert TOON_ENABLED == expected
    
    def test_to_toon_simple_dict(self):
        """to_toon should encode simple dicts or fallback gracefully."""
        data = {"name": "Alice", "age": 30}
        result = to_toon(data)
        assert isinstance(result, str)
        # Content should be represented (either TOON format or str fallback)
        assert "Alice" in result
        assert "30" in result
    
    def test_to_toon_nested_dict(self):
        """to_toon should encode nested dicts or fallback gracefully."""
        data = {"player": {"name": "Bob", "cards": ["Card1", "Card2"]}}
        result = to_toon(data)
        assert isinstance(result, str)
        assert "Bob" in result
    
    def test_to_toon_list(self):
        """to_toon should encode lists or fallback gracefully."""
        data = {"items": ["apple", "banana", "cherry"]}
        result = to_toon(data)
        assert isinstance(result, str)
        assert "apple" in result
    
    def test_to_toon_with_fallback_when_disabled(self):
        """to_toon should return fallback when TOON unavailable/disabled."""
        from clue_game import toon_utils
        
        # Save original values
        orig_available = toon_utils.TOON_AVAILABLE
        orig_enabled = toon_utils.TOON_ENABLED
        
        try:
            # Simulate TOON unavailable
            toon_utils.TOON_AVAILABLE = False
            result = toon_utils.to_toon({"key": "value"}, fallback_str="fallback")
            assert result == "fallback"
        finally:
            # Restore
            toon_utils.TOON_AVAILABLE = orig_available
            toon_utils.TOON_ENABLED = orig_enabled


class TestToonFormatHelpers:
    """Test TOON format helper functions."""
    
    def test_format_notebook_status(self):
        """format_notebook_status should return TOON string."""
        result = format_notebook_status(
            owner="TestPlayer",
            possible_solution={"s": ["Scarlet"], "w": ["Knife"], "r": ["Kitchen"]},
            unknown_counts={"s": 1, "w": 1, "r": 1},
            can_accuse=False
        )
        assert isinstance(result, str)
        assert "TestPlayer" in result
        assert "INVESTIGATING" in result
    
    def test_format_notebook_status_can_accuse(self):
        """format_notebook_status should show READY_TO_ACCUSE."""
        result = format_notebook_status(
            owner="TestPlayer",
            possible_solution={"s": ["Scarlet"], "w": ["Knife"], "r": ["Kitchen"]},
            unknown_counts={"s": 0, "w": 0, "r": 0},
            can_accuse=True
        )
        assert "READY_TO_ACCUSE" in result
    
    def test_format_suggestion_result(self):
        """format_suggestion_result should encode suggestion."""
        result = format_suggestion_result(
            suggester="Scarlet",
            suspect="Green",
            weapon="Knife",
            room="Kitchen",
            disprover="Mustard",
            card_shown="Knife"
        )
        assert isinstance(result, str)
        assert "Scarlet" in result
        assert "Green" in result or "s" in result  # abbreviation
    
    def test_format_strategic_suggestion(self):
        """format_strategic_suggestion should encode recommendation."""
        result = format_strategic_suggestion(
            room="Library",
            recommend_suspect="Miss Scarlet",
            recommend_weapon="Candlestick",
            unknown_suspects=["Miss Scarlet", "Colonel Mustard"],
            unknown_weapons=["Candlestick", "Knife"]
        )
        assert isinstance(result, str)
        assert "Library" in result
    
    def test_format_accusation_recommendation_can_accuse(self):
        """format_accusation_recommendation should show accusation details."""
        result = format_accusation_recommendation(
            can_accuse=True,
            suspect="Miss Scarlet",
            weapon="Candlestick",
            room="Kitchen"
        )
        assert "can_accuse" in result or "true" in result.lower()
        assert "Miss Scarlet" in result or "Scarlet" in result
    
    def test_format_accusation_recommendation_cannot_accuse(self):
        """format_accusation_recommendation should show reason."""
        result = format_accusation_recommendation(
            can_accuse=False,
            reason="Multiple suspects possible",
            possible_suspects=["Scarlet", "Mustard"]
        )
        assert "false" in result.lower() or "can_accuse" in result
    
    def test_format_game_status(self):
        """format_game_status should encode game state."""
        result = format_game_status(
            turn=5,
            current_player="Mustard",
            players_status=[{"name": "Scarlet", "active": True}],
            winner=None,
            game_over=False
        )
        assert isinstance(result, str)
        assert "5" in result
        assert "Mustard" in result
    
    def test_format_available_moves(self):
        """format_available_moves should encode movement options."""
        result = format_available_moves(
            current_location="Library",
            dice_roll=5,
            reachable_rooms=["Study", "Hall"],
            secret_passage="Kitchen",
            recommended=["Study"],
            avoid=["Hall"]
        )
        assert isinstance(result, str)
        assert "Library" in result


class TestNotebookToonOutput:
    """Test that notebook methods produce TOON output."""
    
    def setup_method(self):
        """Reset state before each test."""
        reset_game_state()
        reset_all_notebooks()
    
    def test_get_unknown_cards_toon(self):
        """get_unknown_cards should return TOON format when enabled."""
        notebook = DetectiveNotebook("TestPlayer", ["TestPlayer", "Other"])
        result = notebook.get_unknown_cards()
        
        if TOON_ENABLED:
            # TOON format uses structured output
            assert "unknown" in result or "counts" in result
        else:
            # Text format
            assert "UNKNOWN" in result or "Suspects" in result
    
    def test_get_possible_solution_toon(self):
        """get_possible_solution should return TOON format when enabled."""
        notebook = DetectiveNotebook("TestPlayer", ["TestPlayer", "Other"])
        result = notebook.get_possible_solution()
        
        if TOON_ENABLED:
            assert "can_accuse" in result or "possible" in result
        else:
            assert "POSSIBLE" in result or "SOLUTION" in result
    
    def test_get_notebook_grid_toon(self):
        """get_notebook_grid should return TOON format when enabled."""
        notebook = DetectiveNotebook("TestPlayer", ["TestPlayer", "Other"])
        result = notebook.get_notebook_grid()
        
        if TOON_ENABLED:
            assert "grid" in result
        else:
            assert "NOTEBOOK" in result or "Card" in result
    
    def test_get_suggestion_history_toon(self):
        """get_suggestion_history should return TOON format when enabled."""
        notebook = DetectiveNotebook("TestPlayer", ["TestPlayer", "Other"])
        # Record a suggestion first
        notebook.record_suggestion(
            turn_number=1,
            suggester="TestPlayer",
            suspect="Miss Scarlet",
            weapon="Knife",
            room="Kitchen",
            disprover="Other"
        )
        result = notebook.get_suggestion_history()
        
        if TOON_ENABLED:
            assert "history" in result
        else:
            assert "SUGGESTION" in result or "TestPlayer" in result
    
    def test_get_strategic_suggestion_toon(self):
        """get_strategic_suggestion should return TOON format when enabled."""
        notebook = DetectiveNotebook("TestPlayer", ["TestPlayer", "Other"])
        result = notebook.get_strategic_suggestion("Library")
        
        if TOON_ENABLED:
            assert "room" in result or "Library" in result
        else:
            assert "STRATEGIC" in result or "Library" in result


class TestToolsToonOutput:
    """Test that game tools produce TOON output."""
    
    def setup_method(self):
        """Reset state before each test."""
        reset_game_state()
        reset_all_notebooks()
    
    def test_get_my_cards_toon(self):
        """get_my_cards should return TOON format when enabled."""
        from clue_game.tools.game_tools import get_my_cards
        
        game = reset_game_state()
        game.setup_game(["TestPlayer", "Other"])
        
        result = get_my_cards.func(player_name="TestPlayer")
        
        if TOON_ENABLED:
            assert "cards" in result.lower() or "'cards'" in result
        else:
            assert "Cards" in result
    
    def test_get_current_location_toon(self):
        """get_current_location should return TOON format when enabled."""
        from clue_game.tools.game_tools import get_current_location
        
        game = reset_game_state()
        game.setup_game(["TestPlayer", "Other"])
        player = game.get_player_by_name("TestPlayer")
        player.current_room = Room.LIBRARY
        player.in_hallway = False
        
        result = get_current_location.func(player_name="TestPlayer")
        
        if TOON_ENABLED:
            assert "location" in result or "Library" in result
        else:
            assert "Library" in result
    
    def test_initialize_notebook_toon(self):
        """initialize_notebook should return TOON format when enabled."""
        from clue_game.tools.notebook_tools import initialize_notebook
        
        game = reset_game_state()
        game.setup_game(["TestPlayer", "Other"])
        
        result = initialize_notebook.func(player_name="TestPlayer")
        
        if TOON_ENABLED:
            assert "status" in result or "initialized" in result
        else:
            assert "Notebook" in result or "initialized" in result.lower()
    
    def test_get_accusation_recommendation_toon(self):
        """get_accusation_recommendation should return TOON format when enabled."""
        from clue_game.tools.notebook_tools import get_accusation_recommendation, initialize_notebook
        
        game = reset_game_state()
        game.setup_game(["TestPlayer", "Other"])
        
        # Initialize notebook first
        initialize_notebook.func(player_name="TestPlayer")
        
        result = get_accusation_recommendation.func(player_name="TestPlayer")
        
        # Should indicate cannot accuse (not enough info)
        assert "can_accuse" in result.lower() or "not ready" in result.lower() or "false" in result.lower()


class TestToonTokenEfficiency:
    """Test that TOON format is more token-efficient."""
    
    def test_toon_shorter_than_verbose(self):
        """TOON output should generally be shorter than verbose text."""
        # Create a complex data structure
        data = {
            "player": "TestPlayer",
            "cards": ["Card1", "Card2", "Card3"],
            "location": "Library",
            "can_suggest": True,
            "unknown_suspects": ["Scarlet", "Mustard", "Green"],
            "unknown_weapons": ["Knife", "Rope", "Wrench"]
        }
        
        toon_output = to_toon(data)
        
        # Create equivalent verbose text
        verbose = f"=== PLAYER STATUS ===\n\n"
        verbose += f"Player: {data['player']}\n"
        verbose += f"Your cards ({len(data['cards'])} total):\n"
        for card in data['cards']:
            verbose += f"  - {card}\n"
        verbose += f"\nCurrent location: {data['location']}\n"
        verbose += f"Can suggest: {'Yes' if data['can_suggest'] else 'No'}\n"
        verbose += f"\nUnknown suspects:\n"
        for s in data['unknown_suspects']:
            verbose += f"  - {s}\n"
        verbose += f"\nUnknown weapons:\n"
        for w in data['unknown_weapons']:
            verbose += f"  - {w}\n"
        
        # TOON should be shorter (fewer characters typically means fewer tokens)
        assert len(toon_output) < len(verbose), f"TOON ({len(toon_output)}) should be shorter than verbose ({len(verbose)})"


class TestToonDisabled:
    """Test behavior when TOON is disabled."""
    
    def test_fallback_when_toon_disabled(self):
        """When TOON_ENABLED is False, should use fallback formatting."""
        # This tests the code path, actual disabling requires env var
        from clue_game import toon_utils
        
        # Save original value
        original = toon_utils.TOON_ENABLED
        
        try:
            # Temporarily disable
            toon_utils.TOON_ENABLED = False
            
            # to_toon should return fallback or str representation
            result = toon_utils.to_toon({"test": "data"}, fallback_str="fallback")
            assert result == "fallback"
            
        finally:
            # Restore
            toon_utils.TOON_ENABLED = original
