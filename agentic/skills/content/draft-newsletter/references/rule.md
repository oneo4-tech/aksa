# Draft Newsletter Rule

Read when working on the `draft-newsletter` skill or its supporting scripts.

## Behavior

- The skill produces a Markdown draft only; publishing is a separate operation.
- Content items must be provided or gathered interactively before rendering.
- The template at `references/templates/newsletter.md.j2` defines the newsletter structure.
- Configuration from `config.py` (when added) provides defaults for sender, frequency, and formatting.
- All output paths are relative to the repository root or `.projects/` symlink.