---
name: scan-video-ideas
description: Use for a channel's weekly backlog scan, or at a video's idea stage. Scans the channel's sources through the Rapid Software Testing lens into scored idea cards with the closest existing YouTube videos, then files the owner's picks as video issues; for one video issue, writes its idea card, score, and competition research.
---

# Scan video ideas

## Inputs and prerequisites

- The channel, and either nothing (weekly mode) or `#<n>`, a content issue at stage `idea` (single-issue mode, from `youtube-producer`). No channel: ask the owner which channel.
- The channel workspace, checked with `uv run agentic/scripts/youtube_channel.py check <channel>`; exit 2: show its message and stop. Read the style guide sections `Writing rules`, `Metadata`, `Shorts`, and `Gate 1 checklist`, and `title_max` in `channel.yaml`.
- The channel's pillars, from its Knowledge Base profile through `get-kb`; none found: ask the owner and stop.
- `GOOGLE_CLOUD_API_KEY` in `.env`: a Google Cloud API key with the YouTube Data API v3 enabled. Missing: say so and stop; never print it.
- `gh` signed in, for filing and comments.
- Written below: `S` for `uv run --env-file .env agentic/skills/content/scan-video-ideas/scripts/competition.py`, `C` for `uv run agentic/scripts/content_issue.py`, and `W` for the workspace `.projects/content/yt-<channel>/`.

## Procedure

1. **Read the strategy:** `references/strategy.md` (sources, the RST lens with its attribution, and the scoring guide).
2. **Gather ideas.**
   - Weekly mode: scan each source stream for changes since the last scan (the newest folder under `W/research/ideas/`), and list the channel's videos with `C status --channel <channel>` so no idea repeats one. Keep up to 5 ideas that pass the RST lens.
   - Single-issue mode: `C status <n> --channel <channel>` must show stage `idea`, else stop and report it; read the issue's Brief with `gh issue view <n> --json title,body`. The idea is that brief.
3. **Write each idea card** as JSON, the fields in `scripts/competition.py`: weekly to `W/research/ideas/<YYYY-Www>/<slug>.json`, single-issue to `W/videos/<n>/idea-card.json`.
   - `title` challenge style within `title_max`, following `Metadata`; `claim`, `tester_question`, `proof`, and `hook` worded per `Writing rules`; `format` `long-form` or `short`, per `Shorts`.
   - `rst_concept` names the concept as RST names it; `sources` link the primary source of every claim on the card; a war story without real field notes says so in `risks`.
   - `query` is the search a viewer would type; `anchors` are term groups that every relevant video must match, such as `[["playwright"], ["agent", "healer"]]`.
   - Scores per the scoring guide.
4. **Research competition:** `S <channel> <card>` per card. It prints the score and the closest videos and writes the card as Markdown beside it (`<card>.md`). Exit 2: fix the named fields or report the missing key; exit 1: report the YouTube error and stop, since the day's search quota may be spent.
   - Rescore `distinctness` and `audience_pull` from the videos found, then run `S` again; a query searched today is answered from `W/research/competition-cache/` and costs no quota. A changed query is a new search: change it only when the first one missed the topic.
5. **Report.** Check each card against the style guide's `Gate 1 checklist` and note every item it fails beside the card.
   - Weekly mode: show the cards ranked by score, parked ones (under 40) last, each with its closest videos, and ask the owner which to file. For each pick: `C new <channel> --type <format> --title "<title>" --brief-file <card>.md`. Parked and unpicked cards stay in their week's folder.
   - Single-issue mode: write a scratch file of the line `YouTube: idea card` then the text of `<card>.md`, post it with `gh issue comment <n> --body-file <file>`, and return the card to the producer for gate 1.

## Output

Weekly: the ranked cards with scores and closest videos, and the issue number of each filed video. Single-issue: the idea card comment's link, the score, and whether it is parked. A refused channel, an invalid card, a missing key, or a YouTube error is reported as blocked with the script's message.

## Constraints

- Files only the owner's picks; never passes gate 1, moves a stage, or edits labels or the body except through `C` (D-042). Gate 1 belongs to `youtube-producer`.
- Search quota: 100 searches a day. Never delete or bypass the competition cache, and never rerun a query to refresh it on the same day.
- RST concepts are credited to James Bach and Michael Bolton; no card or brief implies their endorsement.
- Never commits workspace files to aksa, and never puts a `channel.yaml` value into a component.

## Done when

- Every card passed `S` with exit 0 and has its Markdown beside it.
- Weekly: each filed video has its issue number reported; single-issue: the `YouTube: idea card` comment is on the issue.
- No query was searched twice that day: each one has a single cache file under `W/research/competition-cache/`.
