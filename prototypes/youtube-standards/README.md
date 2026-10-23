# PROTOTYPE: youtube-standards

Throwaway. Never merged into `main`. Factory run #28, Concept open items 1-12 (production standards).

**Question:** for each production aspect of the OneO4TestLab channel (voice, script, script review, visual style, slides, screen share, audio, captions, thumbnail, metadata, Shorts, gate checklists), which option does the owner accept as the channel standard?

Research: `.kb/outputs/research/2026-10-23-youtube-production-standards.md`.

## Run

From this folder with `GEMINI_API_KEY` exported, plus `ffmpeg`, `whisper-cli`, Chrome, `vhs`, and the media of `prototypes/youtube-tools` copied into `out/ref/`:

```sh
uv run --no-project steps/voices.py && uv run --no-project steps/styled.py && uv run --no-project steps/pronounce.py
uv run --no-project steps/music.py lyria-3-clip-preview lofi "<prompt>"
uv run --no-project steps/styles.py && vhs steps/demo.tape && uv run --no-project --with playwright steps/browser_demo.py
uv run --no-project --with pillow steps/captions.py
uv run --no-project steps/art.py && uv run --no-project steps/thumbs.py
uv run --no-project --with markdown steps/page.py && open out/index.html
```

Loudness variants: `steps/loudnorm.sh`. Live capture (owner only): `steps/capture_screen.sh`. Fonts are cached from Google Fonts into `out/fonts/`.
