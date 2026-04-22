# Section Modularity Rules

- Every numbered section under `src/` must be modular and strictly self-contained.
- A section may copy code from an earlier section, but it should not import runtime code from earlier numbered sections.
- Shared behavior should be duplicated deliberately inside the section when the goal is tutorial isolation.
- The only allowed shared runtime dependency across numbered sections is [config.py](/Users/yao/projects/agents-playground/src/config.py).
- Each section should be runnable from its own directory-local implementation plus the shared `src/config.py` when needed for environment loading.
- Cross-section imports between `src/01-*`, `src/02-*`, `src/03-*`, and later sections should be treated as a design violation unless explicitly approved.
- If a section needs to evolve past an earlier one, prefer copying and adapting the earlier implementation over reaching back into it.
- Tests for a section should follow the same rule: they may import that section and shared `src/config.py`, but should not depend on runtime modules from other numbered sections.
