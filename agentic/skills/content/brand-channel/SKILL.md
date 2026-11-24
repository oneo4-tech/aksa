---
name: brand-channel
description: Use when a channel needs its branding made, or the owner asks to regenerate it after a palette, wordmark, or banner text change. Generates the avatar (800x800), banner (2048x1152, text inside the 1235x338 safe area), watermark (150x150), and wordmarks from the oneo4 logo spec geometry and the channel palette into the workspace's branding/ folder as SVG sources and PNG renders checked against YouTube's limits, and hands them to the owner to upload; uploads nothing. With --backdrop, and only on the owner's yes, generates the slide backdrop (a dim, photo-like test lab scene, 16:9) with Gemini 3.1 Flash Image for about USD 0.07, cached by prompt, as branding/backdrop.jpg.
---

# Brand channel

## Inputs and prerequisites

- The owner's feedback rules: `agentic/skills/content/run-youtube/references/feedback-rules.md`, its rows for step `brand-channel`.
- The channel name. No channel: ask the owner which.
- Written below: `B` for `uv run agentic/skills/content/brand-channel/scripts/branding.py`, and `W` for the workspace `.projects/content/yt-<channel>/`.
- The channel workspace, checked with `uv run agentic/scripts/youtube_channel.py check <channel>`; exit 2: show its message and stop. Read the style guide section `Visual style` (palette and contrast), and in `channel.yaml` the `palette` and `branding` (`wordmarks`, the first on the banner, `tagline`, `subline`) that `B` applies.
- The logo spec: the `oneo4` brand page of the Knowledge Base (`get-kb`), from the owner's logo spec v0.4. `B` holds its geometry; read the page for the usage rules.
- Google Chrome and the Space Grotesk and Fira Code font files, as the README's Setup lists; missing: ask the owner to install them and report blocked.
- For the backdrop only: `channel.yaml` `branding.backdrop_prompt` (optional; absent, `B`'s default, a dim, photo-like test lab of curved monitors showing code and server racks in soft blue light, no people, text, or logos), `ffmpeg`, and `GEMINI_API_KEY` in `.env` (names only in `.env.example`); missing: ask the owner and report blocked.

## Procedure

1. **Generate:** `B <channel>`. It builds each asset's SVG from the spec geometry and palette, renders each in Chrome at its YouTube size, checks every render's size and file limit before writing any file, and writes `W/branding/<asset>.svg` and `.png`, printing a JSON report.
   - Exit 0: written. Exit 2: a wordmark letter without a spec glyph, a banner line too wide, or an invalid channel; show the message and ask the owner for another word or line in `channel.yaml`. Exit 1: report the Chrome, font, size, or limit error.
2. **Check each asset** against `Visual style` and the spec's usage rules: open each PNG. The 4 and the slash are one stroke with the syntax strokes on top; colours follow meaning (syntax, name, suffix); no outline, shadow, gradient, stretch, or changed slant; the suffix is lighter than the tag; deep red is never used for text. The avatar's icon sits inside the circle YouTube crops to; the banner's wordmark and both lines sit inside the centred safe area; the watermark is legible at 150x150.
3. **The backdrop,** when the owner asks for the slide background or `channel.yaml` `background` names `branding/backdrop.jpg`: `uv run --env-file .env agentic/skills/content/brand-channel/scripts/branding.py <channel> --backdrop`. A backdrop already made from the same prompt is reused and exits 0 with `image` `cached`. Exit 3: a new one costs about USD 0.07; ask the owner, and on an explicit yes run it again with `--yes`. It writes `W/branding/backdrop.jpg` (1920x1080) and `W/branding/backdrop.json` (the model and prompt). Open the JPEG: a test lab scene, dim enough for text over it, with no people, text, logos, or brand; else propose a new `backdrop_prompt` to the owner. Then give the owner the `channel.yaml` line `background: {image: branding/backdrop.jpg, opacity: 0.3, fit: cover}` (opacity at most 0.35 for cover). Exit 1: report the Gemini, key, or ffmpeg error.
4. **Hand over:** give the owner the PNG paths with each one's size and bytes from the report, and where each goes in YouTube Studio (Customization, Branding: picture, banner image, video watermark). The owner uploads them; the SVG sources stay for regeneration.

## Output

The report of each asset (name, SVG and PNG paths, width, height, bytes, YouTube limit) and the check result, handed to the owner to upload; for the backdrop, its path, whether it was cached or generated, its cost, and the `channel.yaml` line. A refused channel, a refused word or line, or a missing Chrome or font is reported as blocked with the script's message.

## Constraints

- The logo geometry follows the owner's spec and is never altered: no new glyphs, paths, weights, slant, or layer order; a missing glyph goes to the owner, who changes the spec first. Colours come only from `channel.yaml` `palette`.
- Uploads nothing and changes no YouTube setting; the owner uploads in YouTube Studio.
- Pays for a backdrop only with `--yes` after the owner's explicit yes in this session; never prints the key.
- Never edits `channel.yaml` or the style guide; changes go to the owner. `scripts/branding.py` is a component: changes to it are new work requests (D-038).
- PNG renders and the backdrop JPEG stay out of git (the workspace ignores `*.png` and `*.jpg`); the SVG sources and `backdrop.json` are the tracked files. Never commits workspace files to aksa.

## Done when

- `B <channel>` exited 0, and `W/branding/` holds the SVG and PNG of the avatar (800x800, under 15 MB), banner (2048x1152, under 6 MB), watermark (150x150, under 1 MB), and each wordmark, as its report shows.
- Each PNG was checked against `Visual style` and the spec's usage rules, and the owner has the paths to upload.
- With `--backdrop`: `W/branding/backdrop.jpg` and `backdrop.json` exist, paid for only on the owner's yes, the image was checked (test lab scene, dim, no text or logos), and the owner has the `channel.yaml` `background` line.
