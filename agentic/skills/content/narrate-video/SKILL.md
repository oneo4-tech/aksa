---
name: narrate-video
description: Use at a video's recording stage, from youtube-producer, or when the owner asks to narrate or re-narrate a video. Renders each scene of videos/<n>/script.json with Gemini 3.8 Flash TTS in the channel's voice, style, pace, and pronunciation into videos/<n>/narration/NN.wav, and checks each file's whisper transcript against the script for spoken markup, writing narration/report.json.
---

# Narrate video

## Inputs and prerequisites

- The channel and `#<n>`, a content issue at stage `recording` (from `youtube-producer`). No channel or issue: ask the owner which.
- Written below: `C` for `uv run agentic/scripts/content_issue.py`, `N` for `uv run --env-file .env agentic/skills/content/narrate-video/scripts/narrate.py`, and `W` for the workspace `.projects/content/yt-<channel>/`.
- The channel workspace, checked with `uv run agentic/scripts/youtube_channel.py check <channel>`; exit 2: show its message and stop. Read the style guide sections `Voice` (delivery, pauses, pronunciation) and `Audio` (what the narration feeds), and in `channel.yaml` the `voice.id`, `voice.style`, `voice.pace`, and `pronunciation` that `N` applies.
- The script: `W/videos/<n>/script.json` from `write-video-script`, passing its check. Missing: stop and route the video back to `write-video-script`.
- `GEMINI_API_KEY` in `.env`; missing: say so and stop, never print it. `ffmpeg`, `whisper-cli`, and the whisper `base.en` model, as the README's Setup lists; missing: ask the owner to install them and report blocked.

## Procedure

1. **Check the stage:** `C status <n> --channel <channel>` must show stage `recording`; else stop and report the stage.
2. **Narrate:** `N <channel> <n>`. Per scene, in order, it respells the `pronunciation` words of `say` (the script keeps the real words, so captions show them), sends the text with `//` and `...` kept and the style only in `speech_metadata.style`, applies `voice.pace` with ffmpeg, writes `W/videos/<n>/narration/NN.wav`, and checks its whisper transcript. It writes and prints `narration/report.json`.
   - Exit 0: every scene is clean.
   - Exit 3, a scene refused (markup heard, the style heard, or a word match under the threshold): synthesis varies run to run, so run `N` once more. Still refused: read the scene's transcript in the report; a misread word becomes a proposed `pronunciation` entry for the owner, a sentence the voice cannot say cleanly goes back to `write-video-script`. Report blocked.
   - Exit 1: report the error. A Gemini error naming the voice may mean the designed voice expired (1-year TTL); the owner re-creates it and updates `voice.id`. Exit 2: fix the input it names.
3. **Report on the issue:** write a scratch file of the line `YouTube: narration`, then the voice id, the pace, each scene's file and match from the report, and any proposed `pronunciation` entries, and post it with `gh issue comment <n> --body-file <file>`. Return to the producer.

## Output

The `YouTube: narration` comment's link, the narration folder, each scene's match, and any proposed pronunciation entries. A refused channel, a stage mismatch, a missing script, key, or tool, a Gemini error, or a scene still refused after one rerun is reported as blocked with the script's message and the scene's transcript.

## Constraints

- Style and delivery go only in `voice.style`, sent as `speech_metadata.style`; never add them to `say` or the text sent, since Gemini speaks style text aloud.
- Never edits `script.json`, `channel.yaml`, or the style guide: script changes go to `write-video-script`, pronunciation and voice changes to the owner.
- Never prints, logs, or posts the API key. Generated audio stays out of git; never commits workspace files to aksa.
- Never passes a gate, moves a stage, or edits labels or the body; `C` and `youtube-producer` own those (D-042).

## Done when

- `N <channel> <n>` exited 0: `W/videos/<n>/narration/NN.wav` exists for every scene and `narration/report.json` shows `passed: true`.
- The `YouTube: narration` comment is on the issue, with no placeholder and no em dash.
