# PROTOTYPE: packaging metadata variants

Limits (YouTube Help): title 100 characters, description 5,000; chapters need a first timestamp 00:00, at least three ascending timestamps, each chapter 10 seconds or longer; more than 60 hashtags and all are ignored; up to three description hashtags show above the title. Tags play a minimal role in discovery.

## Title styles (proposed limit: 60 characters so it is not cut on mobile)

| Style | Example | Chars |
|---|---|---|
| A. Challenge | Spot the Bug: This AI Test Passes and Tests Nothing | 51 |
| B. Statement | I Broke the Code. The AI's Tests Stayed Green. | 46 |
| C. Question | Can AI Write Unit Tests? I Mutated the Code to Find Out | 55 |

## Description templates

### D1. Short

> Two AI-written unit tests pass, and neither can fail. One-character mutation proves it.
>
> 0:00 Two green tests
> 0:25 The code
> 1:00 Testing the mock
> 2:30 Testing existence
> 3:45 Break the code
> 5:00 The tester's version
>
> #softwaretesting #ai #pytest

### D2. Structured

> **What you'll learn:** how to tell whether an AI-written test can actually fail, and the one-character check that proves it.
>
> **Chapters**
> 0:00 Two green tests / 0:25 The code / 1:00 Bug one: testing the mock / 2:30 Bug two: testing existence / 3:45 Break the code / 5:00 The tester's version / 6:30 The question AI skipped
>
> **Code:** <link to the demo repository>
> **Sources:** Python unittest.mock docs (patch.object); mutation testing docs
>
> **Disclosure:** narration uses a synthetic AI voice. No paid promotion.
> **Music:** <Audio Library credit when the licence asks for it>
>
> #softwaretesting #ai #pytest

## Tags policy

- T1. 5-8 tags: topic, tools, pillar (minimal discovery value per YouTube).
- T2. None; rely on title, description, and hashtags.

## Disclosure wording (per YouTube policy)

- Altered or synthetic content setting: "No" when only the narration voice is synthetic and no real person is imitated; "Yes" if a realistic person or event is depicted. A 2024 YouTube announcement lists synthetically generating a person's voice to narrate as needing disclosure, so the description always states the synthetic voice.
- Paid promotion: Studio checkbox whenever there is a sponsor, plus a spoken and on-screen mention.
