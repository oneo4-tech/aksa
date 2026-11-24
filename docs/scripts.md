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
| `check_script.py` (skill `write-video-script`) | Check a video's script against the writing rules, length target, and citations | `CHANNEL N` |
| `scaffold.py` (skill `build-video-demo`) | Create a video's demo folder in the demo repository clone and print its description link | `CHANNEL N --slug --proves --skill --rule` |
| `narrate.py` (skill `narrate-video`) | Narrate a video's scenes with the channel voice and check each transcript for leaked markup | `CHANNEL N` |
| `render.py` (skill `render-video`) | Render a video's scenes into silent clips timed from the narration, with terminal scenes from the VHS recording | `CHANNEL N` |
| `assemble.py` (skill `render-video`) | Assemble the clips, narration, and music bed into the final video with two-pass loudness and captions from the script | `CHANNEL N` |
| `thumbnail.py` (skill `design-thumbnail`) | Compose a video's thumbnail, or up to 3 candidates and their contact sheet, from a layout template with the exact challenge text, around cached, text-free Gemini art or none | `CHANNEL N --text [--text ...] [--subject] [--layout] [--code --mark --marker --chip] [--candidates] [--new-art]`, or `--pick K` |
| `branding.py` (skill `brand-channel`) | Generate the channel's avatar, banner, watermark, and wordmarks from the logo spec geometry and palette, as SVG and PNG | `CHANNEL` |
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
- `channel.yaml`: machine values (name, url, voice, palette, loudness, music_db, cadence with its weekly owner-hours budget, labels, pronunciation, banned_phrases, title_max, demos with the public demo repository and its local clone folder under `.projects/content/`, thumbnail with the art style every thumbnail's art is asked in, branding with the wordmark suffix words and the banner's two lines); schema in the script docstring
- `style-guide.md`: human rules, one `##` section per required heading (Voice through Gate 3 checklist, listed in `SECTIONS`)

A missing file, field, or section stops with a message naming each one.

```bash
# Validate (exit 0 ok, 2 invalid)
uv run agentic/scripts/youtube_channel.py check testlab

# Make the workspace a git repo that ignores media, with videos/ (idempotent)
uv run agentic/scripts/youtube_channel.py init testlab
```

Content scripts import `load(channel)` and the pure writing checks `banned_phrases(text, config)` (the channel's banned phrases found in text: whole words, any case, any spacing, curly apostrophes matched) and `title_ok(title, config)` (non-blank and at most `title_max` characters); no tracked file holds a channel URL.

---

## content_issue.py

One GitHub issue per video, kept apart from factory runs by `kind:youtube` (D-047). Labels, stage order, and gates: `config/content.yaml`; `needs:owner` comes from `config/factory.yaml`.

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

### check_script.py (`write-video-script`)

Reads a video's `videos/<n>/script.json`: `title`, `type` (`long-form` or `short`), `structure` (`challenge-first`, `incident-story`, `myth-buster`), `acronyms`, and `scenes`, each with `kind` (`title`, `points`, `code`, `terminal`), `heading`, `visual` or for a code scene `code`, `say` (the narration), `claims` (citation ids), and optional `kit` (`true` on the "Take it to your agent" beat). Refuses, naming each problem: a banned phrase from `channel.yaml` in the title, a heading, visual, or say; a title over `title_max`; in `say`, a sentence of twenty words or more, three sentences of sixteen or more in a row, digits, markup other than `//` and `...`, or more than one CAPS word per sentence other than `acronyms`; a claim id not in `citations.json` or not found; a length outside 300-600 s (long-form) or 30-60 s (Short); a cold open (scene 1) that is a `title` slide, or whose `visual` has under two thirds of its words in its `say`; no `kit` scene among the last two. Length estimate: words at 172 words a minute times `voice.pace` (about 158 at pace 0.92), the measured speed of content issue #38 (731 words narrated in 278.4 s); `//` and `...` add no time of their own. `say` keeps the real words; `narrate.py` applies the `pronunciation` list at synthesis.

```bash
# Prints JSON (scenes, words, seconds, target_seconds, words_per_minute)
uv run agentic/skills/content/write-video-script/scripts/check_script.py testlab 14
```

Exit codes: 0 the script passes, 1 file error, 2 bad input (invalid script file or channel), 3 refused (a writing rule, cold open, kit beat, length, or citation problem).

### scaffold.py (`build-video-demo`)

Reads `channel.yaml` `demos`: `repo` (the public repository, `owner/name`) and `path` (its local clone, `.projects/content/<path>/`), `channel.yaml` `name` and `url`, and the video's `videos/<n>/citations.json`. Creates `<clone>/<n>-<slug>/` with `README.md` (the content issue's title, what the demo proves, how to run, a Video section with the line `- Video: not published yet` that `package.py --video-url` fills, the channel link, and the folder link, a Sources section listing each claim with its quoted line and text-fragment link, the MIT note; never a link to the private aksa tracker), a "Use it with your AI agent" section with the kit link and copy commands, `demo/`, `tests/`, `demo.tape` (VHS: Menlo 30, 1920x1080, Dracula), `ai-kit/` (`AGENTS.md` with each `--rule`, `skills/<--skill>/SKILL.md`, an Agent Skill answering the rules, and an empty `scripts/` for helpers), and a `.gitignore` for recorded media. A `--skill` not lowercase verb-object or a blank `--rule` is bad input. Refuses an existing folder, a missing clone or one that is not a git repository, a repository missing on GitHub (the owner creates it once), and citations missing or not all verified (`evidence.py`). Only reads GitHub: never creates a repository, commits, or pushes.

