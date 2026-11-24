---
name: write-video-script
description: Use at a video's script stage, from youtube-producer, or when the owner asks to write or rewrite a video's script. Writes videos/<n>/script.json, scenes with heading, visual or code, narration, and the citation ids each relies on, in one of the structures of references/structures.md, sized for a five to ten minute long-form or a thirty to sixty second Short, grammar-checked and passing check_script.py, and posts the script report on the issue.
---

# Write video script

## Inputs and prerequisites

- The channel and `#<n>`, a content issue at stage `script` (from `youtube-producer`), or at `demo` with gate 2 not in `approved` for a rewrite. No channel or issue: ask the owner which.
- Written below: `C` for `uv run agentic/scripts/content_issue.py`, `K` for `uv run agentic/skills/content/write-video-script/scripts/check_script.py`, and `W` for the workspace `.projects/content/yt-<channel>/`.
- The channel workspace, checked with `uv run agentic/scripts/youtube_channel.py check <channel>`; exit 2: show its message and stop. Read the style guide sections `Writing rules`, `Voice`, `Slides and animation`, `Shorts`, and `Gate 2 checklist`, and in `channel.yaml` the `banned_phrases`, `title_max`, `voice.pace`, and optional `narration_avoid_names` that `K` applies, and the `pronunciation` list.
- The research: `W/videos/<n>/research.md` and `W/videos/<n>/citations.json` from `research-video`, every claim found. Missing, or `uv run agentic/skills/content/research-video/scripts/evidence.py <channel> <n>` not exiting 0: stop and route the video back to `research-video`.
- The owner's feedback rules: `agentic/skills/content/run-youtube/references/feedback-rules.md`, its rows for step `write-video-script`.
- The idea: `W/videos/<n>/idea-card.json` when `scan-video-ideas` wrote one (its `title`, `pillar`, `claim`, `tester_question`, `proof`), else the Brief from `gh issue view <n> --json title,body`.

## Procedure

