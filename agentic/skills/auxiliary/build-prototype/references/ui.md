# UI branch

Read this in step 4 when the question is about look or layout. Only when the project has a frontend.

## When

- "What should this page look like?"
- "Show options for the dashboard before committing."

## Where variants live

- **Existing page (preferred):** add `?variant=` to the existing route. The real header, nav and data stay.
- **New page (last resort):** a throwaway route with `prototype` in its path.

## Build

1. **Question and variant count at the top** of the page. Default 3 variants, max 5.
2. **Structurally different variants:** layout, hierarchy, main action. Not just colour or wording.
3. **Switcher on the route:** read the variant from the URL, render the matching variant, show the switcher bar at the bottom.
4. **Switcher bar:**
   - Arrows and a label, for example `B (Sidebar layout)`.
   - Cycles and wraps; left and right arrow keys switch too.
   - Visually distinct from the page.
   - Hidden in production builds.
5. **Hand over** the run command, the URL and the variant keys. Feedback can mix variants, for example "header from B with sidebar from C".
6. **Capture:** the verdict records the winner and why. All variants and the switcher stay on the prototype branch only. The winner is rewritten properly in real code, with tests and error handling.

## Rules

- Variants that differ only in colour or wording are tweaks, not a prototype.
- Share little code between variants. A shared header is fine; a shared layout defeats the point.
- Anything that writes data is stubbed. Reading real data is fine.
- Rewrite the winner when folding it in. Variant code has no tests and no error handling.
