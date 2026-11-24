---
name: design-thumbnail
description: Use at a video's packaging stage, from youtube-producer, or when the owner asks to design or redo a video's thumbnail. Picks the layout (spot-the-bug for a Spot the Bug video, face-off for a comparison, else split or big-subject by issue number), writes 2 to 4 words that challenge or question the viewer and show AI when the video is about AI, composes 3 free variants side by side (text or marker) and, only on the owner's yes, 1 to 3 Gemini 3.1 Flash Image art candidates (about USD 0.07 each), each at 3840x2160 under 2 MB, checks them at 320 and 168 px against a 14-point checklist, and writes the owner's pick as videos/<n>/thumbnail.png or .jpg.
---

# Design thumbnail

## Inputs and prerequisites

- The owner's feedback rules: `agentic/skills/content/run-youtube/references/feedback-rules.md`, its rows for step `design-thumbnail`.
- The channel and `#<n>`, a content issue at stage `packaging` (from `youtube-producer`). No channel or issue: ask the owner which.
- Written below: `C` for `uv run agentic/scripts/content_issue.py`, `T` for `uv run --env-file .env agentic/skills/content/design-thumbnail/scripts/thumbnail.py`, and `W` for the workspace `.projects/content/yt-<channel>/`.
- The channel workspace, checked with `uv run agentic/scripts/youtube_channel.py check <channel>`; exit 2: show its message and stop. Read the style guide sections `Thumbnails` and `Visual style`, and in `channel.yaml` the `palette`, `thumbnail.art_style`, and `thumbnail.field` (the two colours of the background gradient; indigo when absent) that `T` applies.
- The script: `W/videos/<n>/script.json` from `write-video-script`, for its `title`, its claim, and its code scenes; and `W/videos/<n>/demo.json` for the demo folder in the channel's demos repository. Missing script: stop and route the video back to `write-video-script`.
- `GEMINI_API_KEY` in `.env` when new art is needed; missing: say so and stop, never print it. Google Chrome, ffmpeg, and the Space Grotesk and Fira Code font files, as the README's Setup lists; missing: ask the owner to install them and report blocked.

## Procedure

1. **Check the stage:** `C status <n> --channel <channel>` must show stage `packaging`; else stop and report the stage.
2. **Choose the layout** (`--layout`; the templates are `references/<layout>.html` with `references/thumbnail.css` and `references/fit.js`):
   - `spot-the-bug`, the channel's signature, for a Spot the Bug video or any video whose claim is one line of code: the demo's code in a panel under a chip naming who wrote it (`--chip`, default "Written by AI"; give the true author, or `--chip ""` to hide it, when AI did not write it), the buggy line marked, the challenge text at the right, art optional (a character with a face below the text).
   - `face-off` only when the video compares two things and each can fill its half: two characters, one text half over each.
   - Else the default: `split` (subject right, text left) or `big-subject` (one close-up character left, text right), by issue number, so neighbouring videos differ. The owner may name any layout.
3. **Write the text**, by these rules, which `T` enforces (exit 2 names the broken one):
   - **Challenge or question:** 2 to 4 words that put a challenge or a question to the viewer, a curiosity gap the title does not close, never the title word for word (H4): it ends with "?" or uses a challenge verb (spot, find, catch, guess, fix, break, beat, prove), such as "Can you spot it?", "AI wrote this. Bug?", "Will this fail?", "Which test lies?". A statement such as "Never fails" is refused.
   - **AI cue:** when the script's `title` names AI, the thumbnail shows AI: in the text ("AI wrote this. Bug?"), in the `spot-the-bug` chip, or as an AI character in the art subject ("a clay robot"). Only AI in the text survives at 168 px, so prefer it in at least one variant.
   - **Accurate:** the question matches what the video answers (F6).
   - A word a line in warm white, the last word the key word in cyan; order the words so the key word is last. `T` never shrinks the text below a cap height of 15% of the frame and refuses text that does not fit (exit 2), so keep words short: about 7 letters in `split` and `big-subject`, 6 in `spot-the-bug`, and one half of about 7 letters a side in `face-off`. `T` shows the text exactly as given.
