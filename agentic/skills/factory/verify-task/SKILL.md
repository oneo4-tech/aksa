---
name: verify-task
description: Use after implement-task finishes a task of a factory run in stage build, or when the owner asks to verify or review a task's change. Starts one independent reviewer on the task's diff against its acceptance criteria and the rules, posts the report on the factory issue, sends blocking findings back for one fix and one confirm pass, and on a pass lands the task on the delivery branch and ticks it.
---

# Verify task

## Inputs and prerequisites

- The factory issue in stage `build` and its task (`next_task` in `uv run agentic/scripts/factory_issue.py status <n>`), with the pushed branch, head commit, evidence, and `review-component` results from `implement-task`.
- The reviewer brief: `references/reviewer-brief.md` in this skill's folder.
- Runs in the main session, because it starts a sub-agent.

## Procedure

1. **Fix the scope:** the task branch's diff against its base at the head commit: `origin/int/<n>-<slug>...<head>` for a task, `origin/main...<head>` for a small run. The contract is the criteria the task covers and the rules, nothing else.
2. **Review once:** fill `references/reviewer-brief.md` with the issue, task, base, head, criteria, and `review-component` results, in full mode, and give it to a fresh sub-agent, or a fresh session where the vendor has none. Add nothing of your own: no summary of the code and no opinion.
3. **Post the report** unchanged as a comment on the factory issue, starting `Factory: verify T<k>`.
4. **Blocking findings** go to `implement-task` fix mode. Then run one confirm pass, the same brief in confirm mode for those findings, and post its result. A finding still blocking: post it with the options (fix, accept, or a new work request), follow **Owner in the loop** in `agentic/rules/factory.md`, and stop.
5. **Land on a pass,** with no blocking finding left:
   - Large run: from the run's worktree, land the task as `agentic/rules/git.md` describes. If the run has no pull request yet, open its draft as `agentic/rules/git.md` describes and `factory_issue.py set <n> --pr <pr>`. Then `factory_issue.py task <n> --done T<k>`, and delete the task's branch; the worktree stays for the next task.
   - Small run: nothing to land; the change is already on its delivery branch.
   - Both: add the task's `review-component` results to the pull request's review-component section.
6. **Move on** after a large run's last task or a small run's pass: `factory_issue.py stage <n> ship --reason "Every task verified and landed."`.

## Output

The report and any confirm result on the factory issue, and the task landed and ticked, with the stage at `ship` after the last task or a small run's pass; or blocked, with the owner's decision needed. Report a reviewer that could not run as blocked, never as a pass.

## Constraints

- One full review and at most one confirm pass per task (D-032). Notes are never fixed in the run and never raised again; at ship the owner may turn them into new work requests.
- The reviewer sees artifacts only: the factory issue, the diff, and the rules, never the implementer's reasoning. `review-component` results are inputs, not repeated.
- Only this skill lands a task on an integration branch (D-028).

## Done when

- The report covers every criterion the task covers, each with evidence, and every finding is marked blocking or note.
- No blocking finding is open, or the owner decided each one.
- On a pass, a large run's task is ticked and its squash commit is on the integration branch; after the last task, or a small run's pass, the stage is `ship`.