```bash
# Prints the folder, then https://github.com/<repo>/tree/main/<n>-<slug>
uv run agentic/skills/content/build-video-demo/scripts/scaffold.py testlab 14 --slug mocked-tests --proves "..." \
  --skill check-test-can-fail --rule "..." --rule "..."
```

Exit codes: 0 created, 1 GitHub or file error, 2 bad input (invalid channel or slug, or an issue without the channel's label), 3 refused.

### narrate.py (`narrate-video`)

Reads a video's `videos/<n>/script.json` and `channel.yaml` `voice` (`id`, `style`, `pace`) and `pronunciation`. Per scene: respells the `pronunciation` words of `say` (whole words, any case; `//` and `...` kept), posts one Gemini Interactions API request (`gemini-3.8-flash-tts`, the voice id in `generation_config.speech_config`, the style only in the text's `speech_metadata` annotation, since style inside the text is spoken), decodes the base64 WAV, applies `voice.pace` with ffmpeg `atempo` (pitch kept) into `narration/NN.wav`, and transcribes it with `whisper-cli` and the `base.en` model (`WHISPER_MODEL`, else `.cache/whisper/ggml-base.en.bin` in the home folder). A scene is refused when its transcript has a markup word `say` lacks (`slash`, `pause`, `ellipsis`, `dot`), an angle-bracket tag or `//`, the voice style, or a word match (difflib ratio, both sides respelled) under 0.9. Writes `narration/report.json`. Needs `GEMINI_API_KEY`, never printed.

```bash
# Prints JSON (per scene file, transcript, match, problems; match_min; passed)
uv run --env-file .env agentic/skills/content/narrate-video/scripts/narrate.py testlab 14
```

Exit codes: 0 every scene clean, 1 Gemini/tool/file error or key missing, 2 bad input (invalid script file or channel), 3 refused (a scene leaked markup or misses the script).

### render.py (`render-video`)

Reads a video's `videos/<n>/script.json` (`type`, and per scene `kind`, `heading`, `visual` or `code`), `narration/NN.wav`, `demo.json` and the demo files `code` scenes show (in the clone at `channel.yaml` `demos.path`), `demo.mp4` when it exists, and `channel.yaml` `name` and `palette`. Per scene: `whisper-cli -ml 1 -sow -ojf` gives word start times; the scene lasts 0.4 s + its narration + 0.6 s, rounded up to whole frames at 30 fps. Each item (a title word, a point, a terminal line) appears at the first of its words heard after the previous item's, else at its share of the narration; a code scene types its file in, then focuses the line naming a heard word (held at least 1.2 s), the rest dimmed. Drawn scenes fill `references/<kind>.html` with the cue timeline as JSON, the shared `scene.css` and `scene.js`, and the Space Grotesk and Fira Code files embedded (`RENDER_FONTS`, else `.cache/fonts` in the home folder; nothing loads from the network); the system Chrome, with software raster so two renders give identical frames, seeks each frame (`window.seek(t)`) for a JPEG, and ffmpeg encodes them (H.264, CRF 18, no audio). Terminal scenes, when `demo.mp4` exists, play it in order from where the previous terminal scene ended, fitted inside the frame on the palette background with 0.3 s fades, the final frame held past its end. Writes `render/scenes/NN.mp4` and `render/scenes.json` (type, width, height, fps; per scene kind, source, file, narration, seconds, frames, lead).

