# {{title}}

The demo for a video of the {{channel}} channel.

## What it proves

{{proves}}

## Layout

- `demo/`: the code the video shows.
- `tests/`: the tests that prove the claim; they pass.
- `demo.tape`: the [VHS](https://github.com/charmbracelet/vhs) tape that records the terminal demo.

## How to run

Needs [uv](https://docs.astral.sh/uv/). From this folder:

```sh
uv run --with pytest python -m pytest -q tests
```

Record the terminal demo with `vhs demo.tape`; it writes `demo.mp4`, which git ignores.

## Video

{{video}}
- Channel: [{{channel}}]({{channel_url}})
- This folder: {{link}}

{{sources}}

## Licence

MIT; see `LICENSE` at the repository root.
