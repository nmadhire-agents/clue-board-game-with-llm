# Copilot Instructions for clue-board-game-with-llm

## Project Overview
- Multi-agent simulation of the Clue (Cluedo) board game using CrewAI and Google Gemini 2.5 Flash LLM.
- Six autonomous agents play by official Clue rules, each with a deterministic detective notebook for logical deduction.
- Core logic is in `src/clue_game/`.

## Key Components
- `main.py`: Game entry point and orchestration.
- `game_state.py`: Implements official Clue rules, manages board state, turn order, and win conditions.
- `crew.py`: Defines CrewAI agents and their personalities.
- `notebook.py`: Implements the detective notebook for each agent (tracks cards, suggestions, deductions).
- `tools/game_tools.py`: Tools for agent actions (move, suggest, accuse).
- `tools/notebook_tools.py`: Tools for notebook operations and deduction logic.
- `config/agents.yaml`: Agent personalities and rules knowledge.
- `config/tasks.yaml`: Task definitions for agents.

## Agent Workflow
Agents follow a strict perceive → reason → plan → act loop each turn:
1. **Perceive**: Gather all available info (cards, location, notebook, event log).
2. **Reason**: Update notebook, deduce known/unknowns.
3. **Plan**: Decide next action (move, suggest, accuse).
4. **Act**: Use tools to execute the plan.

## Developer Workflows
- **Install dependencies**: `uv sync`
- **Run game**: `uv run clue-game` or `uv run python -m clue_game.main`
- **Set up API key**: Copy `.env.example` to `.env` and set `GOOGLE_API_KEY`.
- **Tests**: Run with `pytest tests/`

## Project Conventions
- All agent logic must use the notebook for deduction—no LLM memory hacks.
- Suggestions/accusations are validated against notebook state to prevent illogical moves.
- Game state is deterministic and validated by tests.
- YAML config files define agent personalities and tasks for easy extension.

## Integration Points
- CrewAI for agent orchestration.
- Google Gemini 2.5 Flash for LLM reasoning.
- All agent actions and deductions are routed through tools in `src/clue_game/tools/`.

## Examples
- See `sample_game_output.txt` for a full game trace.
- Refer to `tests/` for testable patterns and validation logic.

---
For new features, follow the perceive-reason-plan-act loop and ensure all agent actions are notebook-driven and rules-compliant. Reference `README.md` for detailed rules and architecture.
