---
name: create-handoff
description: Use when the owner asks to hand off, hand over, pass on, pause work for someone else, or brief another tool, agent, or person to continue the current session's work. Writes a self-contained handoff note (goal, current state, verified work, open decisions, next steps as exact commands, artifacts), checked for secrets, to .temp/handoffs/.
---

# Create handoff

## Inputs and prerequisites

- The work: the current session, plus the branch, worktree, and pull requests it touched.
- The reader (tool, agent, or person) and their access (repository, GitHub). Ask only if neither the request nor the session says; when the owner is not present, assume another agent with the same access and say so in **For**.
- The destination: `.temp/handoffs/` (gitignored, this machine only) by default, or a pull request comment or the reply itself when the owner asks.
- Note shape: `references/handoff-template.md` in this skill's folder.

## Procedure

1. **Collect facts, not memory.** Run and read `git status`, `git log --oneline origin/main..HEAD`, `git worktree list`, `git remote get-url origin`, and `gh pr list --author @me`. For each open pull request, record its check results with `gh pr checks <n>`. Do not run the checks by hand (`AGENTS.md`); state that uncommitted changes have not been checked.
2. **Fill the template:** goal, current state, done and verified (each with evidence from step 1, or a commit or PR link), not done, open decisions for the owner, next steps as exact commands in order, artifacts, and the rules the reader must follow (`AGENTS.md` and the files in `agentic/rules/` that apply). Use terms from `agentic/memory/vocabulary.md`.
3. **Make it self-contained.** No "as discussed" and no references to this session's turns. State where uncommitted changes live, since only this machine has them. Replace a command the reader cannot run with their access by what to ask for.
4. **Check before sharing.** Remove secrets, tokens, `.env` values, and personal data; check `.env` values with `grep -cF` so they are never printed. Remove absolute or machine-specific paths (D-012) and em dashes, then re-read the note.
5. **Deliver.**
   - Default: write `.temp/handoffs/<YYYY-MM-DD>-<slug>.md`. A reader on another machine needs a pull request comment or the reply instead.
   - Pull request comment: show the owner the note first, then `gh pr comment <n> --body-file <file>`.
   - Reply: return the note as the response.

## Output

The note's location (path, comment link, or the note itself) and a one-line summary of what the reader picks up. Report an unreachable destination as blocked, with the command output.

## Constraints

- Record the work; never change it. Do not commit, push, or close anything on the work's branch; list uncommitted changes under **Current state** and **Not done** instead.
- Ask only for what the session and repository cannot answer.
- Never write a handoff to the Knowledge Base or Memory: it holds facts about aksa work, not domain knowledge (D-015), and it is not an agreed term or decision.

## Done when

- Every **Done and verified** item has evidence from a command run in step 1, a commit, or a PR link.
- Every next step is an exact command the reader can run with their access, or names what to ask for.
- The note has no secret, `.env` value, absolute path, em dash, or reference to this session's turns.
- The note is at its destination.
