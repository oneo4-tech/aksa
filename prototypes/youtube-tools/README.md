# PROTOTYPE: youtube-tools

Throwaway. Never merged into `main`. Factory run #28, Concept decisions 29 and 31.

**Question:** for one sample video ("Spot the Bug: an AI-written unit test that passes but tests nothing"), which free or already-paid option gives acceptable quality for each production step, and how long does each step take?

## Run

From this folder, with `GEMINI_API_KEY` exported, `ffmpeg`, `whisper-cli`, Chrome, and `ggml-base.en.bin` in the home folder under `.cache/whisper/`:

```sh
for v in long short1; do
  uv run --no-project steps/narrate.py content/scenes-$v.json say
  uv run --no-project steps/narrate.py content/scenes-$v.json gemini-gemini-3.8-flash-tts
  TTS_STYLE="Say in a calm, curious, unhurried tone: " uv run --no-project steps/narrate.py content/scenes-$v.json gemini-gemini-2.5-flash-preview-tts
  uv run --no-project steps/render.py slides content/scenes-$v.json
done
uv run --no-project steps/render.py thumb
uv run --no-project steps/thumb_gemini.py gemini-3.1-flash-image
for v in long short1; do for e in say gemini-gemini-3.8-flash-tts gemini-gemini-2.5-flash-preview-tts; do
  uv run --no-project --with pillow steps/edit.py content/scenes-$v.json $e; done; done
uv run --no-project steps/compare.py && open out/index.html
```

Media lands in `out/` (gitignored). `demo/mutate.sh` is the on-screen demo.
