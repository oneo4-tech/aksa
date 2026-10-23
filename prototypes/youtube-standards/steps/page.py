"""PROTOTYPE: build out/index.html, one section per production standard with its variants and a pick.

uv run --no-project --with markdown steps/page.py
"""

import json
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "out"


def md(name: str) -> str:
    return markdown.markdown((HERE / "content" / name).read_text(), extensions=["tables"])


def radio(group: str, value: str, label: str, media: str = "", multi: bool = False) -> str:
    kind = "checkbox" if multi else "radio"
    return (
        f'<label class="opt"><input type="{kind}" name="{group}" value="{value}">'
        f"<div>{media}<p><b>{value}</b> {label}</p></div></label>"
    )


def audio(src: str) -> str:
    return f'<audio controls preload="none" src="{src}"></audio>'


def video(src: str, tall: bool = False) -> str:
    return f'<video controls preload="metadata" class="{"tall" if tall else "wide"}" src="{src}"></video>'


def img(src: str) -> str:
    return f'<a href="{src}" target="_blank"><img src="{src}"></a>'


def section(n: int, title: str, research: str, body: str) -> str:
    return (
        f'<section id="s{n}"><h2>{n}. {title}</h2><div class="research"><b>Research:</b> {research}</div>{body}'
        f'<textarea class="note" name="note-{n}" placeholder="Notes or changes for {title}"></textarea></section>'
    )


def grid(items: list[str]) -> str:
    return f'<div class="grid">{"".join(items)}</div>'


