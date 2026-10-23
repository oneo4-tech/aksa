---
name: render-video
description: Use at a video's editing stage, from youtube-producer, or when the owner asks to render, re-render, or assemble a video. Renders each scene of videos/<n>/script.json with its narration into a clip (HTML Web Animations timed from whisper word timestamps, terminal scenes from the VHS recording), then assembles videos/<n>/render/final.mp4 (1920x1080 long-form with final.srt, or 1080x1920 Short with burned word-highlight captions) with the music bed and two-pass loudness to the channel's target.
---

# Render video

## Inputs and prerequisites

- The channel and `#<n>`, a content issue at stage `editing` (from `youtube-producer`). No channel or issue: ask the owner which.
- Written below: `C` for `uv run agentic/scripts/content_issue.py`, `R` for `uv run agentic/skills/content/render-video/scripts/render.py`, `A` for `uv run agentic/skills/content/render-video/scripts/assemble.py`, and `W` for the workspace `.projects/content/yt-<channel>/`.
- The channel workspace, checked with `uv run agentic/scripts/youtube_channel.py check <channel>`; exit 2: show its message and stop. Read the style guide sections `Visual style` (theme, fonts, contrast), `Slides and animation` (focus lines, fades, visual pace), `Screen capture` (terminal recordings), `Audio` (loudness, music bed), and `Captions` (long-form SRT, Short word highlight), and in `channel.yaml` the `name`, `palette`, `loudness`, and `music_db` that `R` and `A` apply.
- The script and narration: `W/videos/<n>/script.json` from `write-video-script`, and `W/videos/<n>/narration/NN.wav` for every scene with `narration/report.json` showing `passed: true`, from `narrate-video`. Missing or not passed: stop and route the video back to `narrate-video`.
- The demo, when the script has `code` or `terminal` scenes: `W/videos/<n>/demo.json` (the demo's folder, whose files `code` scenes show) and the VHS recording `W/videos/<n>/demo.mp4`, from `build-video-demo`. `demo.json` missing for a `code` scene: route back to `build-video-demo`. `demo.mp4` missing while `terminal` scenes exist: ask the owner whether to record it with `build-video-demo` or draw the terminal scenes from their `visual`; no answer: report blocked.
- The channel's music bed `W/music/bed.mp3`, supplied once by the owner (the `Audio` bed, such as a Lyria ambient clip); it loops under every video. Missing: ask the owner for it and report blocked.
- Google Chrome, `ffmpeg`, `ffprobe`, `whisper-cli` with its `base.en` model, and the Space Grotesk and Fira Code font files, as the README's Setup lists; missing: ask the owner to install them and report blocked. Fonts load only from those local files, never from the network.

## Procedure

1. **Check the stage:** `C status <n> --channel <channel>` must show stage `editing`; else stop and report the stage.
2. **Render the scenes:** `R <channel> <n>`. Per scene it times each on-screen item from the narration's whisper word timestamps, then either draws the scene from its kind's template in `references/` (`title.html`, `points.html`, `code.html`, `terminal.html`, with the shared `references/scene.css` and `references/scene.js`), stepping its Web Animations frame by frame in Chrome and encoding the frames, or, for a `terminal` scene when `demo.mp4` exists, cuts the next stretch of the recording. It writes `W/videos/<n>/render/scenes/NN.mp4` and prints and writes `render/scenes.json`.
   - Exit 0: every scene rendered. Exit 2: fix or route back the input it names (script to `write-video-script`, narration to `narrate-video`, demo files to `build-video-demo`). Exit 1: report the tool error; a font or Chrome error names the README Setup step.
3. **Check the clips** against `Visual style`, `Slides and animation`, and `Screen capture`: open each `render/scenes/NN.mp4` and check the text is legible and inside the frame, each point or focus line appears as the narration names it, the picture changes at the pace `Slides and animation` sets, and each terminal clip shows the steps its scene's narration describes.
   - A scene whose picture or wording is wrong: the fix goes to `write-video-script` (its `visual`, `code`, or scene split), then narrate and render again. A template or timing fault: propose it to the producer as an improvement for the retrospective; never edit the templates in a video run.
4. **Assemble:** `A <channel> <n>`. It joins the clips in order with each narration at its scene's `lead`, loops the music bed under the voice at `music_db`, normalises loudness in two passes to `loudness.lufs` and `loudness.true_peak`, and captions from the script's `say` words timed by whisper: a long-form gets `render/final.srt`, a Short burned captions of three words with the word being said highlighted, drawn from `references/captions.html`. It writes `W/videos/<n>/render/final.mp4` and prints a report with the mix's measured loudness.
   - Exit 0: assembled. Exit 2: fix or route back the input it names (scenes to step 2, narration to `narrate-video`, the music bed to the owner). Exit 1: report the tool error.
5. **Check the video** against `Audio` and `Captions`: play `render/final.mp4` and check the voice sits clearly over the bed, no clip or scene cut is audible, and the captions (the Short's burned words, or `final.srt` loaded beside the long-form) show the script's words in time with the voice. Wrong caption wording goes to `write-video-script`; a timing or level fault is proposed to the producer as in step 3.
6. **Report on the issue:** write a scratch file of the line `YouTube: edit`, then each scene's number, kind, source (`html` or `demo`), and seconds from `scenes.json`, the total length, the final file and its captions from `A`'s report, and any scene sent back, and post it with `gh issue comment <n> --body-file <file>`. Return to the producer with `render/final.mp4` (and `render/final.srt` for a long-form).

## Output

The `YouTube: edit` comment's link, `render/final.mp4` with its size, length, and captions (`render/final.srt` or burned), and per scene its kind, source, and seconds. A refused channel, a stage mismatch, a missing or failed narration, a missing demo file or recording without the owner's answer, a missing music bed, or a missing tool or font is reported as blocked with the script's message.

## Constraints

- Every picture and caption comes from the script, the demo, and the channel's palette and name; never invent on-screen facts or text the script lacks. Captions show the script's real words, never the transcript's or the pronunciation respellings.
- Never edits `script.json`, `channel.yaml`, the style guide, the narration, the demo, or the music bed; changes go to the skill or person that owns each file. The templates, `scripts/render.py`, and `scripts/assemble.py` are components: changes to them are new work requests (D-038), never edits during a video run.
- Generated media stays out of git (the workspace ignores `*.mp4`, `*.mp3`); never commits workspace files to aksa.
- Never passes a gate, moves a stage, or edits labels or the body; `C` and `youtube-producer` own those (D-042).

## Done when

- `R <channel> <n>` exited 0: `W/videos/<n>/render/scenes/NN.mp4` exists for every scene, and `render/scenes.json` lists each with its source and seconds.
- `A <channel> <n>` exited 0: `W/videos/<n>/render/final.mp4` exists, with `render/final.srt` for a long-form.
- The clips were checked against `Visual style`, `Slides and animation`, and `Screen capture`, the final video against `Audio` and `Captions`, and every scene sent back is named in the report.
- The `YouTube: edit` comment is on the issue, with no placeholder and no em dash.