```bash
# Prints render/scenes.json
uv run agentic/skills/content/render-video/scripts/render.py testlab 14
```

Exit codes: 0 every scene rendered, 1 tool/font/file error, 2 bad input (invalid script or channel, missing narration or demo file). The media test (`tests/test_render_media.py`, marker `media`) renders a two-scene fixture twice with the real tools: `uv run pytest -m media`; the default run and CI leave it out.

### assemble.py (`render-video`)

Reads a video's `videos/<n>/script.json` (`type`, each scene's `say`), `render/scenes.json` and its clips from `render.py`, `narration/NN.wav`, the channel's music bed `music/bed.mp3` in the workspace (supplied by the owner), and `channel.yaml` `loudness` and `music_db`. The clips play in order (ffmpeg concat); each narration starts at its scene's start plus its `lead`; the bed loops under the voice at `music_db` dB and fades out over the last 2 s. Loudness is two-pass `loudnorm`: the first pass measures the mix, the second applies the measured values with `linear=true` to `loudness.lufs`, aiming 0.5 dB below `loudness.true_peak` since AAC encoding lifts peaks a little. Captions use the script's `say` words with `//` and `...` removed (real words, not the pronunciation respellings), timed by `whisper-cli -ml 1` word starts (matched words at their heard start, the rest sharing the time between): a long-form gets `render/final.srt` (a cue per sentence, at most 7 words and 42 characters) with the clips copied unchanged; a Short gets burned captions, three words with the word being said in the accent colour, in the lower area clear of the Shorts buttons, drawn per state from `references/captions.html` in Chrome as transparent PNGs and overlaid on whole frames. Writes `render/final.mp4` (H.264, AAC 192 kb/s 48 kHz) and prints type, width, height, seconds, file, captions, and the mix's measured loudness.

```sh
uv run agentic/skills/content/render-video/scripts/assemble.py testlab 14
```

Exit codes: 0 assembled, 1 tool/font/file error, 2 bad input (invalid script or channel, missing or stale `scenes.json`, missing clip, narration, or music bed, silent mix). The media test in `tests/test_render_media.py` speaks a two-scene fixture with macOS `say`, renders and assembles it twice, and checks size, -14 LUFS within 1 LU, true peak at or below -1 dBTP, SRT text equal to the script, and identical frames.

### thumbnail.py (`design-thumbnail`)

Reads `channel.yaml` `palette` and `thumbnail.art_style`, and the title of `videos/<n>/script.json` (missing: exit 2). `--text` is 2 to 4 words on one line that end with "?" or use a challenge verb (spot, find, catch, guess, fix, break, beat, prove); when the script title names AI, each text names AI unless the subject or the spot-the-bug chip does (else exit 2). Layouts: `split` and `big-subject` by issue number, `spot-the-bug` (6 to 10 code lines from `--code`, line `--mark` marked by `--marker` highlight, squiggle, or underline with a small bug glyph, under the `--chip` default "Written by AI"), and `face-off`. Art: with `--subject` only, one Gemini `generateContent` request a candidate (`gemini-3.1-flash-image`, about USD 0.07 an image, no free tier) from a text-overlay prompt in the channel's art style, cached in `thumbnail/art-<k>.<ext>` and `art.json`; another prompt is refused (exit 3) unless `--new-art`. `--candidates N` (1 to 3) composes `thumbnail-<k>` per art image, or free, without a subject, per `--text` or `--marker` given N times, plus `thumbnail-candidates.png` at full, 320 px, and 168 px width; `--pick K` copies one to `thumbnail.<ext>`. Text and marker contrast are checked (WCAG 2.2) and the text never shrinks below a 15% cap height. The system Chrome shoots the 1280x720 page at 3x for 3840x2160, as PNG, else JPEG at quality 92 down to 65, the first at most 2,000,000 bytes. Needs `GEMINI_API_KEY` only for new art, never printed.

```bash
# Prints JSON (layout, text, art generated or cached, prompt, file, format, quality, bytes, width, height)
uv run agentic/skills/content/design-thumbnail/scripts/thumbnail.py testlab 38 --layout spot-the-bug --code .projects/content/yt-testlab/videos/38/thumbnail/code.txt --mark 4 --text "AI wrote this. Bug?" --text "Can you spot it?" --text "Will this fail?" --candidates 3
```

