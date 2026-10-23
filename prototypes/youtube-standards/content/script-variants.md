# PROTOTYPE: script structure variants (same topic, long-form 5-10 min)

Shared rules in every variant (from research): the topic is clear within the first 15 seconds and the hook within 5 [YouTube blog, 2011 and 2014]; the Studio "Intro" metric is retention after 30 seconds [YouTube Help 9314415]; each video needs distinct educational value, not a template with new nouns [YPP inauthentic content, 2025-07-15]. Narration pace target 150-165 words per minute, so 5-10 minutes is about 800-1600 words.

## A. Challenge first ("Spot the Bug")

| Beat | Time | Content |
|---|---|---|
| Cold open | 0:00-0:10 | Two green tests on screen. "Both pass. I can break the code in one keystroke and neither notices. Spot the bug." |
| Pause prompt | 0:10-0:25 | Code on screen, "pause and look" with a 10-second visual timer. |
| Context | 0:25-1:00 | The function under test; what correct behaviour is. |
| Reveal 1 | 1:00-2:30 | Bug one: testing the mock. Line focus, explain why it always passes. |
| Reveal 2 | 2:30-3:45 | Bug two: existence check. Three values that all pass. |
| Proof | 3:45-5:00 | Live mutation in the terminal: AI tests pass, real tests fail. |
| Fix | 5:00-6:30 | Rewrite: one behaviour per test, each can fail for one reason. |
| Principle | 6:30-7:15 | "What would make this test fail?" Mutation as the cheapest test of your tests. |
| CTA | 7:15-7:40 | Comment prompt (worst passing test), next challenge teaser. |

Strength: interactive, fits the Spot the Bug pillar, natural Shorts cut points. Risk: repetitive if every video uses it.

## B. Incident story

| Beat | Time | Content |
|---|---|---|
| Cold open | 0:00-0:12 | "A checkout charged customers 10% more for a week. Every test was green." |
| Stakes | 0:12-0:45 | What broke, who noticed, why CI did not. |
| Investigation | 0:45-3:00 | Walk the test suite like a tester: what does each test actually check? |
| Root cause | 3:00-4:30 | The mocked function and the existence assertion. |
| Proof | 4:30-5:30 | Reproduce with a one-character mutation. |
| Fix and guardrail | 5:30-7:00 | Rewritten tests plus a mutation check in CI. |
| Lesson | 7:00-7:40 | The human question AI skipped; CTA. |

Strength: emotional stakes, strong retention. Risk: the incident must be clearly labelled as a constructed scenario unless it is real and cited.

## C. Myth buster

| Beat | Time | Content |
|---|---|---|
| Claim | 0:00-0:10 | "Claim: AI writes great unit tests. Let's test that claim like a tester." |
| Method | 0:10-0:50 | The experiment: ask an assistant for tests, then mutate the code. |
| Run | 0:50-3:30 | Generate, run, mutate, record what survives. |
| Results | 3:30-5:00 | Score card: which mutations the AI tests caught. |
| Why | 5:00-6:30 | Patterns: testing mocks, existence checks, mirrored logic. |
| Verdict | 6:30-7:20 | Nuanced verdict and a checklist the viewer can apply. |
| CTA | 7:20-7:40 | "Which claim should I test next?" |

Strength: evidence-led, very on-brand for "how testers think". Risk: needs a real, reproducible experiment each time.

## Writing rules (proposed for all variants)

- One idea per video; the title promise is answered on screen.
- Every claim is shown on screen (demo, output) or cited in the description.
- Plain words; sentences under 20 words; numbers spoken as people say them.
- No filler or AI-slop phrases: "in today's video", "let's dive in", "game-changer", "delve", "it's important to note", "without further ado", "smash that like button".
- Narration markup: `<short pause>` and ellipses for pauses, CAPS for one stressed word per sentence at most; never `<long pause>` (spoken aloud in testing).
- Each video states its learning outcome in one sentence before scripting.