1. **Check the stage:** `C status <n> --channel <channel>` must show stage `script`, or `demo` with gate 2 not in `approved`; else stop and report the stage. Its `type` is the script's `type`: `long-form` (five to ten minutes) or `short` (thirty to sixty seconds).
2. **Write the learning outcome** in one sentence: what the viewer can do after watching. Every scene serves it.
3. **Pick the structure** from `references/structures.md`. A Short is always `challenge-first`. For a long-form, take the structure that best fits the topic, unless the channel's latest long-form script of the same `pillar` (the highest-numbered `W/videos/*/script.json` whose idea card has that pillar) used it: then take the next best fit, so each pillar rotates through the three.
4. **Write `W/videos/<n>/script.json`** in the format in `scripts/check_script.py`: `title` (the idea card's title, within `title_max`), `type`, `structure`, `acronyms`, and `scenes` following the structure's beats.
   - Follow each shared section of `references/structures.md`, read in full: "The intro" (a long-form's scene 1; a Short has none), "The cold open", "Scene rules" (reveals, comparisons, the reason before a concept, terms said first, changes shown, real-world examples, cue words, bridges, grammar, no names, never a blank screen), "Introduce the AI kit" (a long-form's `repo` card), "Take it to your agent" (the `kit` scene, its `path` slug proposed for `build-video-demo` until the demo exists; `build-video-demo` builds each file it lists), "Like, share, subscribe", and for a Short, "Short".
   - Each scene is one picture: `kind`, `heading`, and what it shows by kind, in the format in `scripts/check_script.py`: `visual` (on-screen text, where code values and digits go), `code` and optional `marks`, `left` and `right` for `split` and `compare`, the intro, repo, or kit fields. Change the picture at the pace `Slides and animation` sets.
   - `say` follows `Writing rules` and `Voice`: plain words, sentences under twenty words, short and medium sentences mixed, numbers as spoken words, `//` for a pause and `...` for a hesitation, CAPS on at most one stressed word per sentence, and the real spelling of every word: `narrate-video` respells the `pronunciation` words just before synthesis, so captions taken from the script show the real words. Delivery and tone stay in the channel's voice style, never in `say`.
   - `acronyms` lists the capitalised terms spoken as letters or names, such as `AI`, so they are not read as stress.
   - `claims` lists the `citations.json` id of every fact the scene states. A fact with no found claim is said as the video's own interpretation, shown by the demo (a `terminal` or `code` scene for a "The demo must prove" item of `research.md`), or dropped.
   - An incident story that is not real and cited says, in its cold open's `visual`, that it is a constructed scenario.
5. **Grammar pass:** before running `K`, read every on-screen line (each `heading`, `visual` line, split `label`, mark `note`, `roles`, `activity`, `stake`, compare heading and item, kit `use` line and takeaway, and the cta `heading`) and every sentence of `say` as an editor, under "Grammatical, natural English" in `references/structures.md`: full noun phrases with the articles English needs, no reduced relative such as "code an AI wrote" (write "code written by AI"), no telegraphic fragment but a short label, a capital letter starting each sentence. Fix every line that fails, and keep the count of lines checked and the lines changed, as before and after, for the report. `K` flags only a few patterns; the pass owns the rest.
6. **Check it:** `K <channel> <n>`. It prints the estimated length.
   - Exit 3: fix each problem it names (no bridge: open the scene with a sentence linking from the one before, using a transition cue; a grammar flag: rewrite the line, then repeat the grammar pass on its scene; a person named: drop the name and say the concept; a cta not last, over two sentences, or too long: move it after the bridge and cut it to two short sentences; no intro: open a long-form on an `intro` scene; an intro not saying a role or the activity: say it; a weak cold open: show the artifact and say what is shown; a code slide: make it marks in a `code` or `split` scene; a comparison: a `compare` scene; a concept with no reason: open its scene, or end the one before, with why the video needs it; a term shown early: say it first; the kit used before its repo card: add the `repo` scene; no kit beat: add the `kit` scene; a kit line repeating an earlier scene: explain how to use the file instead; no cta, or a cta not saying an action: add it or name the action; a Short's missing hook or beat: add it with a bridging sentence); for a length outside the target, add or cut beats of substance, never padding. Exit 2: fix the fields it names. Then run `K` again, until exit 0.
   - A jargon word the voice is likely to misread and not in `pronunciation`: list it for the owner to add to `channel.yaml`.
7. **Report on the issue:** write a scratch file of the line `YouTube: script`, then a line `YouTube: grammar: <lines checked> lines checked, <changed> changed` with each changed line as before and after (or `none changed`), then the structure, the learning outcome, the estimated length, the kit's files with their use lines, and each scene's heading and `say`, and post it with `gh issue comment <n> --body-file <file>`. Return to the producer, checking the script against `Gate 2 checklist` and noting each item it fails.

## Output

The `YouTube: script` comment's link, the structure, the estimated length from `K`, the demo files the `code` scenes name and the kit scene's files with their use lines for `build-video-demo`, and any pronunciation words proposed. A refused channel, a stage mismatch, research not passing `evidence.py`, or a length the research cannot fill is reported as blocked with the script's message.

## Constraints

- Every fact in `say` rests on a claim found in `citations.json` or on the demo; never write a fact from memory, and never edit `citations.json` (`research-video` and its `evidence.py` own it).
- Concepts from others, such as Rapid Software Testing's, are explained in our own words and credited in the description's References (the concept and its source, by `package-video`); narration never names their authors or any other person, and no scene implies endorsement.
- Never passes a gate, moves a stage, or edits labels or the body; `C` and `youtube-producer` own those (D-047). Never edits `channel.yaml` or the style guide, and never commits workspace files to aksa.

## Done when

- `K <channel> <n>` exited 0 on the final `script.json`.
- The grammar pass of step 5 covered every on-screen line and every narrated sentence, and the report has its `YouTube: grammar` line.
- The script meets every rule of the `references/structures.md` sections step 4 names, including those gate 2 judges rather than `K`, such as an intro creating interest, a cold open's stake and challenge, bridges that truly link, real-world examples, and a middle-to-late scene answering the title's promise; a Short is `challenge-first`, and a long-form's structure follows the rotation of step 3.
- The `YouTube: script` comment is on the issue, with no placeholder and no em dash.
