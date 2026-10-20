# Review of task T<k> of #<n>

You review one change of a Software Factory run, on your own. You get artifacts only, never the implementer's reasoning. Change no file and no issue; reply with the report below.

- Factory issue: `gh issue view <n>`. Read its Requirement, its Spec if any, and task line T<k>, whose title ends with the acceptance criteria it covers: <criteria>.
- Change: `git diff <base>...<head>`, in a checkout that has both.
- Rules: `AGENTS.md`, `agentic/rules/coding.md`, `agentic/rules/git.md`, any rule the change touches, and the active decisions in `agentic/memory/decisions.md`.
- Component reviews already done, not to repeat: <review-component results, or none>.
- Mode: <full, or confirm with the findings to check: F<i>, ...>.

## What to check

1. Each covered criterion: is it met? Name the evidence: a test that checks it (`<path>::<name>`) and passes when you run `uv run pytest -q <path>`, or the component's `review-component` pass.
2. Broken rules: a line in the change that breaks a rule or an active decision, quoting the rule or decision.
3. Defects: wrong behaviour you reproduce, with the command and its output.

In confirm mode, check only the listed findings and the diff made since the full review.

## Findings

- **Blocking**, only with evidence: an unmet criterion, a quoted rule or decision the change breaks, or a reproduced defect.
- **Note**, for everything else: names, style the linters do not enforce, possible improvements, and code outside the change. Notes are never fixed in this run.
- Never report what the checks already enforce: ruff, pytest, and the repository tests.

## Report

### T<k> of #<n> at <head>: <pass | blocking findings>

| Criterion | Met | Evidence |
|---|---|---|
| AC<i> | <yes or no> | <test and result, or review-component pass> |

#### Findings

- **F1** (<blocking | note>) <what>, at `<path>:<line>`. Evidence: <quoted rule, unmet criterion, or command and output>.

With no findings, write "No findings." under the heading.
