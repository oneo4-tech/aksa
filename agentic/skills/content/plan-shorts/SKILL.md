---
name: plan-shorts
description: Use at a long-form video's packaging stage, from youtube-producer, or when the owner asks to plan the Shorts of a ready or published long-form video. Plans its two Shorts, each a standalone thirty to sixty second challenge flowing from a curiosity hook in the first three seconds to the challenge, why it matters, the AI kit takeaway, and a drive to the long-form for the full breakdown, cut from the long-form or independent of it, and on the owner's yes files each as a content issue at stage idea linked to the long-form, giving a cut Short the long-form's demo and the verified citations its scenes use.
---

# Plan Shorts

## Inputs and prerequisites

- The channel and `#<n>`, a long-form content issue at stage `packaging`, `review`, or `ready`, or closed once published. No channel or issue: ask the owner which.
- Written below: `C` for `uv run agentic/scripts/content_issue.py`, `K` for `uv run agentic/skills/content/plan-shorts/scripts/cut.py`, and `W` for the workspace `.projects/content/yt-<channel>/`.
- The owner's feedback rules: `agentic/skills/content/run-youtube/references/feedback-rules.md`, its rows for step `plan-shorts`.
- The channel workspace, checked with `uv run agentic/scripts/youtube_channel.py check <channel>`; exit 2: show its message and stop. Read the style guide sections `Shorts` (format and cut rules) and `Writing rules`, the Short structure in `agentic/skills/content/write-video-script/references/structures.md`, and the long-form's `W/videos/<n>/demo.json` `link` and its demo folder's `ai-kit/AGENTS.md` (the kit every Short points to), and in `channel.yaml` `cadence.shorts_per_week` (two Shorts to each weekly long-form), `title_max`, and `banned_phrases`.
- The long-form's outputs in `W/videos/<n>/`: `script.json`, `research.md`, `citations.json`, and `demo.json`. Missing: stop and report the stage that writes it.

## Procedure

1. **Check the video:** `C status <n> --channel <channel>` must show `type` `long-form` and a stage above; else stop and report it. `gh issue view <n> --comments` already showing a `YouTube: shorts` comment: show it and stop, unless the owner asks for more Shorts.
2. **Find the moments:** from `script.json` and `research.md`, pick the ideas that work alone in under a minute: a beat with one problem shown on screen (a cut), or a claim of the research the long-form did not show (independent). Each Short has one idea, and the two differ.
3. **Plan two Shorts** (`cadence.shorts_per_week`), each under `Shorts` and the Short structure, as a brief:
   - `title`: challenge style, at most `title_max` characters, no banned phrase.
   - `kind`: `cut`, reusing the long-form's scenes, demo, and citations, or `independent`, a new script on the same topic.
   - `hook`: two to eight words that make the viewer curious (a surprise or a question, such as "This test has never failed"), shown large on the `split` of the code under test and its tests and said as the first sentence, within three seconds; never an abrupt start or a slogan. A Short has no intro scene, unlike the long-form; its hook is the opening.
   - `beats`: the Short structure's flow, each with what is on screen and the one bridging sentence into the next (every scene after the first opens on a transition cue, such as "So why does this matter?"), the whole thirty to sixty seconds, under "Scene rules" in the structures file: the challenge (the bug's line marked in the code, never a slide of code), why it matters (the stake, with a reason cue, never a bare title slide), the takeaway, and the drive to the long-form (the last scene names the full video or breakdown and what more it shows). No term on screen before it is said, and the reason before any concept. The takeaway ("Take it to your agent" in the structures file) is a `kit` scene replaying the long-form's GitHub card with one or two of its kit files, each with how the viewer uses it, and the takeaways, saying the kit link is below; its card is the kit's introduction, so a Short needs no `repo` card; an independent Short whose idea the long-form's kit does not cover names the file or rule to add to it. A closing `cta` naming subscribe is optional, the last scene, at most about four seconds. Every on-screen line and sentence in the brief is grammatical, natural English (no "a test an AI wrote": write "a test written by AI"), and no beat names a person.
   - `source`: for a cut, the long-form scene numbers; for an independent Short, the citation ids it relies on.
   - `related`: the description's `Full video:` line links the long-form and its `AI kit:` line the kit (`package-video` adds both), and the owner sets the long-form as the Short's related video in YouTube Studio.
