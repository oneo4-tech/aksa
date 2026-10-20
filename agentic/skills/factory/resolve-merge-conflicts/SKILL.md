---
name: resolve-merge-conflicts
description: Use when a merge into a factory branch reports conflicts (a task landing on its integration branch, a delivery branch updated from main) or the owner asks to resolve, fix, or untangle merge conflicts. Resolves each conflict by what both sides meant, asks the owner only about true contradictions, and finishes the merge with the checks passing; never rebases.
---

# Resolve merge conflicts

## Inputs and prerequisites

- The worktree with the merge in progress: `git status` lists unmerged paths. With no merge in progress, the branch and the base to merge, from the caller or the owner.
- The factory issue behind each side, from the `Refs #<n>` footers of its commits, for its requirement or task.
- Branch rules: `agentic/rules/git.md`.

## Procedure

1. **Confirm the state.** `git status` must show a merge in progress (a squash merge shows unmerged paths without `MERGE_HEAD`). A rebase in progress: stop and report it, since aksa never rebases. Nothing in progress: run `git fetch origin`, then the merge the caller needs, such as `git merge origin/main`.
2. **Read each side's intent** for every conflicted file: `git log --oneline <ours>...<theirs> -- <file>` lists the commits on both sides, `git show <sha> -- <file>` shows each change, and the factory issue in each commit's `Refs #<n>` says what it was for.
3. **Resolve by intent:**
   - Compatible changes: keep both, such as two new rows, functions, or list items, in a sensible order.
   - One side moved or renamed what the other changed: apply the change at the new place.
   - Generated files: regenerate instead of merging by hand, `uv lock` for `uv.lock` and `uv run agentic/scripts/sync_vendors.py claude codex` for vendor skill folders.
   - Decision rows that took the same id: keep both, give the row not yet on `main` the next free id, and update its references.
   - A true contradiction, where both sides need different behaviour: show the owner both intents and the options with a recommendation, and wait. In a factory run with the owner absent, follow **Owner in the loop** in `agentic/rules/factory.md`.
4. **Leave no markers:** `git diff --check` and `grep -rn -E '^(<<<<<<<|>>>>>>>)' <files>` find nothing.
5. **Conclude:** `git add <files>`, then commit (`git commit --no-edit` for a merge, the landing's own message for a squash merge). The pre-commit hook runs the checks; fix what the merge broke in the code, never by weakening a test. Push.

## Output

The merge commit, pushed, and a report naming each conflicted file with what each side meant and how it was resolved. Report a true contradiction as blocked, with both intents and the options.

## Constraints

- Merge, never rebase, force-push, or amend a pushed commit (`agentic/rules/git.md`). Never work on `main` itself.
- Never pick a side without reading both intents, and never drop a side's change silently.
- Only the owner decides a true contradiction.

## Done when

- `git status` is clean, `git diff --check` reports nothing, and no conflict marker remains.
- The commit passed the pre-commit hook and is pushed.
- Every true contradiction was decided by the owner, and the report names every conflicted file.
