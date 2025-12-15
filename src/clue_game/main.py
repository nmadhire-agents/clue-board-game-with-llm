#!/usr/bin/env python
"""
Clue Board Game with LLM Agents
Main entry point for running the multi-agent Clue game.
"""

import os
import sys
from dotenv import load_dotenv

from clue_game.game_state import get_game_state, reset_game_state
from clue_game.notebook import reset_all_notebooks
from clue_game.crew import (
    ClueGameCrew,
    create_player_turn_crew,
    create_moderator_announcement_crew,
)


# Load environment variables
load_dotenv()


# Player names that map to agent methods
PLAYER_CONFIGS = [
    {"name": "Scarlet", "agent_method": "player_scarlet"},
    {"name": "Mustard", "agent_method": "player_mustard"},
    {"name": "Green", "agent_method": "player_green"},
    {"name": "Peacock", "agent_method": "player_peacock"},
    {"name": "Plum", "agent_method": "player_plum"},
    {"name": "White", "agent_method": "player_white"},
]


def run_game(max_turns: int = 20):
    """
    Run a complete game of Clue with AI agents.
    
    Args:
        max_turns: Maximum number of turns before game ends in a draw
    """
    print("\n" + "=" * 60)
    print("🔍 CLUE: THE MYSTERY GAME WITH AI AGENTS 🔍")
    print("=" * 60 + "\n")
    
    # Initialize game state and reset all notebooks
    game_state = reset_game_state()
    reset_all_notebooks()  # Reset deterministic notebooks for new game
    
    player_names = [p["name"] for p in PLAYER_CONFIGS]
    game_state.setup_game(player_names)
    
    # Track which players have had their first turn (for notebook init)
    players_first_turn = {name: True for name in player_names}
    
    # Create the crew instance
    clue_crew = ClueGameCrew()
    
    # Get agent instances
    moderator = clue_crew.game_moderator()
    player_agents = {
        "Scarlet": clue_crew.player_scarlet(),
        "Mustard": clue_crew.player_mustard(),
        "Green": clue_crew.player_green(),
        "Peacock": clue_crew.player_peacock(),
        "Plum": clue_crew.player_plum(),
        "White": clue_crew.player_white(),
    }
    
    # Announce game start
    print("\n📣 MODERATOR ANNOUNCEMENT:")
    print("-" * 40)
    
    start_crew = create_moderator_announcement_crew(
        moderator,
        "start",
        players=[f"{p.name} ({p.character.value})" for p in game_state.players]
    )
    start_crew.kickoff()
    
    print("\n" + "=" * 60)
    print("🎮 GAME BEGINS!")
    print("=" * 60)
    
    # Print initial game state for debugging
    print("\n📋 Initial Setup:")
    print(f"Solution (hidden): {game_state.solution['suspect'].name}, "
          f"{game_state.solution['weapon'].name}, "
          f"{game_state.solution['room'].name}")
    print()
    
    for player in game_state.players:
        print(f"{player.name} ({player.character.value}):")
        print(f"  Location: {player.current_room.value}")
        print(f"  Cards: {[c.name for c in player.cards]}")
    print()
    
    # Main game loop
    turn_count = 0
    while not game_state.game_over and turn_count < max_turns:
        current_player = game_state.get_current_player()
        
        if not current_player.is_active:
            game_state.next_turn()
            continue
        
        turn_count += 1
        
        print("\n" + "=" * 60)
        print(f"🎲 TURN {turn_count}: {current_player.name}'s Turn")
        print("=" * 60)
        
        # Get the corresponding agent
        player_agent = player_agents[current_player.name]
        
        # Check if this is the player's first turn (needs notebook initialization)
        is_first_turn = players_first_turn.get(current_player.name, False)
        
        # Create and run the player's turn crew
        turn_crew = create_player_turn_crew(
            current_player.name,
            player_agent,
            moderator,
            is_first_turn=is_first_turn
        )
        
        # Mark that this player has had their first turn
        players_first_turn[current_player.name] = False
        
        try:
            result = turn_crew.kickoff()
            print(f"\n📝 Turn Result:\n{result}")
        except Exception as e:
            print(f"\n❌ Error during {current_player.name}'s turn: {e}")
        
        # Check if game ended during this turn
        if game_state.game_over:
            break
        
        # Move to next player
        game_state.next_turn()
    
    # Announce game end
    print("\n" + "=" * 60)
    print("🏁 GAME OVER!")
    print("=" * 60)
    
    end_crew = create_moderator_announcement_crew(
        moderator,
        "end",
        winner=game_state.winner or "No one (draw)",
        suspect=game_state.solution["suspect"].name,
        weapon=game_state.solution["weapon"].name,
        room=game_state.solution["room"].name,
        total_turns=turn_count,
    )
    end_crew.kickoff()
    
    # Print final results
    print("\n📊 FINAL RESULTS:")
    print("-" * 40)
    print(f"Winner: {game_state.winner or 'No winner (max turns reached)'}")
    print(f"Total Turns: {turn_count}")
    print(f"Solution: {game_state.solution['suspect'].name} with the "
          f"{game_state.solution['weapon'].name} in the "
          f"{game_state.solution['room'].name}")
    
    return game_state


def run_single_turn_demo():
    """
    Run a single turn demo to test the system.
    """
    print("\n" + "=" * 60)
    print("🧪 SINGLE TURN DEMO")
    print("=" * 60 + "\n")
    
    # Initialize game
    game_state = reset_game_state()
    player_names = ["Scarlet", "Mustard", "Green", "Peacock"]
    game_state.setup_game(player_names)
    
    # Create crew and get first player's agent
    clue_crew = ClueGameCrew()
    first_player = game_state.get_current_player()
    player_agent = clue_crew.player_scarlet()
    
    print(f"Testing turn for: {first_player.name}")
    print(f"Cards: {[c.name for c in first_player.cards]}")
    print(f"Location: {first_player.current_room.value}")
    print()
    
    # Run single turn
    turn_crew = create_player_turn_crew(
        first_player.name,
        player_agent,
        clue_crew.game_moderator()
    )
    
    result = turn_crew.kickoff()
    print(f"\n📝 Result:\n{result}")


def main():
    """Main entry point."""
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Error: GOOGLE_API_KEY environment variable not set.")
        print("Please create a .env file with your Google API key:")
        print("  GOOGLE_API_KEY=your-key-here")
        print("Get your API key at: https://aistudio.google.com/apikey")
        sys.exit(1)
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "demo":
            run_single_turn_demo()
        elif sys.argv[1] == "game":
            max_turns = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            run_game(max_turns)
        else:
            print("Usage: python -m clue_game.main [demo|game [max_turns]]")
    else:
        # Default: run full game
        run_game()


if __name__ == "__main__":
    main()
