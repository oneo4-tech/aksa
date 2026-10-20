---
name: ship-change
description: Use when a factory run is in stage ship, or the owner asks to ship a run, review its pull request, or merge it. Brings the run's pull request up to date with main, checks CI and that verified work covers every acceptance criterion, marks it ready, asks the owner for review feedback, merges on the owner's explicit yes, and closes out the run.
---

# Ship change

## Inputs and prerequisites

- The factory issue in stage `ship` and its pull request (`uv run agentic/scripts/factory_issue.py status <n>`). Another stage: stop and report it.
- The verify reports on the factory issue (`Factory: verify` comments) and their notes.

## Procedure

1. **Bring it up to date:** read `gh pr view <pr> --json mergeable,mergeStateStatus`, and read it again after a few seconds while `mergeable` is `UNKNOWN`, which means GitHub is still computing it. On `mergeStateStatus` `BEHIND`, run `gh pr update-branch <pr>`, which merges `main` into the delivery branch on GitHub. When `mergeable` is `CONFLICTING`, which a draft does not hide, or the update fails on a conflict: `git fetch origin`, `uv run agentic/scripts/new_worktree.py <prefix>/<n>-sync origin/<delivery branch>`, merge `origin/main` there, resolve with `resolve-merge-conflicts`, `git push origin HEAD:<delivery branch>`, then remove that worktree and branch.
2. **Check:**
   - CI is green on the head: `gh pr checks <pr> --watch`.
   - The verify reports mark every acceptance criterion, AC1 to ACn, met.
   - The body has `Closes #<n>`, the run's decisions for the owner, and every changed component's `review-component` result: `uv run agentic/scripts/check_pr_review.py origin/main --body-file <file>` passes.
   A failure goes back with `factory_issue.py stage <n> <stage> --reason "<what failed>"`: a small run to `build`, where `implement-task` fixes the failed check in fix mode; a large run to `plan`, for a task that fixes it.
3. **Hand over:** `gh pr ready <pr>`, then a `Factory: ship` comment on the factory issue: the pull request, CI, each criterion with its evidence, the notes from verify reports each with a recommendation (a new work request or nothing), and the merge method, squash for a small run or a merge commit for an integration branch (D-029).
4. **Ask for the owner's review:** "Have you reviewed? Do you have any feedback on PR #<pr> (<link>)?", with three answers: no feedback, merge now; no feedback, merge later; feedback. Review comments the owner left on the pull request are feedback too: `gh pr view <pr> --comments`, and the inline ones from `gh api --paginate repos/{owner}/{repo}/pulls/<pr>/comments`.
   - **Feedback:** post it as `Factory: owner review of #<pr>`, numbered R1, R2, and so on, each with the owner's call: change in this run, a new work request (`factory_issue.py intake`), or no change. Changes go back as in step 2, the owner's review standing as the fix task's G3, and the run ships again from step 1.
   - **No feedback, merge now:** comment `Factory: the owner approved merging #<pr>.` on the factory issue, then go to step 5.
   - **Merge later, or the owner is absent:** `factory_issue.py set <n> --owner wait --need "Review PR #<pr>: feedback, or the yes to merge"`, and stop.
5. **Merge on the owner's yes recorded in step 4** (D-040): `gh pr merge <pr> --merge` for an integration branch, or `--squash` for a small run.
6. **Close out** after the merge, by step 5 or by the owner on GitHub (`gh pr view <pr> --json state` says `MERGED`, and `Closes #<n>` closed the issue): `factory_issue.py set <n> --owner clear`; file each note the owner wants as a new work request with `factory_issue.py intake`; remove the run's worktree and its local branches (`agentic/rules/git.md`); and comment `Factory: shipped in <merge commit>.`

## Output

Before the merge, the ready pull request, the ship comment's link, and the owner's answer; after it, the merge commit and the closed factory issue. Report a failed check as blocked, with the stage moved back.

## Constraints

- Merge into `main` only on the owner's explicit yes (D-040); the owner may also merge on GitHub.
- No new review: each task was verified before it landed (D-032); CI, the checks above, and the owner's review are the only gates here.
- Never rebase or force-push the delivery branch; `gh pr update-branch` without `--rebase` merges.

## Done when

- Before the merge: the pull request is ready, CI is green, its body passes `check_pr_review.py`, the factory issue has the ship comment, and the owner's review is recorded or the run waits with its need.
- After the merge: the factory issue is closed with `needs:owner` cleared, the closeout comment names the merge commit, and the run's worktree is removed.
