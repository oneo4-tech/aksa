---
name: plan-tasks
description: Use when a large factory run is in stage plan, or the owner asks to plan, break down, or slice a requirement into tasks. Splits the approved requirement and spec into ordered vertical slices, each checkable and fitting one session, checks that every acceptance criterion is covered, passes gate G3, writes the task checklist, pushes the integration branch, and moves the run to build.
---

# Plan tasks

## Inputs and prerequisites

- The factory issue in stage `plan`, with its Requirement and Spec; `uv run agentic/scripts/factory_issue.py status <n>` gives the integration branch name. Another stage: stop and report it.
- After a step back from build: the existing checklist and the reason given; landed tasks stay.

## Procedure

1. **Read the artifacts only:** the acceptance criteria, the Spec's tests and notes for planning, and after a step back the reason.
2. **Slice vertically:** each task goes through every layer it needs, is checkable on its own, and fits one session of implementing, verifying, and landing. A prefactor comes first; a wide change no single slice can keep green goes expand, migrate, contract.
3. **Order the tasks** so each needs only earlier ones; they run one at a time in this order (D-033).
4. **Check coverage:** every acceptance criterion is covered by at least one task, and no task adds scope. An uncovered criterion is a missing task; extra scope is cut or filed as a new work request.
5. **Gate G3.** Show one row per task (`T<k>`, title, slug, the acceptance criteria it covers, what it delivers) and the integration branch name, and ask for the owner's explicit yes. Owner absent: follow **Owner in the loop** in `agentic/rules/factory.md`.
6. **Write the checklist:** a file with one `<slug>: <title> (AC<i>, ...)` line per task, the title ending with the criteria it covers and short enough that its landing subject, `<prefix>(<scope>): <title>` without the criteria, fits 72 characters (`agentic/rules/git.md`); then `factory_issue.py task <n> --plan <file>`.
7. **Push the integration branch** if `git ls-remote origin int/<n>-<slug>` prints nothing: `git fetch origin`, then `git push origin origin/main:refs/heads/int/<n>-<slug>` (`agentic/rules/git.md`).
8. **Move:** `factory_issue.py stage <n> build --reason "G3 approved by the owner."`.

## Output

The task checklist in the Delivery section, the integration branch on GitHub, and the stage moved to `build`. Report a declined gate as blocked, with the owner's open points.

## Constraints

- Never change the Requirement or Spec; a gap goes back to `define` or `spec` with a reason.
- At least two tasks: a requirement that fits one task goes back to `define` to be sized small.

## Done when

- Every acceptance criterion is covered by a task, and the owner approved the task table.
- `factory_issue.py status <n>` shows the tasks, stage `build`, and no problems, and `git ls-remote origin int/<n>-<slug>` prints the branch.
