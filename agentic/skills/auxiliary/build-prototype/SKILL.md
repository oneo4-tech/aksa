---
name: build-prototype
description: Use when the owner asks to prototype, spike, mock up, try out, or compare options for a state machine, data model, API shape, or page layout before writing real code. Builds throwaway code that answers one design question by clicking, as one logic file or switchable UI variants, on a never-merged prototype branch, and records the owner's verdict.
---

# Build prototype

## Inputs and prerequisites

- Scope: the aksa repository only. A design question about another repository is out of scope; say so and stop.
- The design question, from the request. If talking can settle it, or it is factual (use `research-topic`), say so and stop.
- A name: lowercase hyphenated, a few words; propose one.
- Whether aksa has a frontend; the UI branch needs one, so without it only the logic branch applies.
- Guides and templates in this skill's folder: `references/logic.md`, `references/ui.md`, `references/logic-template.html`, `references/verdict-template.md`.

## Procedure

1. **Pick the branch.** Logic for state, transitions, or data; UI for look or layout. Show the owner the pick, the name, and the question, and continue after they agree. When the owner is not present, proceed and list the pick under "Decisions for the owner" (`AGENTS.md`).
2. **State the question** in one paragraph, in agreed terms (`agentic/memory/vocabulary.md`). It shows at the top of the prototype, not only in a comment. If it conflicts with an active decision in `agentic/memory/decisions.md`, tell the owner now.
3. **Create the prototype branch.** Run `git fetch origin`, then `git ls-remote origin "prototype/<name>"`. If it exists, ask the owner for a new name or to continue on it. Otherwise run `uv run agentic/scripts/new_worktree.py prototype/<name> origin/main`, and work in `.worktrees/prototype-<name>` through `git -C`.
4. **Build it.**
   - Logic: follow `references/logic.md`; fill `references/logic-template.html` into `prototypes/<name>/index.html` in the worktree.
   - UI: follow `references/ui.md`, building the variants in aksa's frontend inside the worktree.
5. **Hand it over.** Give the owner the file to open (logic) or the run command, URL, and variant keys (UI), and what to click. Change the prototype on their feedback until they say the question is answered.
6. **Capture.**
   - Commit the prototype: `prototype(<name>): <question in a few words>`.
   - Fill `references/verdict-template.md` into `prototypes/<name>/verdict.md`, show it to the owner, and commit it: `prototype(<name>): add verdict`.
   - After the owner confirms, push: `git -C .worktrees/prototype-<name> push -u origin prototype/<name>`. Open no pull request.
   - If the answer decides something about aksa, propose it as a decision through `add-memory`, with the branch as its source.

## Output

The branch `prototype/<name>` with the prototype and `prototypes/<name>/verdict.md`, and a reply with the branch, how to run it, and the answer. Report a prototype the owner could not run, or a question left unanswered, as blocked with the reason.

## Constraints

- Throwaway and marked: names, the page title, and a banner say `PROTOTYPE`.
- Trivial to run: logic opens with a double-click; UI starts with one command.
- No persistence unless persistence is the question; then use a scratch store named `PROTOTYPE, wipe me`.
- No polish: no tests, no error handling beyond running, no abstractions.
- Show the full relevant state after every action or variant switch.
- Never merge the prototype branch or copy its code. The decision reaches real code rewritten, with tests.
- Never silently override an active decision; a conflict goes to the owner.

## Done when

- Logic: `index.html` is one self-contained file with no external scripts, styles, or network use; its title and banner say `PROTOTYPE`; the question is visible on the page; and `<script id="module">` uses no DOM, storage, or network.
- UI: 3 to 5 structurally different variants switch through `?variant=`, and the switcher is hidden in production builds.
- `verdict.md` has the Prototype, Question, Answer, and Why lines filled, and no placeholder or em dash remains.
- The owner said the question is answered and confirmed the push; `git ls-remote origin prototype/<name>` prints the branch and `gh pr list --head prototype/<name>` prints nothing.
