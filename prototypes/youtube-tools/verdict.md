**Prototype:** `prototype/youtube-tools` (follow `prototypes/youtube-tools/README.md`, then open `prototypes/youtube-tools/out/index.html`)

**Question:** for one sample video ("Spot the Bug: an AI-written unit test that passes but tests nothing"), which free or already-paid option gives acceptable quality for each production step, and how long does each step take?

**Answer:** the owner chose, on 2026-10-22:

- Research, script, demo, metadata, Shorts plan: Claude Code on the existing subscription.
- Narration, long-form and Shorts: Gemini 3.8 Flash TTS (voice Charon) through the AI Studio key, sent plain script text only.
- Slides: HTML templates rendered by headless Chrome; Shorts get code reflowed for a vertical screen.
- Edit: scripted `ffmpeg`; no GUI editor in the first build.
- Captions: `whisper-cli` timings with wording taken from the script; SRT sidecar for long-form, burned in for Shorts.
- Thumbnail: combined, a Claude-designed SVG template for text and layout plus Gemini 3.1 Flash Image art generated without text.
- Media storage: generated media stays out of git; only text artifacts are tracked.
- Pilot pass rule: one long-form video and two Shorts per week within 5 measured owner hours, else lower cadence or raise the budget.

**Why:**

- All three voices were intelligible (whisper transcripts matched the script within 4 distinct words); the owner preferred Gemini 3.8 by ear. Surprise: Gemini 3.8 reads style instructions aloud, so prompts must carry script text only; Gemini 2.5 follows a "Say in a ... tone:" prefix.
- The AI Studio free key hit no rate limits across 26 narration calls and 4 image calls.
- Compute per video was under 3 minutes: narration 15-57s, slides 5-20s, edit 4-30s, captions about 5s, thumbnail about 13s. Owner time is reviews.
- Local `ffmpeg` lacks the drawtext and subtitles filters, so text is rendered as images (Chrome, Pillow) and overlaid.
- `whisper-cli` splits captions mid-phrase, hence script wording with whisper timings.
- Gemini 2.5 Flash Image ignored the 16:9 request; Gemini 3.1 returned 1376x768 and needs a resize. Image models may garble text, so text stays in the SVG template; the combined render kept exact text with Gemini's richer art.
- The 9-scene long-form script ran 2.1-2.8 minutes: a 5-10 minute long-form needs about three times the script.
- `build-prototype` asks for `prototype(<name>):` commits, which `.githooks` rejects; `chore(prototype):` was used.
