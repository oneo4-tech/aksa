---
name: draft-newsletter
description: Draft a newsletter issue from a published video's script and citation dossier, put it on Kit as a draft, and send it only after the owner's yes on the video's GitHub issue.
---

# Draft newsletter

## Inputs and prerequisites

- The GitHub issue number of the published long-form video in the video project.
- The per-video folder `.projects/youtube/<video-project>/videos/<issue-number>/` with `script.md` and `citations.md` (#28's output contract).
- `.projects/content/oneo4-newsletter/config.yaml` with `platform: kit`, `publication_id`, `sender_name`, `sender_email`, `signup_url` (template: `references/config.yaml.example`).
- `KIT_API_KEY`, `GH_TOKEN`, and `GITHUB_REPOSITORY` in the environment; `KIT_API_KEY` is listed in `.env.example`.

If an input is missing, stop and report what is missing. Never invent script or citation content.

## Procedure

1. Load the newsletter config with `scripts/config.py` (`load_newsletter_config`).
2. Read `script.md` and `citations.md` from the per-video folder.
3. Extract metadata (title, video URL, summary, key points) with `scripts/draft_newsletter.py` (`extract_metadata`).
4. Render the Markdown issue from `references/templates/newsletter.md.j2` and write it to `newsletter.md` in the video folder.
5. Convert the Markdown to Kit-compatible HTML with `scripts/markdown_to_html.py` (`convert`), code blocks highlighted.
6. Create the draft in Kit with `scripts/kit_client.py` (`create_draft`) and keep the preview URL.
7. Write the Kit signup URL back to the newsletter config (`update_signup_url_in_config`), for #28's description template.
8. Add the `newsletter:draft` label and a comment with the preview URL on the video's GitHub issue, using `scripts/github_client.py`.
9. Wait for the owner's yes: the `newsletter:approve` label or a comment that contains `newsletter:approve`.
10. On the yes: add `newsletter:approved`, send with `send_draft`, add `newsletter:sent`, and comment the result.
11. With no yes before the timeout: add `newsletter:timeout`, comment why, do not send, and end with exit code 3.

Run the whole flow as one command:

```bash
uv run python agentic/skills/content/draft-newsletter/scripts/draft_newsletter.py <video-issue-number> \
  --video-project oneo4-testlab --newsletter-project oneo4-newsletter
```

Manual fallback: if the Kit send fails, leave the draft in Kit and tell the owner to send it from the Kit UI; record the owner's send with the `newsletter:sent` label and a comment.

## Output

- `newsletter.md` in the video folder.
- A Kit draft with its preview URL, commented on the video issue.
- The signup URL in the newsletter config.
- On the owner's yes: the sent newsletter and the `newsletter:approved` and `newsletter:sent` labels.
- On failure or no yes: what is blocked, the exit code (2 bad input, 3 waiting for the owner), and what the owner must do.

## Constraints

- Sends only after the owner's recorded yes on the video's GitHub issue (AC4); never sends on the agent's own judgement.
- Use the agreed terms: the owner, factory issue, video project, newsletter project (`agentic/memory/vocabulary.md`).
- Secrets come from the environment; never print or commit them (`AGENTS.md`).
- Writes to `.projects/` and `.kb/` only through the repo-root symlinks (D-012).
- Kit sends at most one email a day to the list; one issue per long-form video stays under.

## Done when

- `newsletter.md` exists in the video folder and its code blocks render as highlighted HTML in the Kit draft.
- The Kit draft exists and its preview URL is commented on the video issue.
- The signup URL is written to the newsletter config.
- The video issue carries the right labels for its stage: `newsletter:draft`, then `newsletter:approved` and `newsletter:sent` after the owner's yes, or `newsletter:timeout` otherwise.
- The owner has seen the preview link before any send.
