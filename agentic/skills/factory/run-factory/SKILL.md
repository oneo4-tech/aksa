---
name: run-factory
description: Use when the owner explicitly asks to change tracked software, names a factory issue to resume, or directly asks to start, view, or continue a factory run or queue. Read-only analysis, explanations, and temporary deliverables are not Software Work Requests and must not start intake or create an issue. Starts or resumes a Software Factory run as the factory-orchestrator agent, or shows the open-run queue.
---

# Run factory

## Inputs and prerequisites

- The owner's argument, verbatim: plain text, `#<n>`, or nothing.
- The agent: `agentic/agents/factory-orchestrator.md`.
- `gh` signed in to the repository. If `gh auth status` fails, ask the owner to sign in and stop.

## Procedure

1. Check intent before intake. Start or resume a run only for an explicit request to change tracked code or components, a direct request to start a factory run, an issue named for work, or a direct request to view or continue the factory queue. Read-only analysis, explanations, and temporary deliverables are not Software Work Requests; answer them without starting intake or creating an issue.
2. Read `agentic/agents/factory-orchestrator.md`.
3. Act as that agent for the rest of the session, passing it the argument.

## Output

The agent's output: what the run did and what it now waits for, or the queue of open runs.

## Constraints

- A launcher only: the agent owns input handling, routing, and stopping (D-027).
- Run in the main session, never in a sub-agent.

## Done when

- The session acted as the agent and reported the agent's output.
