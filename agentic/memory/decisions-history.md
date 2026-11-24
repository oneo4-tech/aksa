# Decisions history

Superseded decisions, moved from `decisions.md` (D-016). Read only to learn why a decision changed. Rows are never edited.

| ID | Date | Kind | Area | Decision | Why | Source | Status |
|---|---|---|---|---|---|---|---|
| D-002 | 2026-10-19 | decision | paths | `agentic/config/environment.yaml` is the only file allowed to hold absolute or machine-specific paths; everything else uses repo-relative paths and the repo-root symlinks. | Keeps machine details in one place so the rest of the repository is portable. | aksa-setup session | superseded by D-012 |
| D-009 | 2026-10-19 | rejection | components | No `Config` component type; `agentic/config/` holds shared settings read by scripts. | The existing component types already cover it. | aksa-setup session | superseded by D-013 |
| D-031 | 2026-10-20 | decision | git, naming | Branches are `<prefix>/<n>-<slug>` for a small run, `int/<n>-<slug>` for an integration branch, `<prefix>/<n>-t<k>-<slug>` for a task, and `chore/release-vX.Y.Z` for a release, each in its own worktree from `new_worktree.py`. | Every branch names its factory issue, and integration branches stand out. | #5 | superseded by D-039 |
| D-028 | 2026-10-20 | decision | factory, git | Without asking each time, the factory squash-merges verified tasks into a run's integration branch and changes the labels, sections, and comments of its own factory issues; only the owner merges into `main`. | Gates already approve the content, and asking for every change would stall each run. | #5 | superseded by D-040 |
| D-041 | 2026-10-23 | decision | skills, components | Add `content` skill category for content creation and publishing workflows (newsletters, videos, articles). | Owner agreed in #31 Concept decision #3; #31 builds first and records the category per D-022. | #31 | superseded by D-048 |
| D-046 | 2026-10-23 | decision | skills, components | The `content` skill category holds content production pipelines outside software delivery, such as `run-youtube` and its specialist skills. | Content work is not a Software Work Request and fits no existing category. | #28 | superseded by D-048 |
