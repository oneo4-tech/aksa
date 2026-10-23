# PROTOTYPE: revised writing rules (owner's draft + review)

## Core focus

- **One idea per video.** The whole video serves one concept.
- **Learning outcome first.** Write the outcome in one sentence before scripting; every beat must serve it.
- **Problem in the first 5 seconds.** Every structure (challenge, incident, myth) opens on the failing case or painful problem, not on an intro. Topic clear by 15 seconds.
- **Title promise kept, at the climax.** The title's promise is answered on screen, in the payoff beat (middle to late), not in the first 30 seconds.
- **Next-step bridge.** End by pointing to the next video or challenge, plus one specific comment question; never a generic like or subscribe request.

## Proof

- **Shown, not told.** Every claim is shown on screen (demo, output, animation) or cited in the description.
- **A visual change every 2-3 sentences** (about every 10 seconds): highlight, zoom, typed code, run output, callout, or image.
- **Sources listed** in the description for anything not demonstrated.

## Style and vocabulary

- Plain words; every sentence under 20 words.
- **Rhythm:** mix very short sentences (3-5 words) with medium ones (12-15 words); never three long sentences in a row.
- **Numbers as spoken:** write "ninety", "fifteen hundred", "ten percent"; code values stay as code on screen.
- **Pronunciation list:** respell jargon in the narration text when the voice gets it wrong (owner's pick: respelled), kept per channel.

## Narration markup (Gemini 3.8 TTS)

- Delivery and pace go in the style field (Puck, warm, played at 0.92), never in the script text.
- Pauses: `<short pause>`, `<long pause>`, and ellipses are the documented tags. Measured pauses: ellipsis about 0.5-0.8 s, `<short pause>` about 1.1-1.4 s, `<long pause>` about 1.8-2.3 s.
- `[pause]` and `//` also paused in testing but are undocumented; do not use them. (The draft's claim that `<short pause>` was spoken aloud is not what was tested: `<long pause>` leaked once in 4 earlier runs and 0 of 1 later.)
- **Leak check:** the narration transcript (whisper) must match the script words; any spoken tag fails gate 3.
- CAPS for at most one stressed word per sentence.

## Banned phrases (AI slop and filler)

in today's video, let's dive in, dive deep, deep dive, game-changer, game changing, delve, it's important to note, it's worth noting, without further ado, smash that like button, make sure to subscribe, hey guys, testament to, unveil, unleash, unlock, harness, elevate, revolutionise, revolutionize, supercharge, level up, more than just, in this fast-paced world, ever-evolving, ever-changing landscape, navigate the complexities, seamless, robust, cutting-edge, leverage (as a verb), embark, journey, tapestry, realm, paradigm shift, at the end of the day, buckle up, stay tuned, let's get started, so without wasting time, that being said, in conclusion, look no further.

The agent checks every script against this list (case-insensitive) before gate 2.
