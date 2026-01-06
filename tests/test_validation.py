"""
Tests for Validation Tools and Agent Performance Tracking
Tests the moderator validation system for monitoring agent decision-making quality.
"""

import pytest
from clue_game.game_state import (
    reset_game_state,
    Room,
    Suspect,
    Weapon,
    Card,
)
from clue_game.notebook import DetectiveNotebook, reset_all_notebooks
from clue_game.tools.validation_tools import (
    log_validation_warning,
    track_suggestion_quality,
    get_player_performance_metrics,
    get_validation_log,
    get_game_quality_report,
)


class TestValidationTracking:
    """Test validation tracking in game state."""
    
    def test_player_has_validation_fields(self):
        """Players should have validation tracking fields."""
        game = reset_game_state()
        game.setup_game(["Player1", "Player2"])
        player = game.get_player_by_name("Player1")
        
        assert hasattr(player, "invalid_move_attempts")
        assert hasattr(player, "validation_warnings")
        assert hasattr(player, "successful_suggestions")
        assert hasattr(player, "wasted_suggestions")
        assert player.invalid_move_attempts == 0
        assert len(player.validation_warnings) == 0
        assert player.successful_suggestions == 0
        assert player.wasted_suggestions == 0
    
    def test_game_state_has_validation_log(self):
        """Game state should have system-wide validation log."""
        game = reset_game_state()
        game.setup_game(["Player1", "Player2"])
        
        assert hasattr(game, "validation_log")
        assert isinstance(game.validation_log, list)
        assert len(game.validation_log) == 0


class TestLogValidationWarning:
    """Test logging validation warnings."""
    
    def test_log_warning_creates_entry(self):
        """Should create a validation warning entry."""
        game = reset_game_state()
        game.setup_game(["Player1", "Player2"])
        
        result = log_validation_warning.func(
            player_name="Player1",
            warning_type="invalid_move",
            details="Attempted to move to unreachable room",
            severity="warning"
        )
        
        assert "⚠️" in result or "Validation" in result
        assert "Player1" in result
        
        player = game.get_player_by_name("Player1")
        assert len(player.validation_warnings) == 1
        assert player.validation_warnings[0]["type"] == "invalid_move"
        assert player.validation_warnings[0]["severity"] == "warning"
    
    def test_log_error_increments_invalid_attempts(self):
        """Error severity should increment invalid move counter."""
        game = reset_game_state()
        game.setup_game(["Player1", "Player2"])
        
        log_validation_warning.func(
            player_name="Player1",
            warning_type="illogical_accusation",
            details="Accused cards already known to be held by other players",
            severity="error"
        )
        
        player = game.get_player_by_name("Player1")
        assert player.invalid_move_attempts == 1
    
    def test_log_warning_does_not_increment_invalid_attempts(self):
        """Warning severity should not increment invalid move counter."""
        game = reset_game_state()
        game.setup_game(["Player1", "Player2"])
        
        log_validation_warning.func(
            player_name="Player1",
            warning_type="wasted_suggestion",
            details="Suggested cards already known",
            severity="warning"
        )
        
        player = game.get_player_by_name("Player1")
        assert player.invalid_move_attempts == 0
    
    def test_validation_added_to_global_log(self):
        """Validation should be added to game-wide log."""
        game = reset_game_state()
        game.setup_game(["Player1", "Player2"])
        
        log_validation_warning.func(
            player_name="Player1",
            warning_type="test_warning",
            details="Test details",
            severity="info"
        )
        
        assert len(game.validation_log) == 1
        assert game.validation_log[0]["player"] == "Player1"
        assert game.validation_log[0]["type"] == "test_warning"


