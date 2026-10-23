# PROTOTYPE: citation dossier, idea 2 "Playwright's Healer Fixed My Test. It Also Hid the Bug."

Every claim the video makes is listed with its source, the exact quote, the date checked, and a status. The owner reviews this file at gate 2; nothing marked "needs demo" or "adjust" may stay in the script unproven.

Checked: 2026-10-23.

## Sources

- [S1] Playwright docs, Test Agents: https://playwright.dev/docs/test-agents (page version not stated)
- [S2] Playwright release notes v1.56.0, published 2025-10-06: https://github.com/microsoft/playwright/releases/tag/v1.56.0
- [S3] Michael Bolton, "Oracles Are About Problems, Not Correctness", 2015-03-12, updated 2023-08-11: https://developsense.com/blog/2015/03/oracles-are-about-problems-not-correctness
- [S4] James Bach and Michael Bolton, "Testing and Checking Refined", updated 2024-08-10: https://www.satisfice.com/blog/archives/856

## Claims

| # | Script claim | Source and exact quote | Status |
|---|---|---|---|
| C1 | Playwright ships three test agents: planner, generator, healer. | S1: "Playwright comes with three Playwright Test Agents out of the box: planner, generator and healer." | Verified |
| C2 | They arrived in Playwright 1.56 in October 2025. | S2: "Introducing Playwright Agents, three custom agent definitions designed to guide LLMs through the core process of building a Playwright test" (v1.56.0, 2025-10-06) | Verified |
| C3 | The healer runs the suite and repairs failing tests automatically. | S1: "healer executes the test suite and automatically repairs failing tests" | Verified |
| C4 | It patches locators, waits, or data, and re-runs until the test passes. | S1: "Suggests a patch (e.g., locator update, wait adjustment, data fix)" and "Re-runs the test until it passes or until guardrails stop the loop" | Verified |
| C5 | If it thinks the feature is broken, it skips the test instead of passing it. | S1: "Output: A passing test, or a skipped test if the healer believes that functionality is broken." | Verified; must be said in the video (fairness) |
| C6 | "It also hid the bug" (title). | No source; depends on the healer judging a real product bug as a locator or data drift. | Needs demo: run the healer against an app change that is a real bug; keep the title only if the recorded run shows it passing. Otherwise retitle: "When Should a Healer NOT Heal Your Test?" |
| C7 | An oracle is how we recognise a problem. | S3: "an oracle is a means by which we recognize a problem when we encounter one in testing" | Verified; credit Michael Bolton |
| C8 | A healed check verifies the new behaviour, not the intended one. | S4: "Checking is the mechanistic process of verifying propositions about the product." | Interpretation: phrase with safety language ("in this run, the repaired check verified...") |
| C9 | Agent definitions must be regenerated when Playwright updates. | S1: "These definitions should be regenerated whenever Playwright is updated to pick up new tools and instructions." | Verified |

## Description citations (auto-generated from the table)

Sources: Playwright Test Agents docs (playwright.dev/docs/test-agents); Playwright v1.56.0 release notes; Michael Bolton, "Oracles Are About Problems, Not Correctness" (developsense.com); James Bach and Michael Bolton, "Testing and Checking Refined" (satisfice.com). RST concepts by James Bach and Michael Bolton; explained in our own words, no endorsement implied.

## Competitive research

Blocked: the `.env` cloud key is not a standard API key, so YouTube Data API calls return 401. With a standard key the agent adds the 10 closest videos (views, views per day, length, date) and the gap they leave.
