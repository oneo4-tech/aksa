# Decisions

Active agreed decisions, one row each, newest at the bottom. Superseded rows are in `decisions-history.md` (D-016).

- Change process: never silently override a decision. A reversal is a new row here; the old row's Status becomes `superseded by D-n` and the row moves to `decisions-history.md`. Use the `add-memory` skill.
- Kind: `decision`, `rejection` (a rejected enhancement with a durable reason), `not-feasible`.
- Areas: `components`, `config`, `git`, `kb`, `memory`, `naming`, `paths`, `permissions`, `rules`, `skills`, `sync`. Add an area only with the owner's agreement.
- Why is one sentence; the full reasoning stays in the Source issue or run comment.
- Rows are never edited except Status. Ids are never reused and are unique across both files.

| ID | Date | Kind | Area | Decision | Why | Source | Status |
|---|---|---|---|---|---|---|---|
| D-001 | 2026-10-19 | decision | naming | The project is named `aksa` everywhere (repository, package, sync manifest `.aksa-sync.json`). | One name avoids the kalp/aksa/ark drift found in the first review. | aksa-setup session | active |
| D-003 | 2026-10-19 | decision | sync | `sync_vendors.py` syncs components only to repo-level vendor folders (such as `.claude/skills`), never to global home folders. | Keeps each repository and worktree self-contained. | aksa-setup session | active |
| D-004 | 2026-10-19 | decision | sync, skills | Skill sources stay vendor-neutral; OpenCode gets synced copies with its required frontmatter added by the script. | Vendor-specific fields belong to the sync step, not to every skill. | aksa-setup session | active |
| D-005 | 2026-10-19 | decision | skills | Skill names use lowercase hyphenated verb-object form, such as `record-decision`. | Names read as the action the skill performs. | aksa-setup session | active |
| D-006 | 2026-10-19 | decision | sync | The vendor sync script is `sync_vendors.py`, organized by component kind; skills are the first kind. | Hooks, agents and instructions will sync through the same script later. | aksa-setup session | active |
| D-007 | 2026-10-19 | decision | components | `AGENTS.md` is the root Rule: always loaded, holding repository-wide rules and the index of conditional rules. | It is a component, not a separate kind. | aksa-setup session | active |
| D-008 | 2026-10-19 | decision | components, memory | Component definitions live in `vocabulary.md`; rules link to them instead of restating them. | One definition per term. | aksa-setup session | active |
| D-010 | 2026-10-19 | decision | git | Commits and pull requests may carry AI co-author trailers. | The owner reversed the earlier ban. | aksa-setup session | active |
| D-011 | 2026-10-19 | decision | permissions | `.claude/settings.json` (shared, tracked) allows `git`, `gh` and `uv run` commands without prompts. | The owner chose shared over per-machine permissions. | aksa-setup session | active |
| D-012 | 2026-10-19 | decision | paths | `config/environment.yaml` is the only file allowed to hold absolute or machine-specific paths; everything else uses repo-relative paths and the repo-root symlinks. | The machine environment belongs to aksa as a whole, not to the agentic components. | aksa-setup session | active |
| D-013 | 2026-10-19 | rejection | components, config | No `Config` component type; repo-root `config/` holds repository settings read by scripts. | The existing component types already cover it; settings are not agentic. | aksa-setup session | active |
| D-014 | 2026-10-19 | decision | components, rules | `agentic/rules/components.md` is the single standard for all component kinds, marking which rules tests enforce; `review-component` holds only the review procedure. | One standard avoids drift between authoring guidance, review, and checks. | aksa-setup session | active |
| D-015 | 2026-10-19 | decision | memory, kb | Memory means the governed context about aksa in `agentic/memory/` (vocabulary and decisions); domain knowledge lives in the Knowledge Base, an external resource reached through `.kb`. | One meaning per term removes the conflict over whether `.kb` is a component. | memory-kb session | active |
| D-016 | 2026-10-19 | decision | memory | `decisions.md` holds active rows only; a superseded row gets its Status set and moves to `decisions-history.md`. Area tags come from the list in the `decisions.md` header. | Agents read only live decisions, and history stays complete; a fixed tag list keeps grep reliable. | memory-kb session | active |
| D-017 | 2026-10-19 | decision | kb | The Knowledge Base has `inbox/`, `raw/`, `wiki/`, `outputs/`, a generated `index.md`, and an append-only `log.md`; only `wiki/` is trusted and retrieved, and entries reach it only through `review-kb`. | Progressive retrieval through a generated index keeps lookups cheap, and one approval gate keeps the wiki trustworthy. | memory-kb session | active |
| D-018 | 2026-10-19 | decision | kb, git | The Knowledge Base is versioned in its own git repository, never committed to aksa. | Agent edits to knowledge must be reviewable and revertible. | memory-kb session | active |
| D-019 | 2026-10-19 | decision | memory | Vendor auto-memory (such as Claude's per-project memory) holds personal preferences only; facts about aksa go to Memory and domain facts to the Knowledge Base. | Prevents shadow memory outside the repository and the decision process. | memory-kb session | active |