Exit codes: 0 written, 1 Gemini/Chrome/font/file error, key missing, or over 2 MB in every format, 2 bad input (invalid channel, text, subject, code, or chip, no challenge, no AI cue, no video folder or script), 3 refused (cached art from another prompt without `--new-art`). The media test (`tests/test_thumbnail_media.py`, marker `media`) composes each layout and the free marker candidates with their contact sheet in the real Chrome and checks 3840x2160 and the size limit.

### branding.py (`brand-channel`)

Reads `channel.yaml` `palette` and `branding` (`wordmarks`: suffix words, the first on the banner; `tagline`; `subline`). Builds each asset's SVG from the oneo4 logo spec v0.4 geometry, unaltered (glyph paths, advance 68, suffix from x = 500 at 8.4 against the tag's 14, icon viewBox `2 -18 200 200`), with name strokes first, suffix next, and syntax strokes on top: `avatar` 800x800 (icon at stroke 16 inside YouTube's crop circle, one x-height clear), `banner` 2048x1152 (first wordmark, tagline in Space Grotesk 46 in the name colour, subline in Fira Code 30 in the suffix colour, stacked inside the centred 1235x338 safe area), `watermark` 150x150 (icon at stroke 20, transparent), and `wordmark-<word>` 2400 wide. A letter outside the spec's glyphs (a b c e h k l r s t) or a line too wide for the safe area is refused (exit 2) before anything is written. The system Chrome renders each SVG at its size with the fonts embedded (`RENDER_FONTS`); every render must be its size and under YouTube's limit (avatar 15 MB, banner 6 MB, watermark 1 MB) before `branding/<asset>.svg` and `.png` are written. Uploads nothing.

```bash
# Prints JSON (each asset's name, svg, png, width, height, bytes, limit)
uv run agentic/skills/content/brand-channel/scripts/branding.py testlab
```

Exit codes: 0 written, 1 Chrome/font/file error or a render of the wrong size or over its limit, 2 bad input (invalid channel, letter without a glyph, line too wide). The media test (`tests/test_branding_media.py`, marker `media`) renders every asset in the real Chrome and checks sizes, limits, and the banner lines measured inside the safe area.

### package.py (`package-video`)

Reads a video's `videos/<n>/metadata.json` (`title`, `hook`, `chapters` as `{scene, title}`, `tags`, `hashtags`, `paid_promotion`, and for a Short `related`), `script.json` `type`, `render/scenes.json` (`fps`, each scene's `frames`; a chapter starts where its scene starts), `demo.json` `link`, `citations.json` (every claim verified, `evidence.py`), and `channel.yaml` `title_max` and `banned_phrases`. Writes `description.md` (the hook; chapters, or for a Short `Full video:` and the long-form's `video_url`; `Code:` and the demo link, `AI kit:` and the demo link's `/ai-kit`; `Sources:` with each claim and its text-fragment link; `Narration uses a synthetic AI voice.` and the paid promotion or `No paid promotion.`; the hashtags) and `packaging.json` (`type`, `title`, `description`, `chapters` as `{at, title}`, `tags`, `hashtags`, `paid_promotion`, `video_url`, and for a Short `related_video`). Refuses, naming each problem: a blank title or hook, a title over `title_max`, a banned phrase in the title, hook, or a chapter title; chapters not starting at scene 1 (00:00), fewer than three, not ascending, naming a scene not rendered, or shorter than 10 s; a Short with chapters or whose long-form has no `video_url`; tags outside 5-8; hashtags outside 8-15 (the first three show above the title; YouTube ignores all past fifteen), one not `#` and one word, or one repeated; `<` or `>`; a description over 5,000 characters; no demo link; citations missing or not verified. `--video-url` (a `youtube.com/watch`, `youtube.com/shorts`, or `youtu.be` link) records `video_url` in an existing `packaging.json` and, when `demo.json`'s folder is `<n>-<slug>`, fills that README's `- Video:` line in the local demo clone and rebuilds its Sources section (`scaffold.py`). Local files only: never commits, pushes, or calls YouTube.

```bash
# Prints the files written; with --video-url, the recorded link and the README filled
uv run agentic/skills/content/package-video/scripts/package.py testlab 14
uv run agentic/skills/content/package-video/scripts/package.py testlab 14 --video-url https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

Exit codes: 0 written, 1 file error, 2 bad input (invalid channel, missing or invalid `metadata.json`, `script.json`, or `scenes.json`, a link that is not a YouTube video), 3 refused (a packaging rule, a missing demo link or citations, `--video-url` before packaging).

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