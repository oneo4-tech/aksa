# Logic branch

Read this in step 4 when the question is about state, transitions or data.

## When

- "Does this state machine handle X to Y?"
- "Can this data model represent ...?"
- "Feel out the API before writing it."

## Build

1. **Question visible at the top.** The `#question` section of `references/logic-template.html`, in agreed terms.
2. **Pure module** in `<script id="module">`. Pick one shape:
   - **Reducer:** `step(state, action)` returns the next state. Default in the template.
   - **State machine:** a table of states, events and allowed transitions.
   - **Pure functions:** plain functions over plain data, for data model questions.
   - **Class:** an object with methods, when the question is the API surface itself.

   No DOM: no `document`, no `window`, no button handlers. A forbidden action returns an error and leaves the state unchanged, so the page can show the refusal.
3. **Page around the module** in `<script id="page">`, in this order:
   - Title, marked `PROTOTYPE`.
   - Current state panel: readable, re-rendered after every action. Replace the JSON dump with labelled fields if JSON hides the answer.
   - Free-play buttons: one per action, plus reset.
   - Scenario tabs: at least normal path, edge case and forbidden attempt. Each tab resets to a known initial state, then steps one action per click.
4. **One file**, double-clickable. No framework, no bundler, no server, no external scripts or styles.

## Rule

Keep the logic and the page apart. If the module touches the DOM, storage, or the network, it cannot be lifted out.
