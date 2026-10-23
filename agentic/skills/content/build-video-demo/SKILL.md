---
name: build-video-demo
description: Use at a video's demo stage, from youtube-producer, or when the owner asks to build or rebuild a video's demo. Builds the smallest runnable demo that proves the script's claim, with passing tests and a VHS tape recording it, in the folder <n>-<slug>/ of the channel's public demo repository clone, and returns the folder's description link.
---

# Build video demo

## Inputs and prerequisites

- The channel and `#<n>`, a content issue at stage `demo` (from `youtube-producer`), with gate 2 not in `approved`. No channel or issue: ask the owner which.
- Written below: `C` for `uv run agentic/scripts/content_issue.py`, `S` for `uv run agentic/skills/content/build-video-demo/scripts/scaffold.py`, and `W` for the workspace `.projects/content/yt-<channel>/`.
- The channel workspace, checked with `uv run agentic/scripts/youtube_channel.py check <channel>`; exit 2: show its message and stop. Read the style guide sections `Screen capture` (terminal demo rules) and `Gate 2 checklist` (what the owner checks of the demo plan), and in `channel.yaml` the `demos` repository and clone folder that `S` uses.
- The script and research: `W/videos/<n>/script.json` from `write-video-script` (its `code` scenes name the demo files, its `terminal` scenes the commands shown), the "The demo must prove" list of `W/videos/<n>/research.md`, and `W/videos/<n>/citations.json`, every claim verified by `research-video`, which the README lists. Missing: stop and route the video back to `write-video-script` or `research-video`.
- `uv` to run the demo's tests, and `vhs` to record the tape; without `vhs`, ask the owner to install it and report the recording blocked.

## Procedure

1. **Check the stage:** `C status <n> --channel <channel>` must show stage `demo` with gate 2 not in `approved`; else stop and report the stage.
2. **State the claim** in one sentence: what the demo proves, from "The demo must prove" and the script's climax scene. Pick a slug of two or three lowercase hyphenated words naming it.
3. **Scaffold:** `S <channel> <n> --slug <slug> --proves "<the sentence>"`. It creates `<n>-<slug>/` in the clone with `README.md`, `demo/`, `tests/`, `demo.tape` (from `references/demo.tape`, with the README from `references/readme-template.md`), and prints the description link. The README's Video section holds the line `- Video: not published yet`, which `package-video` fills with the published video's link, the channel's link, and the folder's link; its Sources section lists each claim with its quoted line and text-fragment link. It never links the content issue: the aksa tracker is private.
   - Exit 3, folder exists: a rebuild; continue that folder. Exit 3, clone missing or repository missing on GitHub: ask the owner (see Constraints), then run `S` again; no yes: report blocked. Exit 3, citations not verified: route the video back to `research-video`.
   - Exit 2: fix the input it names.
4. **Build the smallest demo** that proves the claim, test first: the files each `code` scene names go in `demo/`, at those paths, and nothing the video does not show. A claim that a kind of test misses a defect shows the weak test and a step that breaks the code, then restores it, as the prototype's `mutate.sh` did; these stay in `demo/`. `tests/` holds the tests that prove the claim, passing on the correct code, each with one reason to fail. Standard library and pytest only, unless the claim is about another tool.
5. **Run the tests** from the folder: `uv run --with pytest python -m pytest -q tests`; fix the demo until it exits 0. Run each `demo/` step the tape types and check its output is what the script's `terminal` scenes say.
6. **Write the tape:** in `demo.tape`, keep the settings and the hidden setup line, and replace the `Show` part with the `terminal` scenes' commands in order, each followed by a `Sleep` long enough to read its output, as `Screen capture` sets. Record it from the folder: `vhs demo.tape`, then move `demo.mp4` to `W/videos/<n>/demo.mp4`; watch it and fix any step that shows an error the script does not expect.
7. **Fill the README:** adapt "How to run" if the demo needs more than the command above, and add each `demo/` step a viewer runs. No `{{` placeholder is left; keep the `- Video:` line and the Sources section as `S` wrote them, for `package-video` to fill at publish.
8. **Commit in the clone,** never in aksa: `git -C <clone> add <n>-<slug>` and `git -C <clone> commit -m "feat(<n>-<slug>): add the demo"`. Ask the owner for an explicit yes to push; on yes, `git -C <clone> push`; else leave it local and report the push waiting.
9. **Record the link:** write `W/videos/<n>/demo.json` with `folder` (`<n>-<slug>`), `link` (the description link from `S`), `proves` (the sentence), and `pushed` (`true` or `false`); `package-video` puts `link` in the description.
10. **Report on the issue:** write a scratch file of the line `YouTube: demo`, then the claim, the link, the test result line, and whether it is pushed, and post it with `gh issue comment <n> --body-file <file>`. Return to the producer, checking the demo against `Gate 2 checklist` and noting each item it fails.

## Output

The `YouTube: demo` comment's link, the description link, the test result line, the recording path, and whether the folder is pushed. A refused channel, a stage mismatch, a missing script, a missing clone or repository, missing `vhs`, or tests that cannot pass are reported as blocked with the command's message.

## Constraints

- Never create the public demo repository, or push to it, without the owner's explicit yes in this session. Creating it is a one-time owner-approved step: on that yes, `gh repo create <demos.repo> --public --license mit`, then `gh repo clone <demos.repo> .projects/content/<demos.path>`.
- The folder is public: no secrets, `.env` values, absolute paths, links to the private aksa tracker, channel workspace text beyond the README, or code copied from a source whose licence does not allow MIT redistribution.
- Generated media stays out of git: the folder's `.gitignore` ignores it, and the recording lives in the channel workspace.
- Never passes a gate, moves a stage, or edits labels or the body; `C` and `youtube-producer` own those (D-042). Never edits `script.json`, `citations.json`, `channel.yaml`, or the style guide; a script that the demo cannot back goes back to `write-video-script`. Never commits workspace or demo files to aksa.

## Done when

- `uv run --with pytest python -m pytest -q tests` exits 0 in the folder, and the tape's steps match the script's `terminal` scenes.
- The folder has `README.md` with no placeholder, the `- Video:` line, the channel link, the Sources section, and no aksa issue link, `demo/`, `tests/`, and `demo.tape` with the template's settings; the recording is at `W/videos/<n>/demo.mp4`, or reported blocked.
- `W/videos/<n>/demo.json` holds the description link, and nothing was pushed or created without the owner's yes.
- The `YouTube: demo` comment is on the issue, with no placeholder and no em dash.
