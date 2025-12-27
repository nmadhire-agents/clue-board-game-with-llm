"""
Validation and Moderator Tools for Clue Game
Tools for tracking agent performance, logging validation failures, and moderator oversight.
"""

from crewai.tools import tool
from clue_game.game_state import get_game_state


@tool("Log Validation Warning")
def log_validation_warning(player_name: str, warning_type: str, details: str, severity: str = "warning") -> str:
    """
    Log a validation warning when a player attempts an invalid or illogical move.
    Used by the moderator to track agent performance and provide feedback.
    
    Args:
        player_name: The player who triggered the warning
        warning_type: Type of validation issue (e.g., "invalid_move", "wasted_suggestion", "illogical_accusation")
        details: Description of what went wrong
        severity: Severity level - "info", "warning", "error"
    
    Returns:
        Confirmation that the warning was logged
    """
    game_state = get_game_state()
    player = game_state.get_player_by_name(player_name)
    
    if not player:
        return f"Error: Player {player_name} not found"
    
    warning_entry = {
        "turn": game_state.turn_number,
        "player": player_name,
        "type": warning_type,
        "details": details,
        "severity": severity
    }
    
    # Add to player's validation log
    player.validation_warnings.append(warning_entry)
    
    # Increment invalid move counter if it's an error
    if severity == "error":
        player.invalid_move_attempts += 1
    
    # Add to global validation log
    game_state.validation_log.append(warning_entry)
    
    result = f"⚠️ Validation {severity.upper()} logged for {player_name}:\n"
    result += f"   Type: {warning_type}\n"
    result += f"   Details: {details}\n"
    result += f"   Turn: {game_state.turn_number}"
    
    return result


@tool("Track Suggestion Quality")
def track_suggestion_quality(player_name: str, is_wasted: bool, reason: str = "") -> str:
    """
    Track whether a suggestion was logical (using unknown cards) or wasted (using known cards).
    This helps measure agent decision-making quality.
    
    Args:
        player_name: The player who made the suggestion
        is_wasted: True if suggestion included known cards (wasteful), False if logical
        reason: Explanation of why it was wasted (if applicable)
    
    Returns:
        Confirmation and updated quality metrics
    """
    game_state = get_game_state()
    player = game_state.get_player_by_name(player_name)
    
    if not player:
        return f"Error: Player {player_name} not found"
    
    if is_wasted:
        player.wasted_suggestions += 1
        result = f"📊 Suggestion quality tracked for {player_name}: WASTED\n"
        result += f"   Reason: {reason}\n"
    else:
        player.successful_suggestions += 1
        result = f"📊 Suggestion quality tracked for {player_name}: LOGICAL ✓\n"
    
    # Calculate quality percentage
    total = player.successful_suggestions + player.wasted_suggestions
    if total > 0:
        quality_pct = (player.successful_suggestions / total) * 100
        result += f"   Quality score: {player.successful_suggestions}/{total} ({quality_pct:.1f}% logical)"
    
    return result


@tool("Get Player Performance Metrics")
def get_player_performance_metrics(player_name: str = None) -> str:
    """
    Get performance metrics for a player or all players.
    Shows suggestion quality, invalid moves, and validation warnings.
    
    Args:
        player_name: Optional - specific player name, or None for all players
    
    Returns:
        Performance metrics report
    """
    game_state = get_game_state()
    
    if player_name:
        player = game_state.get_player_by_name(player_name)
        if not player:
            return f"Error: Player {player_name} not found"
        players_to_report = [player]
    else:
        players_to_report = game_state.players
    
    result = "📊 AGENT PERFORMANCE METRICS\n"
    result += "=" * 50 + "\n\n"
    
    for player in players_to_report:
        total_suggestions = player.successful_suggestions + player.wasted_suggestions
        quality_pct = (player.successful_suggestions / total_suggestions * 100) if total_suggestions > 0 else 0
        
        result += f"{player.name} ({player.character.value}):\n"
        result += f"  Logical suggestions: {player.successful_suggestions}/{total_suggestions} ({quality_pct:.1f}%)\n"
        result += f"  Invalid move attempts: {player.invalid_move_attempts}\n"
        result += f"  Validation warnings: {len(player.validation_warnings)}\n"
        
        # Show recent warnings
        if player.validation_warnings:
            result += f"  Recent warnings:\n"
            for warning in player.validation_warnings[-3:]:  # Last 3 warnings
                result += f"    - Turn {warning['turn']}: {warning['type']} ({warning['severity']})\n"
        
        result += "\n"
    
    return result


