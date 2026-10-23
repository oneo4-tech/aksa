---
name: render-video
description: Use at a video's editing stage, from youtube-producer, or when the owner asks to render or re-render a video's scenes. Renders each scene of videos/<n>/script.json with its narration into a silent clip videos/<n>/render/scenes/NN.mp4 (30 fps, 1920x1080 long-form, 1080x1920 Short), drawn scenes as HTML Web Animations timed from whisper word timestamps and terminal scenes from the VHS recording, listed in render/scenes.json.
---

# Render video

## Inputs and prerequisites

- The channel and `#<n>`, a content issue at stage `editing` (from `youtube-producer`). No channel or issue: ask the owner which.
- Written below: `C` for `uv run agentic/scripts/content_issue.py`, `R` for `uv run agentic/skills/content/render-video/scripts/render.py`, and `W` for the workspace `.projects/content/yt-<channel>/`.
- The channel workspace, checked with `uv run agentic/scripts/youtube_channel.py check <channel>`; exit 2: show its message and stop. Read the style guide sections `Visual style` (theme, fonts, contrast), `Slides and animation` (focus lines, fades, visual pace), and `Screen capture` (terminal recordings), and in `channel.yaml` the `name` and `palette` that `R` applies.
- The script and narration: `W/videos/<n>/script.json` from `write-video-script`, and `W/videos/<n>/narration/NN.wav` for every scene with `narration/report.json` showing `passed: true`, from `narrate-video`. Missing or not passed: stop and route the video back to `narrate-video`.
- The demo, when the script has `code` or `terminal` scenes: `W/videos/<n>/demo.json` (the demo's folder, whose files `code` scenes show) and the VHS recording `W/videos/<n>/demo.mp4`, from `build-video-demo`. `demo.json` missing for a `code` scene: route back to `build-video-demo`. `demo.mp4` missing while `terminal` scenes exist: ask the owner whether to record it with `build-video-demo` or draw the terminal scenes from their `visual`; no answer: report blocked.
- Google Chrome, `ffmpeg`, `ffprobe`, `whisper-cli` with its `base.en` model, and the Space Grotesk and Fira Code font files, as the README's Setup lists; missing: ask the owner to install them and report blocked. Fonts load only from those local files, never from the network.

## Procedure

1. **Check the stage:** `C status <n> --channel <channel>` must show stage `editing`; else stop and report the stage.
2. **Render the scenes:** `R <channel> <n>`. Per scene it times each on-screen item from the narration's whisper word timestamps, then either draws the scene from its kind's template in `references/` (`title.html`, `points.html`, `code.html`, `terminal.html`, with the shared `references/scene.css` and `references/scene.js`), stepping its Web Animations frame by frame in Chrome and encoding the frames, or, for a `terminal` scene when `demo.mp4` exists, cuts the next stretch of the recording. It writes `W/videos/<n>/render/scenes/NN.mp4` and prints and writes `render/scenes.json`.
   - Exit 0: every scene rendered. Exit 2: fix or route back the input it names (script to `write-video-script`, narration to `narrate-video`, demo files to `build-video-demo`). Exit 1: report the tool error; a font or Chrome error names the README Setup step.
3. **Check the clips** against `Visual style`, `Slides and animation`, and `Screen capture`: open each `render/scenes/NN.mp4` and check the text is legible and inside the frame, each point or focus line appears as the narration names it, the picture changes at the pace `Slides and animation` sets, and each terminal clip shows the steps its scene's narration describes.
   - A scene whose picture or wording is wrong: the fix goes to `write-video-script` (its `visual`, `code`, or scene split), then narrate and render again. A template or timing fault: propose it to the producer as an improvement for the retrospective; never edit the templates in a video run.
4. **Report on the issue:** write a scratch file of the line `YouTube: scenes`, then each scene's number, kind, source (`html` or `demo`), and seconds from `scenes.json`, the total length, and any scene sent back, and post it with `gh issue comment <n> --body-file <file>`. Return to the producer with `render/scenes.json`.

## Output

The `YouTube: scenes` comment's link, the `render/scenes/` folder, and per scene its kind, source, and seconds. A refused channel, a stage mismatch, a missing or failed narration, a missing demo file or recording without the owner's answer, or a missing tool or font is reported as blocked with the script's message.

## Constraints

- Every picture comes from the script, the demo, and the channel's palette and name; never invent on-screen facts or text the script lacks.
- Never edits `script.json`, `channel.yaml`, the style guide, the narration, or the demo; changes go to the skill that owns each file. The templates and `scripts/render.py` are components: changes to them are new work requests (D-038), never edits during a video run.
- Generated media stays out of git (the workspace ignores `*.mp4`); never commits workspace files to aksa.
- Never passes a gate, moves a stage, or edits labels or the body; `C` and `youtube-producer` own those (D-042).

## Done when

- `R <channel> <n>` exited 0: `W/videos/<n>/render/scenes/NN.mp4` exists for every scene, and `render/scenes.json` lists each with its source and seconds.
- Each clip was checked against `Visual style`, `Slides and animation`, and `Screen capture`, and every scene sent back is named in the report.
- The `YouTube: scenes` comment is on the issue, with no placeholder and no em dash.
