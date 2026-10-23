**Prototype:** `prototype/youtube-standards` (follow `prototypes/youtube-standards/README.md`; pages `out/index.html` and `out/round2.html` to `out/round6.html`)

**Question:** for each production aspect of the OneO4TestLab channel, which option does the owner accept as the channel standard, and what research, evidence, backlog, and branding practices go with it?

**Answer:** the owner chose, from 2026-10-23 rounds 1 to 6 (Concept decisions 33 to 61 on #28):

- Voice: Gemini 3.8 Flash TTS designed voice "mentor", warm style in `speech_metadata.style`, played at 0.92; jargon respelled through a pronunciation list; `//` pause markup with a transcript leak check.
- Script: rotate challenge-first, incident story, and myth buster; revised writing rules with banned phrases; full gate 2 review.
- Visuals: neon-terminal style, focus-line code, fade transitions, Vox-style animated scenes at "more" intensity, a visual change every 2-3 sentences; terminal demos recorded with VHS.
- Audio: two-pass loudness to -14 LUFS and -1 dBTP; Lyria ambient bed at -30 dB.
- Captions: Shorts word-highlight burned in; long-form SRT; wording from the script.
- Thumbnails: combined template with clay-3D Gemini art, layouts rotating.
- Metadata: challenge titles of 60 characters or fewer, short description with chapters, 5-8 tags, disclosures.
- Shorts: standalone challenge, 30-60 seconds, one channel, linked to the long-form.
- Gates 1 to 3: full checklists.
- Backlog: research strategy with the RST lens, weekly scan, scoring, per-idea YouTube competitive research (cached; 100 searches a day), 23 ideas approved.
- Evidence: every claim with a link that opens the source at the quote plus the quoted line, auto-checked for an exact match.
- Branding: generated from the oneo4 logo spec v0.4; deep red `#CC0000` syntax, warm white `#F2EFE6` name, cyan `#00E5FF` suffix, background `#0F0F0F` (YouTube dark theme); structured channel description; brand spec captured in the Knowledge Base inbox.
- Demo code: public `oneo4-tech/testlab-demos`, MIT, a folder per video. Newsletter: separate run #31.

**Why:**

- Every choice was made by the owner from rendered or audible variants, with research from official sources (`.kb/outputs/research/2026-10-23-youtube-production-standards.md`, `2026-10-23-testing-backlog-research.md`).
- Surprises: Gemini 3.8 TTS reads style text aloud unless it goes in the separate style field; `<long pause>` leaked once and `//` paused cleanly; Gemini image models have no free tier (about $0.07 per image); single-pass loudnorm misses its target; Playwright videos show no cursor; Web Animations timing must be linear across multi-step keyframes; the AI Studio key cannot call the YouTube Data API, and quota-free reruns need cached searches; the Playwright healer's docs say it skips tests it believes are broken, so a "hides the bug" claim needs a recorded demo.
- Not settled here: refined competitive queries for ideas 4, 7, 17, 21, 23, 24 (rerun after the quota reset; backlog data, not a standard).
