# Decisions

Agreed decisions, one row each, newest at the bottom. Never silently override one; a reversal is a new row and the old row's Status becomes `superseded by D-n`.

- Kind: `decision`, `rejection` (a rejected enhancement with a durable reason), `not-feasible`. Area: the part it touches, for grep.
- Why is one sentence; the full reasoning stays in the Source issue or run comment.
- Append-only: Status is the only editable field. Ids are never reused.

| ID | Date | Kind | Area | Decision | Why | Source | Status |
|---|---|---|---|---|---|---|---|
| D-001 | 2026-10-19 | decision | naming | The project is named `aksa` everywhere (repository, package, sync manifest `.aksa-sync.json`). | One name avoids the kalp/aksa/ark drift found in the first review. | aksa-setup session | active |
| D-002 | 2026-10-19 | decision | paths | `agentic/config/environment.yaml` is the only file allowed to hold absolute or machine-specific paths; everything else uses repo-relative paths and the repo-root symlinks. | Keeps machine details in one place so the rest of the repository is portable. | aksa-setup session | active |
| D-003 | 2026-10-19 | decision | sync | `sync_vendors.py` syncs components only to repo-level vendor folders (such as `.claude/skills`), never to global home folders. | Keeps each repository and worktree self-contained. | aksa-setup session | active |
| D-004 | 2026-10-19 | decision | sync, skills | Skill sources stay vendor-neutral; OpenCode gets synced copies with its required frontmatter added by the script. | Vendor-specific fields belong to the sync step, not to every skill. | aksa-setup session | active |
| D-005 | 2026-10-19 | decision | skills | Skill names use lowercase hyphenated verb-object form, such as `record-decision`. | Names read as the action the skill performs. | aksa-setup session | active |
| D-006 | 2026-10-19 | decision | sync | The vendor sync script is `sync_vendors.py`, organized by component kind; skills are the first kind. | Hooks, agents and instructions will sync through the same script later. | aksa-setup session | active |
| D-007 | 2026-10-19 | decision | components | `AGENTS.md` is the root Rule: always loaded, holding repository-wide rules and the index of conditional rules. | It is a component, not a separate kind. | aksa-setup session | active |
| D-008 | 2026-10-19 | decision | components, memory | Component definitions live in `vocabulary.md`; rules link to them instead of restating them. | One definition per term. | aksa-setup session | active |
| D-009 | 2026-10-19 | rejection | components | No `Config` component type; `agentic/config/` holds shared settings read by scripts. | The existing component types already cover it. | aksa-setup session | active |
| D-010 | 2026-10-19 | decision | git | Commits and pull requests may carry AI co-author trailers. | The owner reversed the earlier ban. | aksa-setup session | active |
| D-011 | 2026-10-19 | decision | permissions | `.claude/settings.json` (shared, tracked) allows `git`, `gh` and `uv run` commands without prompts. | The owner chose shared over per-machine permissions. | aksa-setup session | active |
