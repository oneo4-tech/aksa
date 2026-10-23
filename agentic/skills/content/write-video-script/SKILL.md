---
name: write-video-script
description: Use at a video's script stage, from youtube-producer, or when the owner asks to write or rewrite a video's script. Writes videos/<n>/script.json, scenes with heading, visual or code, narration, and the citation ids each relies on, in one of three structures, sized for five to ten minutes or a thirty to sixty second Short, and checked against the channel's writing rules, length target, and citations.
---

# Write video script

## Inputs and prerequisites

- The channel and `#<n>`, a content issue at stage `script` (from `youtube-producer`), or at `demo` with gate 2 not in `approved` for a rewrite. No channel or issue: ask the owner which.
- Written below: `C` for `uv run agentic/scripts/content_issue.py`, `K` for `uv run agentic/skills/content/write-video-script/scripts/check_script.py`, and `W` for the workspace `.projects/content/yt-<channel>/`.
- The channel workspace, checked with `uv run agentic/scripts/youtube_channel.py check <channel>`; exit 2: show its message and stop. Read the style guide sections `Writing rules`, `Voice`, `Slides and animation`, `Shorts`, and `Gate 2 checklist`, and in `channel.yaml` the `banned_phrases`, `pronunciation`, `title_max`, and `voice.pace` that `K` applies.
- The research: `W/videos/<n>/research.md` and `W/videos/<n>/citations.json` from `research-video`, every claim found. Missing, or `uv run agentic/skills/content/research-video/scripts/evidence.py <channel> <n>` not exiting 0: stop and route the video back to `research-video`.
- The idea: `W/videos/<n>/idea-card.json` when `scan-video-ideas` wrote one (its `title`, `pillar`, `claim`, `tester_question`, `proof`), else the Brief from `gh issue view <n> --json title,body`.

## Procedure

1. **Check the stage:** `C status <n> --channel <channel>` must show stage `script`, or `demo` with gate 2 not in `approved`; else stop and report the stage. Its `type` is the script's `type`: `long-form` (five to ten minutes) or `short` (thirty to sixty seconds).
2. **Write the learning outcome** in one sentence: what the viewer can do after watching. Every scene serves it.
3. **Pick the structure** from `references/structures.md`. A Short is always `challenge-first`. For a long-form, take the structure that best fits the topic, unless the channel's latest long-form script of the same `pillar` (the highest-numbered `W/videos/*/script.json` whose idea card has that pillar) used it: then take the next best fit, so each pillar rotates through the three.
4. **Write `W/videos/<n>/script.json`** in the format in `scripts/check_script.py`: `title` (the idea card's title, within `title_max`), `type`, `structure`, `acronyms`, and `scenes` following the structure's beats.
   - The first scene states the problem within five seconds; the topic is clear by fifteen; the title's promise is answered on screen at the climax, in the middle to late scenes; the last scene bridges to the next video or challenge with one specific comment question, never a generic like or subscribe request.
   - Each scene is one picture: `kind`, `heading`, and `visual` (on-screen text, where code values and digits go) or, for a `code` scene, `code` (the demo file it shows). Change the picture at the pace `Slides and animation` sets.
   - `say` follows `Writing rules` and `Voice`: plain words, sentences under twenty words, short and medium sentences mixed, numbers as spoken words, `//` for a pause and `...` for a hesitation, CAPS on at most one stressed word per sentence, each word of the `pronunciation` list in its respelling. Delivery and tone stay in the channel's voice style, never in `say`.
   - `acronyms` lists the capitalised terms spoken as letters or names, such as `AI`, so they are not read as stress.
   - `claims` lists the `citations.json` id of every fact the scene states. A fact with no found claim is said as the video's own interpretation, shown by the demo (a `terminal` or `code` scene for a "The demo must prove" item of `research.md`), or dropped.
   - An incident story that is not real and cited says, in its first scene's `visual`, that it is a constructed scenario.
5. **Check it:** `K <channel> <n>`. It prints the estimated length.
   - Exit 3: fix each problem it names; for a length outside the target, add or cut beats of substance, never padding. Exit 2: fix the fields it names. Then run `K` again, until exit 0.
   - A jargon word the voice is likely to misread and not in `pronunciation`: list it for the owner to add to `channel.yaml`.
6. **Report on the issue:** write a scratch file of the line `YouTube: script`, then the structure, the learning outcome, the estimated length, and each scene's heading and `say`, and post it with `gh issue comment <n> --body-file <file>`. Return to the producer, checking the script against `Gate 2 checklist` and noting each item it fails.

## Output

The `YouTube: script` comment's link, the structure, the estimated length from `K`, the demo files the `code` scenes name for `build-video-demo`, and any pronunciation words proposed. A refused channel, a stage mismatch, research not passing `evidence.py`, or a length the research cannot fill is reported as blocked with the script's message.

## Constraints

- Every fact in `say` rests on a claim found in `citations.json` or on the demo; never write a fact from memory, and never edit `citations.json` (`research-video` and its `evidence.py` own it).
- RST concepts are credited to James Bach and Michael Bolton in their own words; no scene implies their endorsement.
- Never passes a gate, moves a stage, or edits labels or the body; `C` and `youtube-producer` own those (D-042). Never edits `channel.yaml` or the style guide, and never commits workspace files to aksa.

## Done when

- `K <channel> <n>` exited 0 on the final `script.json`: no banned phrase, sentence, digit, CAPS, markup, pronunciation, citation, title, or length problem.
- The first scene states the problem, a middle-to-late scene answers the title's promise, and the last scene has the next-step bridge and one comment question.
- A Short is `challenge-first` and points to its related long-form video; a long-form's structure follows the rotation of step 3.
- The `YouTube: script` comment is on the issue, with no placeholder and no em dash.