class TestTrackSuggestionQuality:
    """Test tracking suggestion quality."""
    
    def test_track_logical_suggestion(self):
        """Should increment successful suggestions counter."""
        game = reset_game_state()
        game.setup_game(["Player1", "Player2"])
        
        result = track_suggestion_quality.func(
            player_name="Player1",
            is_wasted=False
        )
        
        assert "LOGICAL" in result or "✓" in result
        
        player = game.get_player_by_name("Player1")
        assert player.successful_suggestions == 1
        assert player.wasted_suggestions == 0
    
    def test_track_wasted_suggestion(self):
        """Should increment wasted suggestions counter."""
        game = reset_game_state()
        game.setup_game(["Player1", "Player2"])
        
        result = track_suggestion_quality.func(
            player_name="Player1",
            is_wasted=True,
            reason="Suggested Miss Scarlet which is already known to be held by Player2"
        )
        
        assert "WASTED" in result
        assert "Miss Scarlet" in result
        
        player = game.get_player_by_name("Player1")
        assert player.successful_suggestions == 0
        assert player.wasted_suggestions == 1
    
    def test_track_multiple_suggestions(self):
        """Should track multiple suggestions and calculate quality percentage."""
        game = reset_game_state()
        game.setup_game(["Player1", "Player2"])
        
        # Track 3 logical and 1 wasted
        track_suggestion_quality.func(player_name="Player1", is_wasted=False)
        track_suggestion_quality.func(player_name="Player1", is_wasted=False)
        track_suggestion_quality.func(player_name="Player1", is_wasted=False)
        result = track_suggestion_quality.func(player_name="Player1", is_wasted=True, reason="Known card")
        
        assert "75" in result or "3/4" in result  # 75% quality
        
        player = game.get_player_by_name("Player1")
        assert player.successful_suggestions == 3
        assert player.wasted_suggestions == 1


class TestGetPlayerPerformanceMetrics:
    """Test getting player performance metrics."""
    
    def test_get_single_player_metrics(self):
        """Should return metrics for a specific player."""
        game = reset_game_state()
        game.setup_game(["Player1", "Player2"])
        
        # Add some data
        player = game.get_player_by_name("Player1")
        player.successful_suggestions = 5
        player.wasted_suggestions = 2
        player.invalid_move_attempts = 1
        
        result = get_player_performance_metrics.func(player_name="Player1")
        
        assert "Player1" in result
        assert "5" in result or "71" in result  # 5/7 = 71%
        assert "Logical suggestions" in result or "suggestions" in result.lower()
    
    def test_get_all_players_metrics(self):
        """Should return metrics for all players when no name specified."""
        game = reset_game_state()
        game.setup_game(["Player1", "Player2", "Player3"])
        
        result = get_player_performance_metrics.func()
        
        assert "Player1" in result
        assert "Player2" in result
        assert "Player3" in result
        assert "PERFORMANCE METRICS" in result or "performance" in result.lower()
    
    def test_shows_recent_warnings(self):
        """Should display recent validation warnings."""
        game = reset_game_state()
        game.setup_game(["Player1", "Player2"])
        
        log_validation_warning.func(
            player_name="Player1",
            warning_type="test_warning",
            details="Test details",
            severity="warning"
        )
        
        result = get_player_performance_metrics.func(player_name="Player1")
        
        assert "warning" in result.lower() or "test_warning" in result


class TestGetValidationLog:
    """Test getting validation log."""
    
    def test_empty_log_message(self):
        """Should return message when log is empty."""
        reset_game_state()
        
        result = get_validation_log.func()
        
        assert "No validation events" in result or "not" in result.lower()
    
    def test_shows_recent_events(self):
        """Should show recent validation events."""
        game = reset_game_state()
        game.setup_game(["Player1", "Player2"])
        
        # Log multiple events
        for i in range(5):
            log_validation_warning.func(
                player_name="Player1",
                warning_type=f"warning_{i}",
                details=f"Details {i}",
                severity="info"
            )
        
        result = get_validation_log.func(last_n=3)
        
        assert "warning_4" in result  # Most recent
        assert "warning_3" in result
        assert "warning_2" in result
        assert "warning_0" not in result  # Too old


