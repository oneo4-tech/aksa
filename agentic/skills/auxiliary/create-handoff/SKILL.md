---
name: create-handoff
description: Use when the owner asks to hand off, hand over, pass on, pause work for someone else, or brief another tool, agent, or person to continue the current session's work. Writes a self-contained handoff note (goal, current state, verified work, open decisions, next steps as exact commands, artifacts), checked for secrets, to .kb/outputs/handoffs/.
---

# Create handoff

## Inputs and prerequisites

- The work: the current session, plus the branch, worktree, and pull requests it touched.
- The reader (tool, agent, or person) and their access (repository, GitHub, Knowledge Base). Ask only if neither the request nor the session says; when the owner is not present, assume another agent with the same access and say so in **For**.
- The destination: `.kb/outputs/handoffs/` by default, or a pull request comment or the reply itself when the owner asks.
- Note shape: `references/handoff-template.md` in this skill's folder.
- `.kb` linked for the default destination; if missing, run `uv run agentic/scripts/link_external.py --check` and report the result.

## Procedure

1. **Collect facts, not memory.** Run and read `git status`, `git log --oneline origin/main..HEAD`, `git worktree list`, `git remote get-url origin`, and `gh pr list --author @me`. Run `uv run pytest`, `uv run ruff check .`, and `uv run ruff format --check .`, and record what passed and what failed.
2. **Fill the template:** goal, current state, done and verified (each with evidence from step 1, or a commit or PR link), not done, open decisions for the owner, next steps as exact commands in order, artifacts, and the rules the reader must follow (`AGENTS.md` and the files in `agentic/rules/` that apply). Use terms from `agentic/memory/vocabulary.md`.
3. **Make it self-contained.** No "as discussed" and no references to this session's turns. State where uncommitted changes live, since only this machine has them. Replace a command the reader cannot run with their access by what to ask for.
4. **Check before sharing.** Remove secrets, tokens, `.env` values, and personal data; check `.env` values with `grep -cF` so they are never printed. Remove absolute or machine-specific paths (D-012) and em dashes, then re-read the note.
5. **Deliver.**
   - Default: write `.kb/outputs/handoffs/<YYYY-MM-DD>-<slug>.md`, append `- <date> add outputs/handoffs/<file>: <work>` to `.kb/log.md`, and commit in the Knowledge Base repository (D-018).
   - Pull request comment: show the owner the note first, then `gh pr comment <n> --body-file <file>`.
   - Reply: return the note as the response.

## Output

The note's location (path, comment link, or the note itself) and a one-line summary of what the reader picks up. Report a failed check or an unreachable destination as blocked, with the command output.

## Constraints

- Record the work; never change it. Do not commit, push, or close anything on the work's branch; list uncommitted changes under **Current state** and **Not done** instead.
- Ask only for what the session and repository cannot answer.
- Handoff notes in `outputs/` are not trusted knowledge (D-017); never cite them from `get-kb`.

## Done when

- Every **Done and verified** item has evidence from a command run in step 1, a commit, or a PR link.
- Every next step is an exact command the reader can run with their access, or names what to ask for.
- The note has no secret, `.env` value, absolute path, em dash, or reference to this session's turns.
- The note is at its destination; for the default, `.kb/log.md` has the `add` line and the Knowledge Base repository has it committed.
