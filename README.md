# aksa

![CI](https://github.com/oneo4-tech/aksa/actions/workflows/check.yml/badge.svg)
![CodeQL](https://github.com/oneo4-tech/aksa/actions/workflows/codeql.yml/badge.svg)
![Docs](https://github.com/oneo4-tech/aksa/actions/workflows/docs.yml/badge.svg)
![Release](https://img.shields.io/github/v/release/oneo4-tech/aksa?include_prereleases&label=release)
![License](https://img.shields.io/github/license/oneo4-tech/aksa)
![Python](https://img.shields.io/badge/python-3.13+-blue)

`aksa` (Sanskrit for central axis) is an AI workflow operating system with an agent harness and software factory. It keeps agentic components (rules, skills, agents, memory, scripts, templates) in one vendor-neutral place and syncs them to Claude Code, OpenCode, Codex, Gemini CLI, and Copilot.

Agents start from [`AGENTS.md`](AGENTS.md), which also holds the repository map.

## Setup

Requires [uv](https://docs.astral.sh/uv/) and git.

```sh
uv sync                                   # Python and dev tools
cp .env.example .env                      # then fill in keys
git config core.hooksPath .githooks       # pre-commit checks, pre-push guard for main
```

Point the external links at this machine: edit `config/environment.yaml` (the only file with absolute paths), then:

```sh
uv run agentic/scripts/link_external.py   # creates .kb, .projects, .worktrees
uv run agentic/scripts/sync_vendors.py claude codex   # .claude/skills and .agents/skills
uv run agentic/scripts/kb_index.py        # .kb/index.md from the wiki pages
```

Start parallel work in its own worktree, set up the same way: `uv run agentic/scripts/new_worktree.py <branch>`.

Content skills need system tools, installed once. Narration (`narrate-video`) needs `ffmpeg`, `whisper-cli` (whisper.cpp), and its `base.en` model at `.cache/whisper/ggml-base.en.bin` in the home folder, or the path in `WHISPER_MODEL`, plus `GEMINI_API_KEY` in `.env`:

```sh
brew install ffmpeg whisper.cpp
(cd && mkdir -p .cache/whisper && curl -L -o .cache/whisper/ggml-base.en.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin)   # into the home folder
```

Research evidence (`research-video`) and scene rendering (`render-video`) drive Google Chrome through Playwright (no bundled browser); demo recordings (`build-video-demo`) need `vhs`. Rendering also needs `ffmpeg`, `whisper-cli` as above, and the Space Grotesk and Fira Code font files at `.cache/fonts/` in the home folder, or the folder in `RENDER_FONTS`, since scenes never load fonts from the network:

```sh
brew install --cask google-chrome
brew install vhs
(cd && mkdir -p .cache/fonts && cd .cache/fonts \
  && curl -L -o SpaceGrotesk.ttf 'https://github.com/google/fonts/raw/main/ofl/spacegrotesk/SpaceGrotesk%5Bwght%5D.ttf' \
  && curl -L -o FiraCode.ttf 'https://github.com/google/fonts/raw/main/ofl/firacode/FiraCode%5Bwght%5D.ttf')   # into the home folder
```

The Knowledge Base (`.kb`) is its own git repository with `inbox/`, `raw/`, `wiki/`, and `outputs/`; see `agentic/rules/knowledge.md`.

## Checks

```sh
uv run pytest            # scripts and repository invariants
uv run pytest -m media   # real-media render tests, locally only (Chrome, ffmpeg, whisper-cli, fonts)
uv run ruff check .
uv run ruff format --check .
```

The pre-commit hook and CI (`.github/workflows/check.yml`) run the same checks; the hook also checks the vendor sync. On pull requests that change components, `.github/workflows/review.yml` requires a filled **review-component result** section.

## Where things are decided

- Terms: `agentic/memory/vocabulary.md`
- Decisions: `agentic/memory/decisions.md` (superseded: `agentic/memory/decisions-history.md`)
- Memory and Knowledge Base: `agentic/rules/knowledge.md`
- Component standards: `agentic/rules/components.md`
