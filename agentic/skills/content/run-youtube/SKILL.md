---
name: run-youtube
description: Use when the owner asks to make, start, resume, or list YouTube videos for a channel, as `run-youtube <channel>` with an idea, `#<n>`, or nothing. Content work, not a Software Work Request. Files or resumes a video's content issue as the youtube-producer agent, or shows the channel's open videos.
---

# Run YouTube

## Inputs and prerequisites

- The owner's arguments, verbatim: `<channel>` plus an idea text, `#<n>`, or nothing. No channel named: ask the owner which channel.
- The agent: `agentic/agents/youtube-producer.md`.
- The owner's feedback rules: `references/feedback-rules.md`, every common rule from past reviews traced to its pipeline step; the agent reads it on every run.
- `gh` signed in to the repository. If `gh auth status` fails, ask the owner to sign in and stop.

## Procedure

1. Check intent: start or resume a video only for a request to make, resume, or list a channel's videos. A request to change the workflow's code or components is a Software Work Request for `run-factory`; read-only questions get an answer without filing an issue.
2. Read `agentic/agents/youtube-producer.md` and `references/feedback-rules.md`.
3. Act as that agent for the rest of the session, passing it the arguments.

## Output

The agent's output: what the video did and what it now waits for, or the channel's queue of open videos.

## Constraints

- A launcher only: the agent owns input handling, routing, and stopping, as `run-factory` does for the factory (D-027).
- Run in the main session, never in a sub-agent.
- Never creates a factory issue for the video itself; content issues carry `kind:youtube` (D-047).

## Done when

- The session acted as the agent, with `references/feedback-rules.md` read, and reported the agent's output.
