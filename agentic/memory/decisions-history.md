# Decisions history

Superseded decisions, moved from `decisions.md` (D-016). Read only to learn why a decision changed. Rows are never edited.

| ID | Date | Kind | Area | Decision | Why | Source | Status |
|---|---|---|---|---|---|---|---|
| D-002 | 2026-10-19 | decision | paths | `agentic/config/environment.yaml` is the only file allowed to hold absolute or machine-specific paths; everything else uses repo-relative paths and the repo-root symlinks. | Keeps machine details in one place so the rest of the repository is portable. | aksa-setup session | superseded by D-012 |
| D-009 | 2026-10-19 | rejection | components | No `Config` component type; `agentic/config/` holds shared settings read by scripts. | The existing component types already cover it. | aksa-setup session | superseded by D-013 |
