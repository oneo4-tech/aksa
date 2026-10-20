---
name: ship-change
description: Use when a factory run is in stage ship, or the owner asks to ship a run or get its pull request ready to merge. Brings the run's pull request up to date with main, checks CI and that verified work covers every acceptance criterion, marks it ready with a ship summary for the owner, and after the owner merges closes out the run.
---

# Ship change

## Inputs and prerequisites

- The factory issue in stage `ship` and its pull request (`uv run agentic/scripts/factory_issue.py status <n>`). Another stage: stop and report it.
- The verify reports on the factory issue (`Factory: verify` comments) and their notes.

## Procedure

1. **Bring it up to date:** if `gh pr view <pr> --json mergeStateStatus` says `BEHIND`, run `gh pr update-branch <pr>`, which merges `main` into the delivery branch on GitHub. If it conflicts: `git fetch origin`, `uv run agentic/scripts/new_worktree.py <prefix>/<n>-sync origin/<delivery branch>`, merge `origin/main` there, resolve with `resolve-merge-conflicts`, `git push origin HEAD:<delivery branch>`, then remove that worktree and branch.
2. **Check:**
   - CI is green on the head: `gh pr checks <pr> --watch`.
   - The verify reports mark every acceptance criterion, AC1 to ACn, met.
   - The body has `Closes #<n>`, the run's decisions for the owner, and every changed component's `review-component` result: `uv run agentic/scripts/check_pr_review.py origin/main --body-file <file>` passes.
   A failure goes back: `factory_issue.py stage <n> build --reason "<what failed>"`.
3. **Hand over:** `gh pr ready <pr>`, then a `Factory: ship` comment on the factory issue: the pull request, CI, each criterion with its evidence, the notes from verify reports each with a recommendation (a new work request or nothing), and the merge method, squash for a small run or a merge commit for an integration branch (D-029). Then `factory_issue.py set <n> --owner wait`, and stop.
4. **Close out** after the owner's merge (`gh pr view <pr> --json state` says `MERGED`, and `Closes #<n>` closed the issue): `factory_issue.py set <n> --owner clear`; file each note the owner wants as a new work request with `factory_issue.py intake`; remove the run's worktrees and local branches (`agentic/rules/git.md`); and comment `Factory: shipped in <merge commit>.`

## Output

Before the merge, the ready pull request and the ship comment's link; after it, the merge commit and the closed factory issue. Report a failed check as blocked, with the stage moved back to build.

## Constraints

- Only the owner merges into `main`, or tells you to in this session (D-029, D-037).
- No new review: each task was verified before it landed (D-032), and CI and the checks above are the only gates here.
- Never rebase or force-push the delivery branch; `gh pr update-branch` without `--rebase` merges.

## Done when

- Before the merge: the pull request is ready, CI is green, its body passes `check_pr_review.py`, and the factory issue has the ship comment and `needs:owner`.
- After the merge: the factory issue is closed with `needs:owner` cleared, the closeout comment names the merge commit, and the run's worktrees are removed.
