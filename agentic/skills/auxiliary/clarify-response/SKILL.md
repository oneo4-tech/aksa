---
name: clarify-response
description: Use when the owner says "I don't follow", "what?", "what do you mean", "explain that more simply", "clarify", "rephrase", or "ELI5" about an earlier agent message or part of it. Re-explains it in an independent subagent, so the work stays out of the main context, as the same claims with the missing context added, in ASD-STE100 Simplified Technical English and aksa's agreed terms, then offers unagreed terms and resumes the interrupted work.
---

# Clarify response

## Inputs and prerequisites

- The owner's question or the confusing part, verbatim. If none is given, the target is the agent's last message.
- The target message: the most recent agent message, or the earlier one the owner names.
- The glossary: `agentic/memory/vocabulary.md`.
- The subagent's method: `references/re-pitch.md` in this skill's folder. Do not read it in the main context.

## Procedure

1. **Note where you stopped:** the pending question or the step in progress. Step 5 returns to it.
2. **Launch one subagent** and wait for its result before replying.
   - Prefer a subagent that inherits the conversation; the brief then names the target message instead of copying it.
   - Otherwise start a fresh subagent and paste the target message, or the named part, verbatim into the brief.
   - If the runtime has no subagents, follow `references/re-pitch.md` inline.

   Brief, with the placeholders filled:

   ```text
   Write a re-pitch. Read agentic/skills/auxiliary/clarify-response/references/re-pitch.md and follow it exactly.
   Target message: <which agent message, or the verbatim text>
   Owner's question: <the owner's words, verbatim>
   Glossary: agentic/memory/vocabulary.md
   Files or commands the owner did not see: <paths or commands from the target message, or "none">
   Return only the RE-PITCH and MISSING TERMS parts.
   ```

3. **Show the re-pitch** exactly as returned, without the `RE-PITCH:` label.
4. **Offer missing terms.** For each term in `MISSING TERMS`, add one line: "`<term>` isn't in `agentic/memory/vocabulary.md`. Add it?" If the owner agrees, propose a one-line meaning and record it with `add-memory` after they approve the wording.
5. **Resume** where step 1 stopped: ask a pending question again, or continue the step in progress.
6. **Still unclear?** Run this skill again with the re-pitch as the target message and the owner's new words verbatim.

## Output

A reply in chat, no files:

```markdown
**Context:** We are talking about how the review finds what changed on your branch.

Your branch started from one commit on `main`. That commit is the **merge-base**.
The review compares your branch with that commit, not with the newest `main`.

`merge-base` isn't in `agentic/memory/vocabulary.md`. Add it?
```

If the subagent fails or returns another shape, say so and run `references/re-pitch.md` inline.

## Constraints

- Same point: no new claims, no dropped claims, no new recommendation.
- Show the re-pitch as returned: no rewrite, comment, or apology.
- Never add a term without the owner's agreement; Memory changes only through `add-memory`.
- Disagreement with the point, or a request for a different recommendation, is a new decision, not a re-pitch; do not use this skill for it.

## Done when

- A subagent wrote the re-pitch, and the main context holds only the brief and the returned result.
- The re-pitch starts with a Context line and carries every claim of the target message, with no new claim or recommendation.
- Every term in `MISSING TERMS` is offered, or the list is `none`.
- The interrupted work has resumed where it stopped.
