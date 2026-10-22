# PROTOTYPE packaging: Spot the Bug, AI test that tests nothing

## Research and citations

- `unittest.mock.patch.object` replaces an attribute for the duration of the `with` block, so calling it calls the mock (Python docs, unittest.mock, "patch.object").
- Mutation testing judges a test suite by whether it fails when the code is deliberately changed (mutmut and PIT project docs). Demo run: `demo/mutate.sh`, 2 AI tests pass on mutated code, 2 of 4 real tests fail.
- Claims in the script are shown, not asserted: every result on screen comes from `demo/mutate.sh`.

## Long-form metadata

- Title A: Spot the Bug: This AI Test Passes and Tests Nothing
- Title B: I Broke the Code. The AI's Tests Stayed Green.
- Description: Two AI-written unit tests pass, and neither can fail. We find why (testing the mock, testing existence), prove it with a one-character mutation, and rewrite them the way a tester would. Code: <repo link>.
  Chapters: 0:00 Two green tests / 0:25 The code / 0:45 Your turn to spot it / 1:00 Bug one: testing the mock / 1:30 Bug two: testing existence / 1:55 Break the code / 2:30 The tester's version / 3:00 The question AI skipped / 3:30 Your turn
- Tags: unit testing, AI generated tests, mocking, mutation testing, pytest, software testing, QA
- Disclosure: AI narration (synthetic voice, not cloned) to be checked against YouTube altered/synthetic content guidance; no paid promotion.

## Shorts plan (from the long-form)

1. Short 1 (built): "This AI test passes. Watch it test nothing." Scenes: mock bug, mutation result, the one question.
2. Short 2 (planned): "assert is not None is not a test": bug two only, 3 values that all pass.
3. Hashtags: #softwaretesting #AI #pytest #shorts

## Thumbnail brief

Split screen: green "2 PASSED" badge left, red bug icon right; text "TESTS NOTHING"; max 3 words; high contrast; readable at 160px wide.
