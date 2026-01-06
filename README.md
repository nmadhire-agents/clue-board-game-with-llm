
# Clue Board Game with LLM Agents

[![Build Status](https://github.com/nmadhire-vibecoding/clue-board-game-with-llm/actions/workflows/python-app.yml/badge.svg)](https://github.com/nmadhire-vibecoding/clue-board-game-with-llm/actions/workflows/python-app.yml)


A multi-agent implementation of the classic Clue (Cluedo) board game using CrewAI and Google Gemini 2.5 Flash LLM. Six AI agents compete to solve the murder mystery following the **official game rules** from [Wikipedia](https://en.wikipedia.org/wiki/Cluedo#Rules).

## Agent Autonomy: Perceive, Reason, Plan, Act

Each agent in this game is fully autonomous and follows a structured decision-making loop on every turn:

1. **Perceive**: The agent observes its environment and gathers all available information (cards, location, notebook, event log, etc.).
2. **Reason**: The agent analyzes its observations, updates its detective notebook, and deduces what is known or unknown.
3. **Plan**: The agent formulates a plan to achieve its goal (solving the mystery), deciding whether to move, suggest, or accuse.
4. **Act**: The agent executes its plan by using the appropriate tools (move, make a suggestion, record results, or make an accusation).

This loop ensures that each agent acts independently, adapts to new information, and makes strategic decisions throughout the game. The autonomy structure is enforced in the code and validated by tests.


## Game Overview

In this game, 6 AI players investigate a murder at Tudor Mansion:
- **Who** committed the crime (6 suspects)
- **What** weapon was used (6 weapons)  
- **Where** the crime took place (9 rooms)



Each player uses deduction and strategy to be the first to solve the mystery, autonomously following the perceive → reason → plan → act loop!

## Official Rules Implemented

Based on the [official Cluedo rules](https://en.wikipedia.org/wiki/Cluedo#Rules):

### Game Flow

```
SETUP:
  1. Randomly select 1 suspect, 1 weapon, 1 room -> place in SOLUTION ENVELOPE
  2. Shuffle remaining 18 cards and deal to all players
  3. Each player records their cards in their Detective Notebook
  4. Miss Scarlet goes first (or highest dice roll)

TURN ORDER (clockwise from Miss Scarlet):

  +------------------+
  |   START TURN     |
  +--------+---------+
           |
           v
  +------------------+
  |   ROLL DICE      |  (If you roll a 1, it shows magnifying glass = free clue!)
  +--------+---------+
           |
           v
  +------------------+
  |   MOVE           |  Options:
  |                  |  - Move through doors to adjacent room
  +--------+---------+  - Use secret passage (corner rooms only)
           |            - Stay if moved here by another's suggestion
           v
  +------------------+
  | IN A ROOM?       |--NO--> End turn, next player
  +--------+---------+
           | YES
           v
  +------------------+
  | MAKE SUGGESTION  |  "I suggest it was [SUSPECT] with the [WEAPON]
  | (optional)       |   in the [CURRENT ROOM]"
  +--------+---------+
           |
           v
  +------------------+
  | DISPROVAL        |  Clockwise from you:
  | (automatic)      |  - Each player checks if they have any suggested card
  +--------+---------+  - First player with a match shows you ONE card (secret)
           |            - If no one can disprove -> STRONG LEAD!
           v
  +------------------+
  | MAKE ACCUSATION  |  "I accuse [SUSPECT] with the [WEAPON]
  | (optional)       |   in the [ROOM]" (can be any room!)
  +--------+---------+
           |
      +----+----+
      |         |
   CORRECT    WRONG
      |         |
      v         v
  +------+  +------------------+
  | WIN! |  | ELIMINATED       |
  +------+  | (still disprove) |
            +------------------+
           |
           v
  +------------------+
  |   END TURN       |  -> Next player clockwise
  +------------------+

WINNING CONDITIONS:
  - Make a correct accusation, OR
  - Be the last active player (all others eliminated)
```

---

## Sample Game Output

Below is a sample run of the Clue board game with LLM agents. This demonstrates the gameplay, agent reasoning, and deduction process:

<details>
<summary>Click to expand sample game output</summary>

```
(See full output in [sample_game_output.txt](sample_game_output.txt))
```
+-------------+-------------+-------------+
|   KITCHEN   |  BALLROOM   |CONSERVATORY |
|   (1 door   | (2 doors    |  (1 door    |
|    south)   |  SW + SE)   |    west)    |
+-------------+-------------+-------------+
| DINING ROOM |   [CLUE]    |BILLIARD ROOM|
|  (2 doors   |  Staircase  |  (2 doors   |
|  N + E)     | (blocked)   |   W + S)    |
+-------------+-------------+-------------+
|   LOUNGE    |    HALL     |   LIBRARY   |
|    east)    |  NW+N+NE)   |   N + W)    |
+-------------+-------------+-------------+
|             |             |    STUDY    |
```

</details>
|             |             |  (1 door    |
|             |             |   north)    |
+-------------+-------------+-------------+
```


## Sample Game Output

Below is a sample run of the Clue board game with LLM agents. This demonstrates the gameplay, agent reasoning, and deduction process:

<details>
<summary>Click to expand sample game output</summary>

```
(See full output in [sample_game_output.txt](sample_game_output.txt))
- **Dealt cards** - Remaining cards dealt to players
- **One card shown** - When disproving, show only ONE matching card

## Technical Stack

- **Framework**: [CrewAI](https://github.com/joaomdmoura/crewAI) for multi-agent orchestration
- **LLM**: Google Gemini 2.5 Flash
- **Package Manager**: [uv](https://github.com/astral-sh/uv)
- **Python**: 3.11+

## Installation
```bash
# Clone the repository
git clone https://github.com/nmadhire-vibecoding/clue-board-game-with-llm.git
cd clue-board-game-with-llm

</details>

---

### Board Layout

The mansion layout with 9 rooms and their door positions:

```
+-------------+-------------+-------------+
|   KITCHEN   |  BALLROOM   |CONSERVATORY |
|   (1 door   | (2 doors    |  (1 door    |
|    south)   |  SW + SE)   |    west)    |
+-------------+-------------+-------------+
| DINING ROOM |   [CLUE]    |BILLIARD ROOM|
|  (2 doors   |  Staircase  |  (2 doors   |
|  N + E)     | (blocked)   |   W + S)    |
+-------------+-------------+-------------+
|   LOUNGE    |    HALL     |   LIBRARY   |
|  (1 door    |  (3 doors   |  (2 doors   |
|    east)    |  NW+N+NE)   |   N + W)    |
+-------------+-------------+-------------+
|             |             |    STUDY    |
|             |             |  (1 door    |
|             |             |   north)    |
+-------------+-------------+-------------+
```

# Install dependencies with uv
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

## Running the Game

```bash
# Run a full game
uv run clue-game

# Or run directly
uv run python -m clue_game.main
```

## Project Structure

```
src/clue_game/
├── __init__.py
├── main.py              # Entry point
├── game_state.py        # Game state management (official rules)
├── crew.py              # CrewAI agent definitions
├── notebook.py          # Deterministic detective notebook
├── toon_utils.py        # TOON format utilities for token efficiency
├── config/
│   ├── agents.yaml      # Agent personalities & rules knowledge
│   └── tasks.yaml       # Task definitions
└── tools/
    ├── __init__.py
    ├── game_tools.py       # Game action tools (move, suggest, accuse)
    ├── notebook_tools.py   # Detective notebook tools
    └── validation_tools.py # Moderator validation & performance tracking
```

## Detective Notebook

LLMs are notoriously bad at maintaining long-term logic across many turns. To solve this, each agent has a **deterministic Detective Notebook** that:

- Tracks card ownership in a grid (Card x Player)
- Records all suggestions and outcomes
- Auto-deduces solution when all players don't have a card
- Provides strategic suggestions based on current knowledge
- **Validates suggestions** - Warns when suggesting known cards (wastes a turn)
- **Validates accusations** - BLOCKS accusations that contradict notebook (prevents elimination)
- **Recommends accusations** - Tells agent when all 3 categories narrowed to 1 option

This prevents the AI from "forgetting" crucial information during the game!

## Validation & Agent Oversight

To ensure agents make logical, notebook-driven decisions, a comprehensive **validation system** monitors agent performance:

### Moderator as Validator
The game moderator acts as an impartial judge and validator, tracking:
- Invalid move attempts and rule violations
- Suggestion quality (logical vs wasted on known cards)
- Agent decision-making patterns
- Real-time feedback on illogical moves

### Performance Metrics
Each agent is graded on:
- **Logical suggestions**: Using unknown cards to gather information
- **Wasted suggestions**: Suggesting cards already known (no new info)
- **Invalid attempts**: Moves blocked for contradicting notebook
- **Quality score**: Percentage of logical decisions

### Grading System
- **A (Excellent)**: ≥80% logical suggestions, 0 invalid attempts
- **B (Good)**: ≥60% logical suggestions, ≤2 invalid attempts
- **C (Fair)**: ≥40% logical suggestions
- **D (Needs Improvement)**: <40% logical suggestions

### End-Game Analysis
At game conclusion, the moderator generates a comprehensive quality report showing:
- Individual agent performance metrics
- Overall decision-making quality
- Validation warnings and patterns
- Suggestions for prompt improvements

This system ensures agents follow the perceive → reason → plan → act loop effectively!

## Token Efficiency with TOON Format

Tool outputs use **[TOON (Token-Oriented Object Notation)](https://github.com/toon-format/toon)** format by default, achieving **30-60% token reduction** compared to verbose text output. TOON combines YAML-like structure with CSV-style tabular data for maximum LLM efficiency.

### Example Output Comparison

**Before (Verbose Text):**
```
=== POSSIBLE SOLUTION ===

SUSPECT: 3 possibilities - Miss Scarlet, Colonel Mustard, Mrs. White
WEAPON: Candlestick (only possibility!)
ROOM: 2 possibilities - Kitchen, Library

🎯 Not ready to accuse yet
```

**After (TOON Format):**
```
can_accuse: false
confirmed:
  w: Candlestick
possible:
  s[3]: Miss Scarlet,Colonel Mustard,Mrs. White
  r[2]: Kitchen,Library
```

### Configuration

TOON format is enabled by default. To disable it (for debugging):
```bash
export CLUE_TOON_ENABLED=false
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Your Google AI API key for Gemini 2.5 Flash |
| `CLUE_TOON_ENABLED` | Enable TOON format for token efficiency (default: `true`) |
| `CLUE_DEBUG` | Enable debug logging (default: `false`) |

## License

MIT License - See [LICENSE](LICENSE) file
