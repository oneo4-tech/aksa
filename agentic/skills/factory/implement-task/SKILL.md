---
name: implement-task
description: Use when a factory run in stage build has an open task (the next line of its checklist, or the whole of a small run), or when verify-task sends blocking findings back. Builds the task test-first in the run's worktree and inside the task's scope, pushes small conventional commits, and opens a small run's draft pull request; in fix mode it fixes only the blocking findings. Returns the evidence for each acceptance criterion.
---

# Implement task

## Inputs and prerequisites

- The factory issue in stage `build`: `uv run agentic/scripts/factory_issue.py status <n>` gives the next task, its branch, and the delivery branch. A small run is one task, `T1`, on its delivery branch. In fix mode, the blocking findings of the task's latest `Factory: verify` comment, or the items of the latest `Factory: owner review` comment marked to change in this run.
- The contract: the acceptance criteria the task covers (the end of its title, or all of them for a small run), each with its test from the Requirement or Spec, and the Concept's "To record" items.
- Rules: `agentic/rules/coding.md` (test first), `agentic/rules/git.md` (worktrees and commits), `agentic/rules/components.md` (component changes).

## Procedure

1. **Worktree:** work only in the run's one worktree: create it for the run's first task or a small run, and start each later task on a fresh branch in it, as `agentic/rules/git.md` describes (D-039). A branch left by an earlier session: continue it.
2. **Restate the contract** before any code: each criterion the task covers and the test that will prove it. A criterion whose test was not agreed at G1 or G2 is a blocker (step 8).
3. **A fix run** starts with `diagnose-bug`; the fix lands behind its failing regression test.
4. **Build one behaviour at a time** (`agentic/rules/coding.md`): red, watching the test fail for the expected reason; green, with the least code; refactor with the test green. Run the one test while building; the pre-commit hook runs the full checks on each commit. Reach green by fixing the code.
   - A component change starts from its template in `agentic/templates/` and follows `agentic/rules/components.md`; its tests are `tests/test_repository.py` and a `review-component` pass. After adding or renaming a skill, run `uv run agentic/scripts/sync_vendors.py claude codex`.
5. **Record agreed Memory:** on the run's first task, add the Concept's "To record" items through `add-memory`.
6. **Commit as you go:** one small change per commit, conventional, with `Refs #<n>` (`agentic/rules/git.md`), pushed after each commit. At a small run's first push, open the run's draft pull request as `agentic/rules/git.md` describes, and record it: `factory_issue.py set <n> --pr <pr>`.
7. **Finish:** every covered criterion's test passes; run `review-component` on each changed component; push. Return the branch, its head commit, the evidence per criterion (test or review result), and the `review-component` results.
8. **Stop when the owner is needed:** a test not agreed, work bigger than the task, or a step only a person can do. Commit and push what is done, post a `Factory: blocker` comment on the factory issue (what, why, the options with a recommendation), and return blocked. Going back takes `factory_issue.py stage <n> <stage> --reason "<what>"`: a wrong spec to `spec`, a wrong requirement to `define`, and work bigger than the task to `plan` in a large run or to `define` in a small run, to size it large.

## Fix mode

- The input is the blocking findings by id, such as `F2`, from the latest `Factory: verify` comment, or the owner's review items, such as `R1`.
- Work in the run's worktree, on the task's branch. Each fix gets a test first where behaviour changes, then the fix, in a commit naming its finding or item: `fix(<scope>): address F2`.
- Return when every blocking finding has its commit; notes are never touched.

## Output

The task branch with its commits pushed, its head commit, the evidence for each covered criterion, and the `review-component` results; or blocked, with the blocker comment's link.

## Constraints

- Stay inside the task's criteria; anything beyond them goes to the owner as a new work request.
- Never weaken, skip, or delete a test, bypass a hook, force-push, or amend a pushed commit.
- Never review your own work, land the task, or tick it: `verify-task` does those.

## Done when

- Every criterion the task covers has a passing test, or a `review-component` pass for a component, named in the returned evidence.
- Every commit passed the pre-commit hook and is pushed; for a small run, the draft pull request exists and is recorded on the factory issue.
