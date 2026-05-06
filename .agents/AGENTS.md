# Section Modularity Rules

- Every numbered section under `src/` must be modular and strictly self-contained.
- A section may copy code from an earlier section, but it should not import runtime code from earlier numbered sections.
- Shared behavior should be duplicated deliberately inside the section when the goal is tutorial isolation.
- The only allowed shared runtime dependency across numbered sections is [config.py](/Users/yao/projects/agents-playground/src/config.py).
- Each section should be runnable from its own directory-local implementation plus the shared `src/config.py` when needed for environment loading.
- Cross-section imports between `src/01-*`, `src/02-*`, `src/03-*`, and later sections should be treated as a design violation unless explicitly approved.
- If a section needs to evolve past an earlier one, prefer copying and adapting the earlier implementation over reaching back into it.
- Tests for a section should follow the same rule: they may import that section and shared `src/config.py`, but should not depend on runtime modules from other numbered sections.

- Always give me a 3 line critique of my current code and design decisions as if I were to be a top engineer and a 3 line summary of what I should do next based on what frontier companies do in 2026. I'd like guidance which are specific design decisions, not line-by-line nitpicks.