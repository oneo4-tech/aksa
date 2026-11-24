# {{title}}

The demo for a video of the {{channel}} channel.

## What it proves

{{proves}}

## Layout

- `demo/`: the code the video shows, a slice of a real service (realistic values, a real collaborator such as a tax or payment client), not a toy function.
- `tests/`: the tests that prove the claim; they pass.
- `ai-kit/`: rules, an agent skill, and scripts that make an AI coding agent ask the video's tester questions.
- `demo.tape`: the [VHS](https://github.com/charmbracelet/vhs) tape that records the terminal demo.

## How to run

Needs [uv](https://docs.astral.sh/uv/). From this folder:

```sh
uv run --with pytest python -m pytest -q tests
```

Record the terminal demo with `vhs demo.tape`; it writes `demo.mp4`, which git ignores.

## Use it with your AI agent

The `ai-kit/` folder ({{link}}/ai-kit) makes a coding agent ask this video's tester questions before it calls its work done.

- `ai-kit/AGENTS.md`: rules to paste into your AGENTS.md, CLAUDE.md, Cursor rules, or Copilot instructions. From your project's root:

  ```sh
  curl -fsSL {{raw}}/ai-kit/AGENTS.md >> AGENTS.md
  ```

- `ai-kit/skills/{{skill}}/`: an agent skill, and `ai-kit/scripts/`: the helpers it runs. Clone this repository, then from your project's root:

  ```sh
  cp -r path/to/{{repo_name}}/{{folder}}/ai-kit .
  mkdir -p .claude/skills && cp -r ai-kit/skills/{{skill}} .claude/skills/
  ```

  Other agents that read `SKILL.md` folders, such as from `.agents/skills/`, take the same folder.

## Video

{{video}}
- Channel: [{{channel}}]({{channel_url}})
- This folder: {{link}}

{{sources}}

## Licence

MIT; see `LICENSE` at the repository root.
