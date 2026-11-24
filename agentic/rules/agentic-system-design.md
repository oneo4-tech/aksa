# Agentic system design

Read when designing or reviewing an agentic component: choosing its kind, an agent's loop, how its work is verified, which memory it uses, and whether it needs an agent eval. This is design guidance (D-044); `agentic/rules/components.md` stays the single standard that `review-component` checks (D-014). Kinds are defined in `agentic/memory/vocabulary.md` (D-008).

## Choosing the kind

- "Always" or "never": a Rule. It constrains behaviour across tasks and never holds a procedure.
- "When asked to X, do these steps": a Skill. It produces an output for its caller and never owns an outcome.
- "You are responsible for X": an Agent. It owns an outcome and invokes rules and skills by path instead of restating them.
- Durable context about aksa is Memory; domain knowledge goes to the Knowledge Base (D-015). Placement follows `agentic/rules/components.md`.

## The RALPH loop

An agent works in a RALPH loop until every acceptance criterion is met or it stops for the owner:

| Phase | The agent |
|---|---|
| Receive and reason | Takes the goal, context, and constraints; finds the rules and skills that apply, by path. |
| Act | Runs one skill or deterministic step and produces an artifact: a diff, test, note, or pull request. |
| Learn | Checks the result against the acceptance criteria and notes what deviated. |
| Plan | Chooses the next step: continue, retry with a change, hand off for review, or ask the owner. |
| Handle | On a failure or blocking finding, finds the root cause with evidence and proposes the fix, or escalates. |

- Reason before acting; check each result before planning the next step.
- Existing agents already loop this way through their workflow steps; naming the phases is not required.

## Verification

- Automated checks (`uv run pytest`, `ruff check`, `ruff format --check`, CI) run on every change.
- Each factory task is verified once by an independent reviewer before it lands (D-032), through `verify-task`.
- A reviewer reports findings with evidence and never rewrites the author's work; a blocking finding gets one fix and one confirm pass, then goes to the owner (D-032).
- Owner approvals stay where `agentic/rules/factory.md` and `agentic/rules/knowledge.md` place them: gates, the merge into `main`, Memory changes, and Knowledge Base reviews.

## Memory boundaries

The tiers, their skills, and the Knowledge Base layout are in `agentic/rules/knowledge.md` (D-015, D-017).

| Question | Look in |
|---|---|
| A repository convention, such as skill naming | `agentic/rules/` |
| Whether a decision or term is agreed | `agentic/memory/` through `get-memory` |
| A domain fact, such as what a client's project needs | `.kb/wiki/` through `get-kb` |
| The source behind a cited fact | `.kb/raw/`, only to verify the citation |

- Read Memory for how aksa works, then the Knowledge Base for domain evidence.
- Generated outputs never become trusted knowledge on their own; reusable content returns through `add-kb` and `review-kb`.

## Agent evals

An agent eval is a versioned set of real tasks with owner-labeled expected results, run on an agent or skill to catch regressions.

- Consider one before an agent runs unattended, when another component consumes a skill's output, or when a blocking finding shows a systemic weakness.
- The owner or a named domain expert labels the dataset, never the agent under test (D-045).
- Version the dataset with the agent or skill it tests, re-run it on every change to them, and record results on the factory issue or pull request.

## Design questions

Settle these while designing; acceptance is still `review-component` against `agentic/rules/components.md`.

- Kind: does the component have exactly one kind, and does a rule hold only constraints, a skill only a procedure, an agent only an outcome?
- Reuse: does it link existing rules, skills, scripts, and decisions instead of restating them?
- Loop: for an agent, where does it stop for the owner, and how does it handle a failure?
- Verification: which automated checks cover it, and which owner approvals apply?
- Memory: does it read Memory for conventions and the Knowledge Base wiki for domain facts, and never trust `inbox/`, `raw/`, or `outputs/` content as knowledge?
- Evals: does it need an agent eval before running unattended?
- Portability: is it vendor-neutral (D-004), with vendor adaptation left to `sync_vendors.py`?
