# Coding

Read before writing, changing, or reviewing code or tests. Components follow `agentic/rules/components.md` instead, and simplicity and scope rules are in `AGENTS.md`.

## Test first

Build one behaviour at a time:

1. **Red.** Write one test for the next behaviour from the acceptance criteria. Run it and watch it fail for the expected reason; a test that passes before the code exists tests nothing.
2. **Green.** Write the least code that passes it, and run that test.
3. **Refactor.** Clean names and structure with the test green, and run it again.
4. Repeat until every acceptance criterion has a test. The pre-commit hook runs the full checks on every commit.

A fix starts with a regression test that reproduces the bug (`diagnose-bug`); the fix lands behind it.

## Seams

- Test through a seam (`agentic/memory/vocabulary.md`): existing seams first, as high as possible, as few as possible. One test through a public entry point beats several tests of private helpers.
- Never test past the seam, such as a private helper the seam already covers.
- The seam for each acceptance criterion is agreed at G1 for a small run or G2 for a large run; a criterion without one goes to the owner (`agentic/rules/factory.md`).

## Good tests

- Check behaviour, not implementation, so they survive a refactor that keeps behaviour.
- Named for the behaviour, such as `test_claim_refuses_an_issue_held_by_another_session`.
- One reason to fail: arrange, act, assert. Use `pytest.mark.parametrize` for cases of one behaviour.
- Fast, isolated, and deterministic: no network, GitHub, or real clock. Pass data in, and fake only the thin I/O layer at its boundary.
- In `tests/test_<script>.py` for a script.

## Code

- Pure core, thin shell: logic that decides lives in functions without I/O; GitHub, git, file, and clock access stays in a thin layer that gathers inputs and applies results.
- Errors are explicit: catch only the exceptions you expect, and say what failed and how to fix it.
- New scripts exit 0 when done, 1 on an error, 2 on bad input, and 3 when refused and the owner is needed.
- Read settings from `config/` instead of copying their values (D-013).
- Standard library first; a new dependency needs a reason in the pull request and `uv add`.

## Never

- Weaken, skip, or delete a test to get to green; fix the code.
- Skip a test without a linked issue, or leave a check failing.
