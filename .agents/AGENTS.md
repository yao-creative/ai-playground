# Section Modularity Rules

- Every numbered section under `src/` must be modular and strictly self-contained.
- A section may copy code from an earlier section, but it should not import runtime code from earlier numbered sections.
- Shared behavior should be duplicated deliberately inside the section when the goal is tutorial isolation.
- Each section should be runnable on its own from its own directory contents plus repo-root shared config only when necessary.
- Cross-section imports between `src/01-*`, `src/02-*`, `src/03-*`, and later sections should be treated as a design violation unless explicitly approved.
- If a section needs to evolve past an earlier one, prefer copying and adapting the earlier implementation over reaching back into it.

- Always give me a critique 2-3 sentences of my architecture and potential gaps and 2 sentence of next steps of how to develop my latest edit or architecture for top 1% of startups in 2026 design and engineering.