4. **Write the art subject** (optional only for `spot-the-bug`): one character as a scene, with a readable facial expression (F1, F5; give an object a face), the story's payoff in it and large, such as "a smug green clay checkmark character with half-closed eyes and a sly grin, hiding a small red clay ladybird bug behind its back". For `face-off`, the two characters facing each other. Name no words, signs, screens, or labels. `T` adds `thumbnail.art_style`, the placement and size for the layout, rim light, the field gradient named in words from `thumbnail.field` (such as "dark grey"; never a hex code, which art may draw as text) with negative space for the text, and a positive exclusion ("Plain, unmarked surfaces; blank background"), following Gemini's template for art with text overlaid later (F15 to F17).
5. **Write the code** (`spot-the-bug` only): 6 to 10 real lines from the demo file the video shows, each at most 30 characters, reflowed without changing what the code does, the buggy line among them; write them to `W/videos/<n>/thumbnail/code.txt` and note the buggy line's number for `--mark`.
6. **Mark the line** (`spot-the-bug` only, `--marker`): `highlight` (the default: a soft cyan bar behind the buggy line, the only marker still visible at 168 px), `squiggle` (a red wavy underline, like an editor's error), or `underline` (a thick cyan underline). Each adds a small flat red bug glyph in the gutter. Red stays a small accent; never ring the line.
7. **Propose 3 free variants first:** `T <channel> <n> --text "<a>" --text "<b>" --text "<c>" --candidates 3` with the layout's options (for `spot-the-bug`: `--layout spot-the-bug --code W/videos/<n>/thumbnail/code.txt --mark <line>`, and `--marker` once, or once per candidate to compare markers). No subject means no Gemini call and no cost. It writes `thumbnail-1.png` to `thumbnail-3.png` and `thumbnail-candidates.png`, a contact sheet of all three at full, 320 px, and 168 px width; show the owner the sheet.
8. **Paid art, only on the owner's yes:** when the owner wants a character or art layout, recommend 2 or 3 art candidates (`--candidates`), as the first image is rarely right (F15, F16). The cost is about USD 0.07 for each image not already cached from the same prompt. Show the layout, texts, subject, code, and total, and ask the owner's yes. No yes: stay with the free variants. Changing the layout or subject changes the prompt, so it needs new art (and a new yes). Then `T <channel> <n> --text "<text>" --subject "<subject>" --layout <layout> --candidates <N>` (one `--text`, or one for each candidate); it prints the cost before calling Gemini, caches the art in `W/videos/<n>/thumbnail/`, and writes the candidates and the contact sheet the same way.
   - For either run, exit 0: written, with a report of the contrast and cap height it checked; `thumbnail.png` for one candidate. Exit 2: fix what it names (text too long: fewer or shorter words; no challenge: a question or challenge verb; no AI cue: AI in the text, the chip, or the subject). Exit 3: the cached art came from another prompt; keep the subject and layout, or, on the owner's yes to the cost, rerun with `--new-art`. Exit 1: report the error; a Gemini error may name a key or quota problem, a font or Chrome error names the README Setup step.
9. **Check each candidate** at full size, 320 px wide, and 168 px wide (the contact sheet shows all three sizes; or `ffmpeg -v error -i <file> -vf scale=320:-1 .temp/<name>-320.png`, the same for 168), against this checklist:
   1. One focal subject, the largest thing in the frame, about 40 to 60% of its height (F2, H1, H2).
   2. The payoff, such as the marked line, still identifiable at 320 and 168 px (F4, H1).
   3. A readable emotion: a face with a clear expression, when the layout has art (F1, F5, H3).
   4. The channel's field (`thumbnail.field`, such as a grey gradient): the edge stays visible against YouTube's #0F0F0F page (F13, H1).
   5. Text of 2 to 4 words that adds to the title instead of repeating it (H4).
   6. Text that challenges or questions the viewer, so the viewer wants the answer (H4).
   7. AI shown when the video is about AI: in the text, the chip, or the art.
   8. Text legible at 168 px; `T` already holds its cap height at 15% or more (F3, H4).
   9. Warm white text with one cyan key word; red only as a small accent shape (bug glyph, squiggle, underline, disc), never as text and never a large ring (F13, H5).
   10. Contrast: text 4.5:1 and markers 3:1, which `T` checks on both `thumbnail.field` colours and the code panel; check the art next to them by eye too (F12, H5).
   11. Simple: subject, text, and one marker; nothing else competes (F2).
   12. Accurate: it shows what the video shows, and the question matches its answer (F6).
   13. The art has no letters, numbers, fake writing, or logos (F16).
   14. Recognisably the channel's (its field colour, code panel or clay style, cyan key word, text placement) while this video's subject is new (F7, H7).
   - A fault in one candidate: drop it. Every candidate faulty: write a new subject and, with the owner's yes to the cost, rerun with `--new-art`; a text change only: rerun without it (free). A layout fault: propose it to the producer as an improvement for the retrospective; never edit the templates in a video run.
10. **Pick:** show the owner the passing candidates with your recommendation; on the owner's choice, `T <channel> <n> --pick <k>` copies it to `thumbnail.png` or `.jpg` (free). Skip for one candidate.
11. **Report on the issue:** write a scratch file of the line `YouTube: thumbnail`, then the layout, text, marker, subject, art (`generated` or `cached`) and cost, the picked file, format, and size, and the checklist result; post it with `gh issue comment <n> --body-file <file>`. Add the Test & Compare advice: in YouTube Studio the owner may test up to 3 clearly different thumbnails, such as the other passing candidates or a second layout; too-similar variants make the test run longer; it takes a few days to 2 weeks and picks the winner by watch time share (F10); read Home and Suggested click-through rate in the first 24 hours (F9). Return to the producer with the thumbnail's path.

## Output

The `YouTube: thumbnail` comment's link, the thumbnail's path, layout, format, and size, the candidates made (with their texts and markers, and the contact sheet's path) and the one picked, the checklist result, and whether the art was generated (paid, with the cost) or cached. A refused channel, a stage mismatch, a missing script, key, font, Chrome, or ffmpeg, no yes to the cost, or a Gemini error is reported as blocked with the script's message.

## Constraints

- All thumbnail text comes from the template's text slot; art is never asked for text, and art showing writing is replaced, never kept.
- Proposes free variants first; pays for art only after the owner's yes to the total in this session; never reruns `--new-art` or raises `--candidates` with a subject to try variations unasked.
- Never edits `script.json`, `channel.yaml`, or the style guide; title changes go to `write-video-script` or `package-video`, style changes to the owner. The templates and `scripts/thumbnail.py` are components: changes to them are new work requests (D-038).
- Never prints, logs, or posts the API key. Generated images stay out of git (the workspace ignores `*.png`, `*.jpg`); never commits workspace files to aksa.
- Never passes a gate, moves a stage, or edits labels or the body; `C` and `youtube-producer` own those (D-042).
- The F and H labels are rationale citations only: F a cited fact, H a labelled hypothesis, of the research output `.kb/outputs/research/2026-10-24-youtube-thumbnails.md`. Outputs are not trusted knowledge (`agentic/rules/knowledge.md`); the procedure never reads it, and the rules here bind on their own.

## Done when

- `T` exited 0 and `W/videos/<n>/thumbnail.png` or `thumbnail.jpg` exists, 3840x2160 and at most 2 MB, as its report shows: written directly for one candidate, or by `--pick` from the owner's choice.
- Each candidate shown to the owner was checked at full size, 320 px, and 168 px against the 14-point checklist, and the picked one passes it.
- The owner saw 3 free variants before any paid art was proposed.
- The `YouTube: thumbnail` comment is on the issue, with the Test & Compare advice, no placeholder, and no em dash.