def main() -> None:
    voices = json.loads((OUT / "voice" / "voices.json").read_text())
    s = []
    s.append(
        section(
            1,
            "Voice",
            "Gemini 3.8 Flash TTS has 30 prebuilt voices; delivery (emotion, pace, tone) goes in a separate speech_metadata.style "
            "field, pauses as inline &lt;short pause&gt; tags, CAPS for stress. Free tier for 3.8 Flash TTS; paid $0.50 in, "
            "$9.00 per 1M audio tokens out (ai.google.dev, 2026-10-22). Test findings: &lt;long pause&gt; is spoken aloud; "
            "jargon was pronounced correctly without respelling. Subtitle guidance assumes 160-180 words per minute (BBC).",
            "<h3>Voice (same paragraph, no style)</h3>"
            + grid([radio("voice", v["voice"], f"{v['wpm']} wpm", audio(f"voice/{v['voice']}.wav")) for v in voices])
            + "<h3>Delivery style (Charon, Interactions API with tags)</h3>"
            + grid(
                [
                    radio("voice-style", k, d, audio(f"voice/style-{k}.wav"))
                    for k, d in [
                        ("tags-only", "no style field"),
                        ("calm", "calm, curious, unhurried, measured pace"),
                        ("confident", "confident, energetic, slightly faster"),
                        ("warm", "warm, conversational mentor"),
                    ]
                ]
            )
            + "<h3>Pace (Charon, time-stretched, pitch kept)</h3>"
            + grid(
                [
                    radio("voice-pace", t, l, audio(f"voice/Charon-pace-{t}.wav"))
                    for t, l in [
                        ("1.00", "as generated, about 195 wpm"),
                        ("0.92", "about 180 wpm"),
                        ("0.85", "about 165 wpm"),
                    ]
                ]
            )
            + "<h3>Jargon pronunciation</h3>"
            + grid(
                [
                    radio("voice-pron", k, l, audio(f"voice/pron-{k}.wav"))
                    for k, l in [
                        ("plain", "pytest, CI, YAML, regex, OAuth, JWT as written"),
                        ("respelled", "pie-test, yamel, rej-ex..."),
                    ]
                ]
            ),
        )
    )
    s.append(
        section(
            2,
            "Script structure",
            "YouTube's own guidance: grab attention immediately, make the topic clear early, tease what is coming "
            "(Creator Playbook); Studio's Intro metric is the share still watching after 30 seconds. YPP inauthentic content "
            "policy (2025-07-15) targets templated, repetitive, mass-produced videos.",
            md("script-variants.md")
            + grid(
                [
                    radio("script", k, l)
                    for k, l in [
                        ("A-challenge", "Challenge first"),
                        ("B-incident", "Incident story"),
                        ("C-myth", "Myth buster"),
                        ("rotate", "Rotate A/B/C by pillar"),
                    ]
                ]
            )
            + grid(
                [
                    radio("script-rules", "agree", "Writing rules as listed"),
                    radio("script-rules", "edit", "Edit in notes"),
                ]
            ),
        )
    )
    s.append(
        section(
            3,
            "Script review (gate 2)",
            "See checklists below; Lean vs Full depth.",
            grid([radio("gate2", "lean", "5 items"), radio("gate2", "full", "12 items")]),
        )
    )
    themes = ["github-dark", "lab-notebook", "neon-terminal"]
    s.append(
        section(
            4,
            "Visual style",
            "WCAG 2.2: text contrast at least 4.5:1 (3:1 for large text), colour never the only signal (1.4.1). "
            "Inter, JetBrains Mono, IBM Plex, Fira Code are SIL OFL 1.1; documents made with them are outside the licence, "
            "so videos and thumbnails are free to use.",
            "".join(
                f"<h3>{t}</h3>"
                + grid([img(f"visual/{t}-{k}.png") for k in ("title", "code", "points", "terminal")])
                + radio("visual", t, "")
                for t in themes
            ),
        )
    )
    s.append(
        section(
            5,
            "Slides",
            "One idea per slide; code readable at phone size (30px code at 1080p); ligatures off so == stays two characters.",
            "<h3>Code presentation</h3>"
            + grid(
                [
                    radio("slides-code", k, l, img(f"slides/{k}.png"))
                    for k, l in [
                        ("a-full-file", "whole snippet"),
                        ("b-focus-lines", "focus lines, rest dimmed"),
                        ("c-zoom-callout", "zoomed lines with callouts"),
                    ]
                ]
            )
            + "<h3>Transition</h3>"
            + grid(
                [
                    radio("slides-transition", k, "", video(f"slides/trans-{k}.mp4"))
                    for k in ("cut", "fade", "slideleft")
                ]
            ),
        )
    )
    s.append(
        section(
            6,
            "Screen share and demos",
            "VHS (MIT) scripts terminal recordings to MP4/GIF/WebM with set font, size, theme, typing speed. "
            "FFmpeg avfoundation captures the macOS screen with capture_cursor and capture_mouse_clicks. macOS can pause "
            "notifications while sharing; Accessibility can enlarge the pointer. Playwright videos show no cursor.",
            grid(
                [
                    radio("capture", "vhs", "scripted terminal (VHS), reproducible", video("capture/vhs.mp4"), True),
                    radio(
                        "capture",
                        "playwright",
                        "scripted browser (Playwright), for UI testing demos",
                        video("capture/playwright.mp4"),
                        True,
                    ),
                    radio(
                        "capture",
                        "live",
                        "live capture by you: steps/capture_screen.sh (not run by the agent)",
                        "",
                        True,
                    ),
                ]
            ),
        )
    )
    s.append(
        section(
            7,
            "Audio",
            "EBU R 128: -23 LUFS, true peak max -1 dBTP (broadcast). YouTube documents a viewer-side Stable volume feature "
            "but no LUFS target. Audio Library music is copyright-safe; Creative Commons tracks need credit. YouTube asks "
            "for AI disclosure when generated music is the main focus. Lyria 3 generated the beds below.",
            "<h3>Loudness (first 30 s of narration)</h3>"
            + grid(
                [
                    radio("loudness", k, l, audio(f"audio/{f}.wav"))
                    for k, l, f in [
                        ("raw", "-18.6 LUFS, peaks +0.9 (clipping)", "voice-raw"),
                        ("-14", "-15.0 LUFS, -1 dBTP", "voice-14"),
                        ("-16", "-16.3 LUFS, -1.5 dBTP", "voice-16"),
                    ]
                ]
            )
            + "<h3>Music bed</h3>"
            + grid(
                [
                    radio("music", "none", "voice only", audio("audio/voice-14.wav")),
                    radio("music", "lyria-lofi", "AI lo-fi bed at -26 dB", audio("audio/mix-lofi.wav")),
                    radio("music", "lyria-ambient", "AI ambient bed at -26 dB", audio("audio/mix-ambient.wav")),
                    radio("music", "audio-library", "YouTube Audio Library track, chosen by you in Studio"),
                ]
            ),
        )
    )
    s.append(
        section(
            8,
            "Captions",
            "WCAG 2.2 SC 1.2.2 (Level A): captions for all prerecorded audio. BBC: 2 lines max for 16:9, 3 for 9:16, "
            "line width 68% (16:9) or 90% (9:16), break at punctuation, white on black. FCC: accurate, synchronous, complete, "
            "never covering important visuals. YouTube accepts SRT and WebVTT.",
            grid(
                [
                    radio("captions-short", k, l, video(f"captions/{k}.mp4", True))
                    for k, l in [
                        ("a-yellow-outline", "phrase, yellow with outline"),
                        ("b-white-box", "phrase, white on black box (BBC)"),
                        ("c-word-highlight", "3 words, current word highlighted"),
                    ]
                ]
            )
            + grid(
                [
                    radio("captions-long", "srt", "long-form: SRT file only, viewer toggles"),
                    radio("captions-long", "burned", "long-form: burned in as well"),
                ]
            ),
        )
    )
    s.append(
        section(
            9,
            "Thumbnail",
            "YouTube: 16:9, recommended 3840x2160 (min width 640), JPG or PNG, 2 MB limit on mobile upload. Gemini image "
            "models have no free tier (3.1 Flash Image about $0.067 per 1K image); aspect ratio is settable. Gemini docs "
            "advise generating text separately, which the combined template does.",
            "<h3>Art style (split layout)</h3>"
            + grid(
                [
                    radio("thumb-art", k, "", img(f"thumbs/split-{k}.png"))
                    for k in ("glossy-cartoon", "flat-vector", "clay-3d")
                ]
            )
            + "<h3>Layout</h3>"
            + grid(
                [
                    radio("thumb-layout", k, "", img(f"thumbs/{f}.png"))
                    for k, f in [
                        ("split", "split-glossy-cartoon"),
                        ("code-circle", "layout-code-circle"),
                        ("face-off", "layout-face-off"),
                    ]
                ]
            )
            + grid([radio("thumb-layout", "rotate", "rotate layouts by pillar")]),
        )
    )
    s.append(
        section(
            10,
            "Metadata",
            "Limits and rules from YouTube Help are in the block below.",
            md("metadata-variants.md")
            + grid([radio("title", k, "") for k in ("A-challenge", "B-statement", "C-question", "match-script")])
            + grid([radio("description", k, "") for k in ("D1-short", "D2-structured")])
            + grid([radio("tags", k, "") for k in ("T1-5-8-tags", "T2-none")]),
        )
    )
    s.append(
        section(
            11,
            "Shorts",
            "Shorts are square or vertical and up to 3 minutes (uploads from 2024-10-15). A Short can link a related video "
            "from your channel (needs advanced features). YouTube shows editor guides for where like, comments, and "
            "description overlay, but publishes no pixel safe zones.",
            grid(
                [
                    radio("shorts", k, l, video(f"shorts/{k}.mp4", True))
                    for k, l in [
                        ("a-cutdown", "cut from the long-form, 25 s"),
                        ("b-challenge", "standalone challenge with countdown, 22 s"),
                        ("c-myth-proof", "myth then proof, 18 s"),
                    ]
                ]
            )
            + grid([radio("shorts-length", k, "") for k in ("under-30s", "30-60s", "up-to-3min")]),
        )
    )
    s.append(
        section(
            12,
            "Gate checklists",
            "",
            md("checklists.md")
            + grid([radio("gate1", k, "") for k in ("lean", "full")])
            + grid([radio("gate3", k, "") for k in ("lean", "full")]),
        )
    )

    nav = "".join(f'<a href="#s{i}">{i}</a>' for i in range(1, 13))
    page = f"""<!doctype html><meta charset=utf-8><title>PROTOTYPE youtube-standards</title>
<style>
body {{ font: 15px -apple-system, sans-serif; background: #0d1117; color: #e6edf3; margin: 0 auto; max-width: 1400px; padding: 16px; }}
.banner {{ background: #9e6a03; color: #fff; padding: 8px 12px; font-weight: 700; border-radius: 6px; }}
nav {{ position: sticky; top: 0; background: #0d1117; padding: 8px 0; z-index: 2; }} nav a {{ color: #58a6ff; margin-right: 12px; }}
section {{ border-top: 1px solid #30363d; padding: 12px 0 24px; }}
.research {{ background: #161b22; border-left: 4px solid #58a6ff; padding: 10px 14px; margin: 8px 0 16px; color: #c9d1d9; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; margin: 10px 0; }}
.opt {{ display: block; background: #161b22; border: 2px solid #30363d; border-radius: 10px; padding: 10px; cursor: pointer; }}
.opt:has(input:checked) {{ border-color: #3fb950; }} .opt input {{ float: right; }}
img, video.wide, audio {{ width: 100%; }} video.tall {{ height: 460px; display: block; margin: auto; }}
table {{ border-collapse: collapse; }} td, th {{ border: 1px solid #30363d; padding: 4px 8px; }}
textarea {{ width: 100%; background: #161b22; color: #e6edf3; border: 1px solid #30363d; }} .note {{ height: 48px; }}
#picks {{ height: 260px; }}
</style>
<div class="banner">PROTOTYPE: throwaway, generated media, never committed</div>
<h1>OneO4TestLab production standards</h1>
<p>Pick one option per group (screen share allows several), add notes, then copy the text at the bottom back to the factory session.</p>
<nav>{nav} <a href="#done">picks</a></nav>
{"".join(s)}
<h2 id="done">Your picks</h2><textarea id="picks" readonly></textarea>
<script>
const out = document.getElementById('picks');
function update() {{
  const picks = {{}};
  document.querySelectorAll('input:checked').forEach(i => (picks[i.name] = picks[i.name] ? picks[i.name] + ', ' + i.value : i.value));
  const notes = [...document.querySelectorAll('.note')].filter(t => t.value.trim()).map(t => t.name + ': ' + t.value.trim());
  out.value = Object.entries(picks).map(([k, v]) => k + ': ' + v).concat(notes).join('\\n');
}}
document.addEventListener('change', update); document.addEventListener('input', update);
</script>"""
    (OUT / "index.html").write_text(page)
    print(OUT / "index.html")


if __name__ == "__main__":
    main()
