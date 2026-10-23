---
name: design-thumbnail
description: Use at a video's packaging stage, from youtube-producer, or when the owner asks to design or redo a video's thumbnail. Writes the thumbnail text (at most four words, matching the title and the video's claim) and a text-free art subject, generates the art once with Gemini 3.1 Flash Image in the channel's art style (paid, about USD 0.07, after the owner's yes), and composes it into the issue's rotating layout (split, code-circle, face-off) as videos/<n>/thumbnail.png or .jpg at 3840x2160 under 2 MB.
---

# Design thumbnail

## Inputs and prerequisites

- The channel and `#<n>`, a content issue at stage `packaging` (from `youtube-producer`). No channel or issue: ask the owner which.
- Written below: `C` for `uv run agentic/scripts/content_issue.py`, `T` for `uv run --env-file .env agentic/skills/content/design-thumbnail/scripts/thumbnail.py`, and `W` for the workspace `.projects/content/yt-<channel>/`.
- The channel workspace, checked with `uv run agentic/scripts/youtube_channel.py check <channel>`; exit 2: show its message and stop. Read the style guide sections `Thumbnails` (text, art, and layout rules) and `Visual style` (palette and contrast), and in `channel.yaml` the `palette` and `thumbnail.art_style` that `T` applies.
- The script: `W/videos/<n>/script.json` from `write-video-script`, for its `title` and the claim its scenes prove. Missing: stop and route the video back to `write-video-script`.
- `GEMINI_API_KEY` in `.env` when new art is needed; missing: say so and stop, never print it. Google Chrome and the Space Grotesk and Fira Code font files, as the README's Setup lists; missing: ask the owner to install them and report blocked.

## Procedure

1. **Check the stage:** `C status <n> --channel <channel>` must show stage `packaging`; else stop and report the stage.
2. **Write the text:** at most four words on one line, saying the video's claim in the title's terms without repeating the title word for word, under the `Thumbnails` rules. `T` shows it exactly as given, so write the case and punctuation wanted. The `code-circle` layout shows it as one line of code.
3. **Write the art subject:** one concrete scene or object standing for the claim, such as "a smug red bug hiding behind a glowing green checkmark", naming no words, signs, screens, or labels. `T` adds `thumbnail.art_style`, the palette background, and the rule that the art has no text, letters, or numbers.
4. **Confirm the cost:** new art is one Gemini 3.1 Flash Image call, about USD 0.07 (the model has no free tier). Show the text, subject, and layout (`T` picks `split`, `code-circle`, or `face-off` by issue number, so neighbouring videos differ; the owner may name another with `--layout`), and ask the owner's yes. No yes: report blocked. Art already made from the same subject is reused free, with no need to ask.
5. **Compose:** `T <channel> <n> --text "<text>" --subject "<subject>"`, adding `--layout <layout>` only when the owner named one. It generates or reuses the art in `W/videos/<n>/thumbnail/`, composes the layout from `references/` (`split.html`, `code-circle.html`, or `face-off.html`, with `references/thumbnail.css` and `references/fit.js`), and writes `W/videos/<n>/thumbnail.png` or `thumbnail.jpg`, printing a report.
   - Exit 0: written. Exit 2: fix the text or subject it names. Exit 3: the cached art came from another subject; keep that subject, or, on the owner's yes to the cost, rerun with `--new-art`. Exit 1: report the error; a Gemini error may name a key or quota problem, a font or Chrome error names the README Setup step.
6. **Check the thumbnail** against `Thumbnails` and `Visual style`: open the file and look at it at full size and at about 320 pixels wide. The text is the agreed text and legible small; the art shows the subject; it has no letters, numbers, or fake writing. Art with writing or a wrong subject: write a new subject, and with the owner's yes to the cost, rerun with `--new-art`. A text change only: rerun without `--new-art` (free). A layout fault: propose it to the producer as an improvement for the retrospective; never edit the templates in a video run.
7. **Report on the issue:** write a scratch file of the line `YouTube: thumbnail`, then the text, subject, layout, art (`generated` or `cached`), file, format, and size from `T`'s report, and post it with `gh issue comment <n> --body-file <file>`. Return to the producer with the thumbnail's path.

## Output

The `YouTube: thumbnail` comment's link, the thumbnail's path, layout, format, and size, and whether the art was generated (paid) or cached. A refused channel, a stage mismatch, a missing script, key, font, or Chrome, no yes to the cost, or a Gemini error is reported as blocked with the script's message.

## Constraints

- All thumbnail text comes from the template's text slot; art is never asked for text, and art showing writing is replaced, never kept.
- Pays for art only after the owner's yes in this session; never reruns `--new-art` to try variations unasked.
- Never edits `script.json`, `channel.yaml`, or the style guide; title changes go to `write-video-script` or `package-video`, style changes to the owner. The templates and `scripts/thumbnail.py` are components: changes to them are new work requests (D-038).
- Never prints, logs, or posts the API key. Generated images stay out of git (the workspace ignores `*.png`, `*.jpg`); never commits workspace files to aksa.
- Never passes a gate, moves a stage, or edits labels or the body; `C` and `youtube-producer` own those (D-042).

## Done when

- `T <channel> <n>` exited 0: `W/videos/<n>/thumbnail.png` or `thumbnail.jpg` exists, 3840x2160 and at most 2 MB, as its report shows.
- The text is at most four words matching the title and claim, and the thumbnail was checked against `Thumbnails` and `Visual style` with no writing in the art.
- The `YouTube: thumbnail` comment is on the issue, with no placeholder and no em dash.
