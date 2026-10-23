---
name: draft-newsletter
description: Draft a newsletter issue from curated content, producing a Markdown file ready for review and publishing.
---

# Draft Newsletter

## Inputs and prerequisites

- A topic or theme for the newsletter issue.
- Curated content items (links, summaries, or raw text) to include.
- Access to the newsletter template at `references/templates/newsletter.md.j2`.
- Optional: configuration at `config.py` for defaults (sender, schedule, etc.).

If required inputs are missing, prompt the user for the topic and content items before proceeding.

## Procedure

1. Read the template at `references/templates/newsletter.md.j2` to understand the structure.
2. Gather content items from the user or from a provided source.
3. Render the template with the collected content, producing a Markdown draft.
4. Save the draft to a timestamped file in the workspace (e.g., `.projects/newsletter-YYYY-MM-DD.md`).
5. Present the draft path to the user for review.

## Output

- A Markdown file containing the drafted newsletter issue, structured per the template.
- If rendering fails or content is insufficient, report the failure and what is needed.

## Constraints

- Uses only the template in `references/templates/newsletter.md.j2` for structure.
- Does not publish or send the newsletter; only produces the draft.
- Configuration defaults from `config.py` when added (T2).

## Done when

- The draft Markdown file exists at the expected path.
- The file contains all required sections from the template populated with provided content.
- The user confirms the draft is ready for review.