# Scripts Reference

Deterministic operations in `agentic/scripts/`. All have tests in `tests/`.

## Scripts

| Script | Purpose | Key Flags |
|--------|---------|-----------|
| `link_external.py` | Create/repair symlinks from `config/environment.yaml` | `--check` |
| `sync_vendors.py` | Sync `agentic/skills/` to vendor folders | `--check`, `<vendor>...` |
| `kb_index.py` | Rebuild `.kb/index.md` from wiki frontmatter | `--check` |
| `factory_issue.py` | **Only writer** of factory issue labels/body | `status`, `labels` |
| `check_pr_review.py` | CI gate: verify `review-component` in PR body | — |
| `new_worktree.py` | Create git worktree with links + vendor folders | `<branch>` |

---

## link_external.py

Creates symlinks at repo root:
- `.kb/` → Knowledge Base repo
- `.projects/` → Project workspace repo
- `.worktrees/` → Worktrees directory

```bash
# Create/repair
uv run agentic/scripts/link_external.py

# Verify only
uv run agentic/scripts/link_external.py --check
```

**Config**: `config/environment.yaml` (only file with absolute paths)

```yaml
kb: "/path/to/kb-repo"
projects: "/path/to/projects-repo"
worktrees: "/path/to/worktrees-dir"
```

---

## sync_vendors.py

Syncs `agentic/skills/` → vendor skill folders.

```bash
# Sync to specific vendors
uv run agentic/scripts/sync_vendors.py claude codex

# Sync all configured vendors
uv run agentic/scripts/sync_vendors.py

# Verify only
uv run agentic/scripts/sync_vendors.py --check
```

**Vendors** (defined in script):
- `claude` → `.claude/skills/`
- `codex` → `.agents/skills/` (shared by OpenCode, Codex, Gemini, Copilot)

---

## kb_index.py

Rebuilds `.kb/index.md` from wiki page frontmatter.

```bash
# Rebuild
uv run agentic/scripts/kb_index.py

# Validate only
uv run agentic/scripts/kb_index.py --check
```

**Output**: Markdown table with title, tags, updated date, path.

---

## factory_issue.py

**Single source of truth** for factory issue management.

```bash
# Show current run status
uv run python -m agentic.scripts.factory_issue status

# Sync label set (run after config/factory.yaml changes)
uv run python -m agentic.scripts.factory_issue labels
```

**Only this script** writes factory issue labels and body. Skills use it via subprocess.

---

## check_pr_review.py

CI gate (`.github/workflows/review.yml`). Fails PR if:
- Component files changed (`agentic/**`)
- PR body lacks `## review-component result` section
- Section doesn't contain "pass" or resolved mismatches

```bash
# Run manually (simulates CI)
uv run agentic/scripts/check_pr_review.py "origin/main"
```

**Env vars** (set by CI):
- `BASE_REF` — base branch
- `PR_BODY` — PR description

---

## new_worktree.py

Creates a worktree for parallel work with full setup.

```bash
uv run agentic/scripts/new_worktree.py feature/my-feature
```

**Creates**:
- Git worktree at `.worktrees/feature-my-feature/`
- Symlinks: `.kb`, `.projects` (same as main)
- Vendor folders: `.claude/skills/`, `.agents/skills/`
- Runs `link_external.py` + `sync_vendors.py` inside worktree

**Usage**:
```bash
cd ../.worktrees/feature-my-feature
# Full aksa environment, isolated branch
```

---

## Adding a New Script

1. Create `agentic/scripts/<name>.py`
2. Add CLI with `argparse` (support `--check` for validators)
3. Add tests in `tests/test_<name>.py`
4. Follow `coding.md` (ruff, type hints, pytest)
5. Run `uv run pytest` to verify