# Morning reflection routine

Cloud routine prompt (paste as the routine's message). Sources: this repo and the private data repo, cloned side by side. Secrets `REFLECTION_BOT_TOKEN` and `REFLECTION_CHAT_ID` set on the environment, never in a repo.

---

Two repositories are checked out side by side: `reflection-routine` (code and skills) and `reflections` (private data). Read `reflection-routine/.claude/skills/reflection-run/SKILL.md` and follow it exactly with the argument `morning`. The repo root is the `reflection-routine` checkout; the data folder is the `reflections` checkout (export `REFLECTIONS_DIR` to its absolute path). Work autonomously, ask nothing, and finish with the two-line report the skill specifies.
