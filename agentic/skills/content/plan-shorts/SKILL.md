---
name: plan-shorts
description: Use at a long-form video's packaging stage, from youtube-producer, or when the owner asks to plan the Shorts of a ready or published long-form video. Plans its two Shorts, each a standalone thirty to sixty second challenge with its hook in the first two seconds, cut from the long-form or independent of it, and on the owner's yes files each as a content issue at stage idea linked to the long-form.
---

# Plan Shorts

## Inputs and prerequisites

- The channel and `#<n>`, a long-form content issue at stage `packaging`, `review`, or `ready`, or closed once published. No channel or issue: ask the owner which.
- Written below: `C` for `uv run agentic/scripts/content_issue.py` and `W` for the workspace `.projects/content/yt-<channel>/`.
- The channel workspace, checked with `uv run agentic/scripts/youtube_channel.py check <channel>`; exit 2: show its message and stop. Read the style guide sections `Shorts` (format and cut rules) and `Writing rules`, the Short structure in `agentic/skills/content/write-video-script/references/structures.md`, and in `channel.yaml` `cadence.shorts_per_week` (two Shorts to each weekly long-form), `title_max`, and `banned_phrases`.
- The long-form's outputs in `W/videos/<n>/`: `script.json`, `research.md`, `citations.json`, and `demo.json`. Missing: stop and report the stage that writes it.

## Procedure

1. **Check the video:** `C status <n> --channel <channel>` must show `type` `long-form` and a stage above; else stop and report it. `gh issue view <n> --comments` already showing a `YouTube: shorts` comment: show it and stop, unless the owner asks for more Shorts.
2. **Find the moments:** from `script.json` and `research.md`, pick the ideas that work alone in under a minute: a beat with one problem shown on screen (a cut), or a claim of the research the long-form did not show (independent). Each Short has one idea, and the two differ.
3. **Plan two Shorts** (`cadence.shorts_per_week`), each under `Shorts` and the Short structure, as a brief:
   - `title`: challenge style, at most `title_max` characters, no banned phrase.
   - `kind`: `cut`, reusing the long-form's scenes, demo, and citations, or `independent`, a new script on the same topic.
   - `hook`: one line spoken in the first two seconds: the failing case and the challenge.
   - `beats`: look, reveal, and bridge, each with what is on screen, the whole thirty to sixty seconds.
   - `source`: for a cut, the long-form scene numbers; for an independent Short, the citation ids it relies on.
   - `related`: the description's `Full video:` line links the long-form (`package-video` adds it), and the owner sets the long-form as the Short's related video in YouTube Studio.
4. **Ask the owner:** show both briefs and ask for an explicit yes to file them; changes asked: revise and ask again. No yes: report the plan waiting and stop.
5. **File each Short:** write its brief to a scratch file and run `C new <channel> --type short --title "<title>" --brief-file <file>`, adding `--parent <n>` for a cut (a sub-issue of the long-form) or `--related <n>` for an independent Short. Each starts at stage `idea` with its folder `W/videos/<short>/`; `youtube-producer` takes it through its stages like any video.
   - Exit 3, a link refused: `#<n>` is not a long-form of this channel; report it. Exit 1: report the error; a Short filed before a failed sub-issue link is named in the message, so link it by hand or ask the owner.
6. **Report on the long-form issue:** write a scratch file of the line `YouTube: shorts`, then each Short's number, title, kind, and hook, and post it with `gh issue comment <n> --body-file <file>`. Return to the producer with the Shorts' numbers.

## Output

The `YouTube: shorts` comment's link and each Short's issue number, title, and kind; or the plan waiting for the owner's yes. A wrong type or stage, a missing output, or a failed `C new` is reported as blocked with its message.

## Constraints

- Files issues only on the owner's explicit yes in this session, and only through `C new`; never edits labels or bodies, passes gates, or moves stages (D-042).
- Plans; never scripts, records, or packages a Short: each Short's own stages do that, and its script is always the `challenge-first` Short structure.
- Never edits the long-form's outputs, `channel.yaml`, or the style guide. Publishes and sets nothing on YouTube; the related-video link in Studio is the owner's.

## Done when

- Two Short briefs, each one standalone idea of thirty to sixty seconds with its hook in the first two seconds and a title within `title_max`, were shown to the owner.
- On the owner's yes, each Short is a content issue at stage `idea` from `C new`, with `--parent <n>` or `--related <n>`.
- The `YouTube: shorts` comment is on the long-form issue, with no placeholder and no em dash.
