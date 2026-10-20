# Git

Read before creating a branch, worktree, commit, or pull request, or before merging. A factory run's lifecycle is in `agentic/rules/factory.md`.

## Branches

| Branch | Name | From | Lands in |
|---|---|---|---|
| Small run | `<prefix>/<n>-<slug>` | `origin/main` | `main`, by pull request and squash merge |
| Integration branch of a large run | `int/<n>-<slug>` | `origin/main` | `main`, by pull request and merge commit |
| Task of a large run | `<prefix>/<n>-t<k>-<slug>` | the integration branch | the integration branch, by local squash merge |
| Release | `chore/release-vX.Y.Z` | `origin/main` | `main`, by pull request and squash merge |

- `<n>` is the factory issue number, `<prefix>` the run type's prefix in `config/factory.yaml`, and `<slug>` lowercase hyphenated words (D-030, D-031). `factory_issue.py status <n>` prints a run's branch names; use them as printed.
- Prototype branches follow `build-prototype` and are never merged.

## Worktrees

- Every branch that changes files gets its own worktree: run `git fetch origin`, then `uv run agentic/scripts/new_worktree.py <branch> <base>` with the base from the table, such as `origin/main` or `origin/int/<n>-<slug>`. It lands in `.worktrees/<branch with / replaced by ->`.
- An integration branch gets no worktree: `plan-tasks` creates it with `git push origin origin/main:refs/heads/int/<n>-<slug>`, and it changes only when a task lands or `ship-change` updates it.
- The main checkout stays on a clean `main`. Run git only inside the worktree you work in; one writer per worktree at a time.
- After a branch lands or merges, remove its worktree and local branch: `git worktree remove .worktrees/<dir>`, then `git branch -D <branch>` (a squash merge leaves the branch unmerged in git's view). Delete a task branch's remote copy with `git push origin --delete <branch>`; GitHub deletes merged pull request branches (D-037).

## Commits

- Conventional: `<prefix>(<scope>): <subject>`, with an optional lowercase scope and a subject of at most 72 characters; a body with what and why; a `Refs #<n>` footer for factory work. A breaking change adds `!` after the scope and a `BREAKING CHANGE:` footer. AI co-author trailers are allowed (D-010).
- Small commits, pushed as you go, so another session can resume.
- Never bypass a hook, amend a pushed commit, force-push, or rebase a pushed branch. To update a branch, merge its base into it; on conflicts, use `resolve-merge-conflicts`.

## Pull requests and merges

- A factory run has one pull request into `main`, opened as a draft at the first push of its delivery branch (D-025). Title: the factory issue's title. Body: `.github/pull_request_template.md`, with `Closes #<n>`.
- Mark it ready only at ship. Only the owner merges into `main`: squash for a small run or a release, a merge commit for an integration branch (D-029). `.githooks/pre-push` refuses direct pushes to `main` (D-037).
- A task lands on its integration branch from the task's own worktree (D-028): `git fetch origin`, `git switch --detach origin/int/<n>-<slug>`, `git merge --squash <task branch>`, a commit whose subject is `<prefix>(<scope>): <task title>`, then `git push origin HEAD:int/<n>-<slug>`.