@tool("Get Validation Log")
def get_validation_log(last_n: int = 10) -> str:
    """
    Get recent validation events from the system-wide log.
    Useful for the moderator to review agent behavior.
    
    Args:
        last_n: Number of recent events to retrieve (default 10)
    
    Returns:
        Recent validation log entries
    """
    game_state = get_game_state()
    
    if not game_state.validation_log:
        return "No validation events recorded yet."
    
    result = f"📋 VALIDATION LOG (Last {last_n} events)\n"
    result += "=" * 50 + "\n\n"
    
    recent_events = game_state.validation_log[-last_n:]
    
    for event in recent_events:
        icon = "⚠️" if event['severity'] == "warning" else "❌" if event['severity'] == "error" else "ℹ️"
        result += f"{icon} Turn {event['turn']} - {event['player']}:\n"
        result += f"   {event['type']}: {event['details']}\n\n"
    
    return result


@tool("Get Game Quality Report")
def get_game_quality_report() -> str:
    """
    Generate an overall quality report for the game.
    Shows aggregate metrics for all agents' decision-making quality.
    Used by moderator at game end for analysis.
    
    Returns:
        Comprehensive quality report for all players
    """
    game_state = get_game_state()
    
    result = "📊 GAME QUALITY REPORT\n"
    result += "=" * 60 + "\n\n"
    
    result += f"Total turns: {game_state.turn_number}\n"
    result += f"Total validation events: {len(game_state.validation_log)}\n\n"
    
    result += "PLAYER PERFORMANCE SUMMARY:\n"
    result += "-" * 60 + "\n\n"
    
    total_logical = 0
    total_wasted = 0
    total_invalid = 0
    
    for player in game_state.players:
        total_suggestions = player.successful_suggestions + player.wasted_suggestions
        quality_pct = (player.successful_suggestions / total_suggestions * 100) if total_suggestions > 0 else 0
        
        total_logical += player.successful_suggestions
        total_wasted += player.wasted_suggestions
        total_invalid += player.invalid_move_attempts
        
        result += f"{player.name}:\n"
        result += f"  • Logical suggestions: {player.successful_suggestions}\n"
        result += f"  • Wasted suggestions: {player.wasted_suggestions}\n"
        result += f"  • Suggestion quality: {quality_pct:.1f}%\n"
        result += f"  • Invalid attempts: {player.invalid_move_attempts}\n"
        result += f"  • Total warnings: {len(player.validation_warnings)}\n"
        
        # Grade the player
        if quality_pct >= 80 and player.invalid_move_attempts == 0:
            grade = "A (Excellent)"
        elif quality_pct >= 60 and player.invalid_move_attempts <= 2:
            grade = "B (Good)"
        elif quality_pct >= 40:
            grade = "C (Fair)"
        else:
            grade = "D (Needs Improvement)"
        
        result += f"  • Grade: {grade}\n\n"
    
    # Overall stats
    total_all_suggestions = total_logical + total_wasted
    overall_quality = (total_logical / total_all_suggestions * 100) if total_all_suggestions > 0 else 0
    
    result += "OVERALL STATISTICS:\n"
    result += "-" * 60 + "\n"
    result += f"Total logical suggestions: {total_logical}\n"
    result += f"Total wasted suggestions: {total_wasted}\n"
    result += f"Overall suggestion quality: {overall_quality:.1f}%\n"
    result += f"Total invalid move attempts: {total_invalid}\n"
    
    return result