class TestGetGameQualityReport:
    """Test game quality report generation."""
    
    def test_generates_comprehensive_report(self):
        """Should generate full quality report."""
        game = reset_game_state()
        game.setup_game(["Player1", "Player2", "Player3"])
        
        # Add varied performance data
        p1 = game.get_player_by_name("Player1")
        p1.successful_suggestions = 8
        p1.wasted_suggestions = 2
        p1.invalid_move_attempts = 0
        
        p2 = game.get_player_by_name("Player2")
        p2.successful_suggestions = 3
        p2.wasted_suggestions = 5
        p2.invalid_move_attempts = 2
        
        result = get_game_quality_report.func()
        
        assert "GAME QUALITY REPORT" in result or "QUALITY" in result
        assert "Player1" in result
        assert "Player2" in result
        assert "Player3" in result
        assert "OVERALL" in result or "Overall" in result
    
    def test_calculates_grades(self):
        """Should assign performance grades to players."""
        game = reset_game_state()
        game.setup_game(["ExcellentPlayer", "GoodPlayer", "PoorPlayer"])
        
        # Excellent: 80%+ logical, 0 invalid
        excellent = game.get_player_by_name("ExcellentPlayer")
        excellent.successful_suggestions = 9
        excellent.wasted_suggestions = 1
        excellent.invalid_move_attempts = 0
        
        # Good: 60%+ logical, ≤2 invalid
        good = game.get_player_by_name("GoodPlayer")
        good.successful_suggestions = 6
        good.wasted_suggestions = 4
        good.invalid_move_attempts = 1
        
        # Poor: <40% logical
        poor = game.get_player_by_name("PoorPlayer")
        poor.successful_suggestions = 2
        poor.wasted_suggestions = 8
        poor.invalid_move_attempts = 5
        
        result = get_game_quality_report.func()
        
        # Check for grades (A, B, C, D or Excellent, Good, etc.)
        assert "Grade" in result or "grade" in result
        # Excellent player should have grade A, Poor player grade D
        assert "ExcellentPlayer" in result and "Grade: A" in result
        assert "PoorPlayer" in result and ("Grade: D" in result or "Grade: F" in result)
    
    def test_shows_overall_statistics(self):
        """Should show aggregate statistics."""
        game = reset_game_state()
        game.setup_game(["Player1", "Player2"])
        game.turn_number = 10
        
        p1 = game.get_player_by_name("Player1")
        p1.successful_suggestions = 5
        p1.wasted_suggestions = 1
        
        p2 = game.get_player_by_name("Player2")
        p2.successful_suggestions = 4
        p2.wasted_suggestions = 2
        
        result = get_game_quality_report.func()
        
        assert "Total turns: 10" in result or "10" in result
        assert "logical" in result.lower() or "wasted" in result.lower()


class TestValidationIntegrationWithNotebook:
    """Test validation works with notebook validation."""
    
    def test_wasted_suggestion_detected(self):
        """Should detect when suggestion uses known cards."""
        game = reset_game_state()
        reset_all_notebooks()
        game.setup_game(["Player1", "Player2"])
        
        # Setup notebook with known card
        from clue_game.notebook import get_notebook
        notebook = get_notebook("Player1", ["Player1", "Player2"])
        notebook.mark_card("Miss Scarlet", "Player2")  # Player2 has Miss Scarlet
        
        validation = notebook.validate_suggestion("Miss Scarlet", "Knife", "Library")
        
        assert not validation["valid"]
        assert len(validation["wasted_cards"]) > 0
        assert "Miss Scarlet" in validation["wasted_cards"]
    
    def test_logical_suggestion_approved(self):
        """Should approve suggestions using unknown cards."""
        game = reset_game_state()
        reset_all_notebooks()
        game.setup_game(["Player1", "Player2"])
        
        from clue_game.notebook import get_notebook
        notebook = get_notebook("Player1", ["Player1", "Player2"])
        
        # Don't mark any of these cards - they're unknown
        validation = notebook.validate_suggestion("Miss Scarlet", "Knife", "Library")
        
        assert validation["valid"]
        assert len(validation["wasted_cards"]) == 0
    
    def test_illogical_accusation_blocked(self):
        """Should block accusations that contradict notebook."""
        game = reset_game_state()
        reset_all_notebooks()
        game.setup_game(["Player1", "Player2"])
        
        from clue_game.notebook import get_notebook
        notebook = get_notebook("Player1", ["Player1", "Player2"])
        notebook.mark_card("Miss Scarlet", "Player2")  # Player2 has Miss Scarlet
        
        validation = notebook.validate_accusation("Miss Scarlet", "Knife", "Library")
        
        assert not validation["valid"]
        assert len(validation["warnings"]) > 0
        assert "Miss Scarlet" in str(validation["warnings"])


class TestValidationErrorHandling:
    """Test error handling in validation tools."""
    
    def test_log_warning_unknown_player(self):
        """Should handle unknown player gracefully."""
        reset_game_state()
        
        result = log_validation_warning.func(
            player_name="NonExistent",
            warning_type="test",
            details="test",
            severity="info"
        )
        
        assert "Error" in result or "not found" in result
    
    def test_track_quality_unknown_player(self):
        """Should handle unknown player gracefully."""
        reset_game_state()
        
        result = track_suggestion_quality.func(
            player_name="NonExistent",
            is_wasted=False
        )
        
        assert "Error" in result or "not found" in result
    
    def test_metrics_unknown_player(self):
        """Should handle unknown player gracefully."""
        reset_game_state()
        
        result = get_player_performance_metrics.func(player_name="NonExistent")
        
        assert "Error" in result or "not found" in result
