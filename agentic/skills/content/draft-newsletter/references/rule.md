# Draft newsletter rule

Read when working on the `draft-newsletter` skill or its supporting scripts.

## Behavior

- The skill drafts from `script.md` and `citations.md` in the video folder; it never invents content.
- It writes `newsletter.md`, then a Kit draft, and reports the preview URL.
- It sends only after the owner's yes: the `newsletter:approve` label or a comment containing `newsletter:approve` on the video's GitHub issue in the aksa repository. A label left by an earlier attempt is removed before the new draft is posted. A comment counts only when the owner or a repository member wrote it after the draft comment; the label path relies on repository write access.
- Labels track the stage on the video issue: `newsletter:draft`, `newsletter:approved`, `newsletter:sent`, or `newsletter:timeout`.
- The Kit UI send is the manual fallback when the API send fails.
- The signup URL comes from the newsletter config and is written back to it.
- All paths are repo-relative; output goes only to the video folder and `.projects/content/oneo4-newsletter/`.
- Secrets come from the environment (`KIT_API_KEY`, `GH_TOKEN`); never print or commit them.
