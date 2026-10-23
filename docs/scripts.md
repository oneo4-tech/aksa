# Scripts Reference

Deterministic operations in `agentic/scripts/`. All have tests in `tests/`.

## Scripts

| Script | Purpose | Key Flags |
|--------|---------|-----------|
| `link_external.py` | Create/repair symlinks from `config/environment.yaml` | `--check` |
| `sync_vendors.py` | Sync `agentic/skills/` to vendor folders | `--check`, `<vendor>...` |
| `kb_index.py` | Rebuild `.kb/index.md` from wiki frontmatter | `--check` |
| `factory_issue.py` | **Only writer** of factory issue labels/body | `status`, `labels` |
| `github_issues.py` | Thin `gh` layer for issues, labels, and sub-issues, imported by `factory_issue.py` and `content_issue.py` | none |
| `content_issue.py` | **Only writer** of content (video) issue labels/body | `new`, `stage`, `gate`, `hours`, `summary`, `status` |
| `youtube_channel.py` | Load and validate a channel's config and style guide; set up its workspace | `check`, `init` |
| `competition.py` (skill `scan-video-ideas`) | Score an idea card and add the closest YouTube videos, cached per query | `CHANNEL CARD`, `--top` |
| `evidence.py` (skill `research-video`) | Check each claim's quote on its live page and add a text-fragment link | `CHANNEL N` |
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

## youtube_channel.py

Loads a YouTube channel from its workspace `.projects/content/yt-<channel>/` (never committed to aksa):
- `channel.yaml`: machine values (name, url, voice, palette, loudness, music_db, cadence with its weekly owner-hours budget, labels, pronunciation, banned_phrases, title_max); schema in the script docstring
- `style-guide.md`: human rules, one `##` section per required heading (Voice through Gate 3 checklist, listed in `SECTIONS`)

A missing file, field, or section stops with a message naming each one.

```bash
# Validate (exit 0 ok, 2 invalid)
uv run agentic/scripts/youtube_channel.py check testlab

# Make the workspace a git repo that ignores media, with videos/ (idempotent)
uv run agentic/scripts/youtube_channel.py init testlab
```

Content scripts import `load(channel)`; no tracked file holds a channel URL.

---

## content_issue.py

One GitHub issue per video, kept apart from factory runs by `kind:youtube` (D-042). Labels, stage order, and gates: `config/content.yaml`; `needs:owner` comes from `config/factory.yaml`.

- Labels: `kind:youtube`, `channel:<name>` (from `channel.yaml` `labels.channel`, created on demand), `content-type:long-form|short`, one `youtube-stage:*`
- Stages: idea, research, script, demo, recording, editing, packaging, review, ready; one forward at a time
- Gates: leaving `idea` (gate 1), `demo` (gate 2), and `review` (gate 3) needs the owner's yes, recorded as a `YouTube: gate N approved.` comment
- Gate 2 is refused while `videos/<n>/citations.json` (in the workspace of the channel named by the issue's `YouTube: filed for channel` comment) is missing or invalid, or has any claim never checked, changed since checked, or not found; the refusal names each claim
- Hours: each entry is a dated `YouTube: hours `<stage>` +<h> on <date>.` comment; the body's `## Hours` table is the per-stage running total, rebuilt by the script from those comments

```bash
# File a video at idea; creates videos/<issue-number>/ in the channel workspace
uv run agentic/scripts/content_issue.py new testlab --type long-form --title "..." --brief-file brief.md
# A Short cut from long-form #12 (sub-issue), or an independent Short linking it
uv run agentic/scripts/content_issue.py new testlab --type short --title "..." --parent 12
uv run agentic/scripts/content_issue.py new testlab --type short --title "..." --related 12

uv run agentic/scripts/content_issue.py status 14 --channel testlab   # resume one video
uv run agentic/scripts/content_issue.py status --channel testlab      # queue, waiting first
uv run agentic/scripts/content_issue.py gate 14 1 --request           # wait for the owner
uv run agentic/scripts/content_issue.py gate 14 1 --approve           # only on the owner's yes
uv run agentic/scripts/content_issue.py stage 14 research
uv run agentic/scripts/content_issue.py hours 14 --stage idea --hours 1.5   # --date YYYY-MM-DD to log a past day
# Weekly pilot summary (JSON): per-video hours that ISO week, long-form and Shorts counts,
# total vs channel.yaml cadence.owner_hours_per_week; verdict pass only with at least the
# cadence's long-form and Shorts within the budget, else fail with reasons
uv run agentic/scripts/content_issue.py summary --channel testlab --week 2026-W44
```

Exit codes: 0 done, 1 GitHub/config/file error, 2 bad input or invalid channel, 3 refused.

---

## Skill scripts

A script serving one skill lives in that skill's `scripts/` folder (`agentic/rules/components.md`); its tests are still in `tests/`.

### competition.py (`scan-video-ideas`)

Validates an idea card (JSON: pillar, RST concept, claim, tester's question, proof, format, hook, sources, risks, scores, search query and anchor terms), computes its weighted score (lens 3, proof 3, freshness 2, audience pull 2, distinctness 2, effort 1; max 65, parked under 40), and adds the closest relevant YouTube videos from the YouTube Data API v3 (`search.list`, then `videos.list`). Needs `GOOGLE_CLOUD_API_KEY`. Each query's results are cached for the day in the channel workspace's `research/competition-cache/`, so no query spends search quota (100 a day) twice.

```bash
# Prints JSON (score, closest videos); writes card.md beside the card, the brief for content_issue.py new
uv run --env-file .env agentic/skills/content/scan-video-ideas/scripts/competition.py testlab card.json
```

Exit codes: 0 done, 1 YouTube/file error, 2 bad input (invalid card or channel, key missing).

### evidence.py (`research-video`)

Reads a video's `videos/<n>/citations.json`, a JSON list of claims (`id`, `claim`, `url`, `quote`). Loads each source page once in the system Chrome through Playwright (`playwright` dependency, Chrome channel; no bundled browser), checks each quote is on the rendered text exactly, with only whitespace normalised, and writes back per claim: `link` (a text fragment `url#:~:text=<first 4 words>,<last 3 words>`, the whole quote when it has 7 words or fewer, that opens the page at the quote), `found`, `checked` (UTC), and `error` for a page that did not load. No screenshots or snapshots. `content_issue.py` gate 2 reads the same file through `gate_problems`.

```bash
# Prints JSON (claims, found, the ids not found)
uv run agentic/skills/content/research-video/scripts/evidence.py testlab 14
```

Exit codes: 0 every quote found, 1 page/browser/file error, 2 bad input (invalid citations file or channel), 3 a quote not found.

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