4. **Ask the owner:** show both briefs and ask for an explicit yes to file them; changes asked: revise and ask again. No yes: report the plan waiting and stop.
5. **File each Short:** write its brief to a scratch file and run `C new <channel> --type short --title "<title>" --brief-file <file>`, adding `--parent <n>` for a cut (a sub-issue of the long-form) or `--related <n>` for an independent Short. Each starts at stage `idea` with its folder `W/videos/<short>/`; `youtube-producer` takes it through its stages like any video.
   - Exit 3, a link refused: `#<n>` is not a long-form of this channel; report it. Exit 1: report the error; a Short filed before a failed sub-issue link is named in the message, so link it by hand or ask the owner.
   - **A cut Short reuses the long-form's demo and citations:** right after its `C new --parent <n>`, run `K <channel> <short> --from <n> --scenes <source>`, the brief's long-form scene numbers, such as `2,3`. It writes `W/videos/<short>/demo.json` (the long-form's, so the Short shows and links the same demo), `citations.json` (the long-form's verified claims those scenes state), and the recording of each cut terminal scene, the long-form's `demo-K.mp4` renumbered `demo-1.mp4`, `demo-2.mp4`, and so on in the `--scenes` order (or the long-form's single `demo.mp4` when it has no `demo-K.mp4`), with no new research. The Short's script keeps its terminal scenes in that order, as `render-video` plays `demo-K.mp4` for its K-th terminal scene. Exit 3: report its message; a long-form output or recording missing, or citations unverified, goes back to the stage that writes it, and scenes that state no claim make the Short independent or need other scenes, the owner's choice. Exit 2: the scene numbers are not in the long-form's `script.json`; fix them from the brief.
6. **Report on the long-form issue:** write a scratch file of the line `YouTube: shorts`, then each Short's number, title, kind, and hook, and post it with `gh issue comment <n> --body-file <file>`. Return to the producer with the Shorts' numbers.

## Output

The `YouTube: shorts` comment's link and each Short's issue number, title, and kind, and for a cut Short its `demo.json` and `citations.json`; or the plan waiting for the owner's yes. A wrong type or stage, a missing output, or a failed `C new` or `K` is reported as blocked with its message.

## Constraints

- Files issues only on the owner's explicit yes in this session, and only through `C new`; never edits labels or bodies, passes gates, or moves stages (D-042).
- Plans; never scripts, records, or packages a Short: each Short's own stages do that, and its script is always the `challenge-first` Short structure. The one output it writes in a Short's folder is a cut Short's demo and citations, only through `K`.
- Never edits the long-form's outputs, `channel.yaml`, or the style guide. Publishes and sets nothing on YouTube; the related-video link in Studio is the owner's.

## Done when

- Two Short briefs, each one standalone idea of thirty to sixty seconds with a curiosity hook said within three seconds over a `split` of the code and its tests, then the challenge, why it matters, a `kit` beat explaining its files and takeaways, and a drive to the long-form's full breakdown, a bridging sentence opening each beat after the first, every line grammatical, no person named in narration, an optional closing cta of about four seconds, and a title within `title_max`, were shown to the owner.
- On the owner's yes, each Short is a content issue at stage `idea` from `C new`, with `--parent <n>` or `--related <n>`.
- Each cut Short has `W/videos/<short>/demo.json` and `citations.json` from `K`.
- The `YouTube: shorts` comment is on the long-form issue, with no placeholder and no em dash.
