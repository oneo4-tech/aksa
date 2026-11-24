---
name: {{skill}}
description: Use after writing or changing code or tests, and before calling the work done, to answer the tester's questions in ai-kit/AGENTS.md (from the {{channel}} demo {{folder}}). Checks the work against each rule and reports the evidence for each.
---

# {{skill_title}}

The rules come from `ai-kit/AGENTS.md`, {{link}}/ai-kit.

## Procedure

1. **List the work:** the code and tests written or changed, and the behaviour each test claims to check.
2. **Answer each rule** in one line, with evidence: a command and its output, or a file and line. A rule without an answer means the work is not done.
{{rules}}
3. **Run the helper scripts** in `ai-kit/scripts/`, when there are any, as `python3 ai-kit/scripts/<script>` from the project root.
4. **Fix** what a rule or a script finds, then answer the rules again.
5. **Report** each rule with its answer and evidence, and what you fixed.

## Done when

- Every rule has a one-line answer with evidence.
- Nothing a rule or a script found is left unfixed or unexplained.
