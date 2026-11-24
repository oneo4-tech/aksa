---
name: research-video
description: Use at a video's research stage, from youtube-producer, or when the owner asks to research or recheck a video's claims. Researches one content issue from primary sources into videos/<n>/research.md and the claims list videos/<n>/citations.json, each quote checked on its live page with a link that opens the page at it, the evidence gate 2 requires.
---

# Research video

## Inputs and prerequisites

- The channel and `#<n>`, a content issue at stage `research` (from `youtube-producer`), or at a later stage before gate 2 to recheck its claims. No channel or issue: ask the owner which.
- Written below: `C` for `uv run agentic/scripts/content_issue.py`, `E` for `uv run agentic/skills/content/research-video/scripts/evidence.py`, and `W` for the workspace `.projects/content/yt-<channel>/`.
- The channel workspace, checked with `uv run agentic/scripts/youtube_channel.py check <channel>`; exit 2: show its message and stop. Read the style guide sections `Writing rules` (how claims and interpretations are worded) and `Gate 2 checklist` (what the owner checks of the research).
- The video's idea: its Brief from `gh issue view <n> --json title,body`, and `W/videos/<n>/idea-card.json` when `scan-video-ideas` wrote one (its `claim`, `rst_concept`, `proof`, and `sources`).
- Web search and page fetch tools, and Google Chrome for `E`. Without web tools, research the Knowledge Base only and list every unsourced claim under Gaps; without Chrome, `E` exits 1: report it and stop.

## Procedure

1. **Check the stage:** `C status <n> --channel <channel>` must show stage `research`, or for a recheck `script` or `demo` with gate 2 not in `approved`; else stop and report the stage.
2. **List the claims.** From the brief and idea card, write each fact the video will state as one short, atomic claim: what a tool does, which version added it, what a specification or RST author says. A claim that needs two facts becomes two claims. Each key concept the video teaches, such as mutation testing or testing versus checking, gets at least one claim from its primary source page: `package-video` links only those pages, or their site roots, under the description's `References:`.
3. **Find primary sources, Knowledge Base first.** Run `get-kb` for each claim, then search the web for the rest. Allowed: the web sources `research-topic` allows (official documentation, specifications, source repositories, release notes, changelogs), primary sources first, plus the RST authors' own sites (satisfice.com, developsense.com, rapid-software-testing.com) for RST concepts; everything `research-topic` bans stays banned. Open each page, note its version or date, and drop any source outside the list.
4. **Write `W/videos/<n>/citations.json`:** a JSON list, one object per claim with `id` (`C1`, `C2`, ...), `claim` (as the script will say it), `url`, and `quote`, the shortest full line of the rendered page that states the claim, copied from the page, never retyped or paraphrased. The format is in `scripts/evidence.py`.
5. **Check the evidence:** `E <channel> <n>`. It loads each page in Chrome, checks each quote exactly (only whitespace normalised), and writes `link`, `found`, and `checked` into the file.
   - Exit 3: for each claim it names, copy the quote again from the page, find another allowed source that states it, or move the claim to "The demo must prove" or drop it. Then run `E` again.
   - Exit 1: a page did not load (its `error` field) or Chrome did not start; run `E` once more, then replace the source or report blocked. Exit 2: fix the fields it names.
   - Repeat until exit 0.
6. **Write `W/videos/<n>/research.md`** from `references/research-template.md`: the sources, the claims table from `citations.json` with each link, the claims only the demo can prove, the interpretations worded per `Writing rules`, and the gaps.
7. **Report on the issue:** write a scratch file of the line `YouTube: research` then the Claims table and "The demo must prove" list from `research.md`, and post it with `gh issue comment <n> --body-file <file>`. Return to the producer, checking the research against `Gate 2 checklist` and noting each item it fails.

## Output

The `YouTube: research` comment's link, the claim count (all found), the claims the demo must prove, and the gaps. `write-video-script` cites claims by id; gate 2 refuses the video while any claim in `citations.json` is not found. A refused channel, a stage mismatch, Chrome missing, or a claim with no allowed source is reported as blocked with the script's message.

## Constraints

- Fields `link`, `found`, `checked`, and `error` are written only by `E`; never set them by hand. A claim stays a fact in the script only once its quote is found.
- Evidence is the link, the quoted line, and the exact-match check; no screenshots or page snapshots.
- RST concepts are credited to James Bach and Michael Bolton in their own words; no claim implies their endorsement.
- Never passes a gate, moves a stage, or edits labels or the body; `C` and `youtube-producer` own those (D-042). Never commits workspace files to aksa.
- Never fill a claim from memory, and never put aksa-internal text, file paths, or secrets in a search query.

## Done when

- `E <channel> <n>` exited 0 on the final `citations.json`: every claim found on its page.
- Every key concept the video teaches has a claim from its primary source page.
- Every source in `research.md` is on the allowed list, and every claim row in it matches an entry of `citations.json` by id, claim, and link.
- `research.md` has no placeholder left and no em dash.
- The `YouTube: research` comment is on the issue.
