---
name: run-factory
description: Use when the owner gives a software work request to build, fix, or change something, names an issue to work on, asks to continue factory work, or asks what is waiting on them. Starts or resumes a Software Factory run as the factory-orchestrator agent, or shows the queue of runs.
---

# Run factory

## Inputs and prerequisites

- The owner's argument, verbatim: plain text, `#<n>`, or nothing.
- The agent: `agentic/agents/factory-orchestrator.md`.
- `gh` signed in to the repository. If `gh auth status` fails, ask the owner to sign in and stop.

## Procedure

1. Read `agentic/agents/factory-orchestrator.md`.
2. Act as that agent for the rest of the session, passing it the argument.

## Output

The agent's output: what the run did and what it now waits for, or the queue.

## Constraints

- A launcher only: the agent owns input handling, routing, and stopping (D-027).
- Run in the main session, never in a sub-agent.

## Done when

- The session acted as the agent and reported the agent's output.
