---
name: diagnose-bug
description: Use before fixing a bug, when implement-task starts a fix task or a check fails without an obvious cause, or when the owner asks to debug, reproduce, or find the root cause of a defect. Reproduces the bug as a failing regression test at the highest seam, narrows the cause with evidence instead of guesses, and returns the root cause and the smallest fix; the fix itself stays with the caller.
---

# Diagnose bug

## Inputs and prerequisites

- The bug: expected behaviour, actual behaviour, and how to trigger it, from the factory issue's requirement or task line, or the failing check's output. Look for missing detail in the issue, logs, and code first; ask the owner only what cannot be found.
- The worktree of the branch that will carry the fix.
- The test method and seams: `agentic/rules/coding.md`.

## Procedure

1. **State the bug precisely:** input, expected, actual, and where it was seen.
2. **Reproduce it by hand** with the smallest command or input, and record the exact command and output. If it does not reproduce, report what was tried and stop.
3. **Write the regression test** at the highest seam that shows the bug, run it, and watch it fail for the reported reason. This test is the fix's contract.
4. **Narrow the cause with evidence,** one hypothesis at a time, writing down each one and the result that confirmed or ruled it out:
   - Shrink the input until the failure flips.
   - When it used to work, bisect: `git bisect start <bad> <good>`, `git bisect run uv run pytest -q <test file>`, then `git bisect reset`.
   - Trace the path from the seam inward, with temporary prints or assertions that are removed before any commit.
5. **Name the root cause** at `path:line` with why it is wrong, the smallest fix that makes the regression test pass without breaking another test, and any sibling place with the same flaw.
6. **Hand back** to the caller the failing test, the evidence, the root cause, and the proposed fix.

## Output

The failing regression test in the worktree, and a diagnosis: the reproduction command and output, each hypothesis with its result, the root cause at `path:line`, the proposed fix, and sibling places. Report a bug that does not reproduce as blocked, with what was tried.

## Constraints

- Diagnose only: the fix lands through the caller, `implement-task`, behind the regression test (`agentic/rules/coding.md`).
- A cause outside the task's scope is reported, not fixed; it can become a new work request.
- Never present a guess as the cause.

## Done when

- The regression test fails on the current code for the reported reason.
- The root cause is named at `path:line` and backed by evidence: a reproduction, a bisect result, or a traced path.
- No temporary debugging code is left in the worktree.
