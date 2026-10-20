---
name: release-version
description: Use when the owner asks to release, cut or tag a version, or write release notes. Proposes the next SemVer version from the pull requests merged into main since the last tag, the highest change winning, writes the CHANGELOG.md section and the version in a release pull request after the owner approves, and tags and publishes the GitHub release once the owner merges it.
---

# Release version

## Inputs and prerequisites

- The owner's request. Only the owner starts a release; the factory orchestrator never does.
- The last release tag: run `git fetch origin --tags`, then `git describe --tags --abbrev=0 --match 'v*' origin/main`. No tag means the first release.
- The pull requests merged into `main` since that tag: `gh pr list --state merged --base main --limit 200 --json number,title,body,mergedAt`, keeping those merged after the tag's commit date (`git log -1 --format=%cI <tag>`).
- The section format: `references/changelog-section.md` in this skill's folder.

## Procedure

1. **Collect the entries:** every pull request merged since the tag, or all of them on the first release, except earlier release pull requests (`chore(release): ...`). A title with `!` before its colon, or a body with a `BREAKING CHANGE:` line, is breaking; otherwise a `feat` title is a feature, a `fix` title a fix, and anything else a chore. Name to the owner any title outside the `<prefix>(<scope>): <summary>` form.
2. **Propose the version,** the highest change winning (D-035): any breaking entry raises the major version, else any feature raises the minor, else the patch rises. The first release proposes the version already in `pyproject.toml`.
3. **Release gate.** Fill `references/changelog-section.md`: one line per pull request in its group, in merge order, with empty groups left out. Show the owner the version, the rule that decided it, and the section. The owner may only raise the version. An explicit yes also approves tagging and publishing once the owner merges the release pull request.
4. **Open the release pull request.** Run `git fetch origin`, then `uv run agentic/scripts/new_worktree.py chore/release-vX.Y.Z origin/main`. In that worktree, put the section at the top of `CHANGELOG.md`, below its `# Changelog` heading (create the file on the first release); set `version` in `pyproject.toml`; run `uv lock`; commit `chore(release): vX.Y.Z`; push; and open a pull request with that title, the section as its summary, and `none` as its review-component result.
5. **Keep it current.** If another pull request merges into `main` before the owner merges the release, merge `origin/main` into the release branch, add the new entry, and return to step 3 when the version changes.
6. **Tag and publish** after the owner's merge: read the merge commit with `gh pr view <n> --json mergeCommit`, write the section to a file, and run `gh release create vX.Y.Z --target <merge commit> --title vX.Y.Z --notes-file <file>`. Then remove the worktree and its local branch (`agentic/rules/git.md`).

## Output

Before the merge, the release pull request's link; after it, the release URL from `gh release view vX.Y.Z --json url`. Report a declined gate or a failed `gh release create` as blocked, with the reason or the command output.

## Constraints

- A release is not a factory run: it has no factory issue, and the owner merges its pull request with a squash merge (D-029).
- Only this skill writes `CHANGELOG.md` (D-035).
- Tag and publish only after the owner merged the release pull request. Never move or delete a published tag; fix a wrong release with a new patch release.

## Done when

- The owner approved the exact version and section.
- The release pull request has the section at the top of `CHANGELOG.md` and the same version in `pyproject.toml` and `uv.lock`, and its checks passed.
- After the merge, `gh release view vX.Y.Z` shows the tag on the release pull request's merge commit, with the section as its notes.
