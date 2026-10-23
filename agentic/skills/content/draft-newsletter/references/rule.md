# Draft newsletter rule

Read when working on the `draft-newsletter` skill or its supporting scripts.

## Behavior

- The skill drafts from `script.md` and `citations.md` in the video folder; it never invents content.
- It writes `newsletter.md`, then a Kit draft, and reports the preview URL.
- It sends only after the owner's yes: the `newsletter:approve` label or a comment containing `newsletter:approve` on the video's GitHub issue.
- Labels track the stage on the video issue: `newsletter:draft`, `newsletter:approved`, `newsletter:sent`, or `newsletter:timeout`.
- The Kit UI send is the manual fallback when the API send fails.
- All paths are repo-relative; output goes only to the video folder and `.projects/content/oneo4-newsletter/`.
- Secrets come from the environment (`KIT_API_KEY`, `GH_TOKEN`); never print or commit them.
