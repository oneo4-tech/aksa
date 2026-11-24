# Owner feedback rules

Every common rule the owner gave in YouTube reviews, traced to the pipeline step that applies it and what enforces it. Source: the `YouTube: owner` comments on content issue #38 (Spot the Bug long-form) and its Short #39. `youtube-producer` reads this file at the start of every run and checks each row of the current stage before asking for a gate; each specialist applies its step's rows.

Enforced by: **check**, a script refuses the output (exit 3 or 2) and a test covers it; **checklist**, a person or the producer judges it against the named list, with the style guide section the specialist reads. The style guide is the channel's `style-guide.md`; `channel.yaml` holds the machine values.

## Rules

| # | Owner feedback (review) | Rule for all content | Step | Enforced by |
|---|---|---|---|---|
| 1 | Length from the measured narration (gate 2) | The length estimate uses the measured speed of the channel voice | `write-video-script` | check: `check_script.py` (BASE_WPM, voice.pace) |
| 2 | Paid art only after the owner's yes (packaging) | Paid images are generated only on the owner's explicit yes, cost named first | `design-thumbnail`, `brand-channel` | check: `thumbnail.py` prints cost; `branding.py --backdrop` refuses without `--yes` |
| 3 | Opening narration and title text do not match; needs a better hook (round 1) | The cold open shows the real artifact and says what is on screen; never a title slide | `write-video-script` | check: `check_script.py` (cold open, HOOK_SHARE); checklist: Gate 2 item 1 |
| 4 | End every video with rules, skills, or scripts for the viewer's AI agent (round 1) | Every video, Shorts too, has a kit scene and an `ai-kit/` in the demo folder | `write-video-script`, `build-video-demo` | check: `check_script.py` (kit scene, files in `ai-kit/`); checklist: Gate 2 item 13 |
| 5 | Code highlight band and arrow not aligned (round 1) | Marks and focus bands sit on their code lines | `render-video` | checklist: render-video step 3, Gate 3 item 14 |
| 6 | Thumbnail does not catch the eye (round 1); must challenge, ask, and show AI; no red circle (round 2); grey background (round 3) | 2-4 challenging words, AI shown, red a small accent, grey field | `design-thumbnail` | check: `thumbnail.py` (challenge words, AI cue, markers, `thumbnail.field`); checklist: the skill's 14 points, Gate 3 item 4 |
| 7 | More hashtags for AI and testing (round 1) | 8-15 hashtags, the first three the most important | `package-video` | check: `package.py` (HASHTAGS) |
| 8 | First slide shows the tests and code side by side (round 2) | A code challenge and every Short open on a `split` | `write-video-script` | check: `check_script.py` (split cold open) |
| 9 | Bug reveals highlighted in the code, not text slides (round 2) | Reveals are `marks` on code lines; no points slide of code | `write-video-script`, `render-video` | check: `check_script.py` (code-like points lines, marks cues) |
| 10 | Reduce the music by 30 dB (round 2) | Music bed at `music_db` under the voice | `render-video` | check: `assemble.py` applies `channel.yaml` `music_db`; checklist: Gate 3 item 2 |
| 11 | Comparisons side by side with examples (round 2) | A comparison is a `compare` scene, an example a side | `write-video-script` | check: `check_script.py` (versus heading, two items a side) |
| 12 | A term on screen only after the narrator introduces it (round 2); bug headings appear when called out (round 3) | Heading terms are said first; a heading appears at its first word said | `write-video-script`, `render-video` | check: `check_script.py` (heading terms); `render.py` heading timing; checklist: Gate 3 item 15 |
| 13 | A mutation example shows the mutated code (round 2) | Every code change is shown before and after | `build-video-demo` | checklist: Gate 2 item 14, the demo step prints both lines |
| 14 | Terminal: a blank line between steps (rounds 2 and 3) | One blank line before each comment step, none between a comment and its command | `build-video-demo` | check: `references/demo.tape` setup from `scaffold.py`; checklist: Gate 2 item 15 |
| 15 | Kit shows link, snippet, and takeaways as the narrator talks (round 2) | Each kit element appears at its cue word | `write-video-script`, `render-video` | check: `check_script.py` (cue words); `render.py` cue timing |
| 16 | Description: Code and AI kit on separate lines; References for key concepts only (round 2) | `Code:` and `AI kit:` lines; 2-5 key-concept references from cited pages | `package-video` | check: `package.py` (REFERENCES, cited urls) |
| 17 | Real-world, practical code (round 2) | A realistic service, values in cents, a real collaborator; never a toy | `build-video-demo`, `write-video-script` | checklist: Gate 2 item 15 |
| 18 | Motion graphics, medium, not too much (common) | Medium, purposeful motion timed to the narration | `render-video` | check: `render.py` MOTION and stagger; checklist: Gate 2 item 14 |
| 19 | Introduction first: roles, audience, activity (round 3) | A long-form opens on an `intro` naming roles, activity, and stake | `write-video-script` | check: `check_script.py` (intro) |
| 20 | Context of why before a concept (round 3) | A concept follows a sentence giving its reason | `write-video-script` | check: `check_script.py` (REASON cue); checklist: Gate 2 item 14 |
| 21 | Introduce the AI kit first, with a GitHub graphic (round 3) | A long-form's `repo` card comes before any scene using the kit | `write-video-script` | check: `check_script.py` (repo before kit) |
| 22 | Background: a test lab scene, not the wordmark (round 4; round 3 asked for more opacity) | Slides show a dim test lab backdrop, filling the frame | `brand-channel`, `render-video` | check: `branding.py --backdrop`; `youtube_channel.py` (`background.fit`, opacity at most 0.35 cover, 0.15 contain); `render.py` draws it |
| 23 | Never a blank slide or screen over a second (round 4) | Every scene has a heading and a visual from its first words; no gap over 1 s | `write-video-script`, `render-video` | check: `check_script.py` (heading and visual fields required); `render.py` timing; checklist: producer gate 2 and 3 |
| 24 | Carry every learning into the pipeline (round 4) | This file: every run reads it; new common feedback adds a row | `youtube-producer` | checklist: producer workflow steps 1, 6, and 8 |
| 25 | Kit: same GitHub animation, no repetition, explain each file and its use (round 4) | The kit scene replays the GitHub card with each file's use line; no line repeats an earlier scene | `write-video-script`, `build-video-demo`, `render-video` | check: `check_script.py` (kit files, no repeat, files in `ai-kit/`); `render.py` kit card |
| 26 | Like, share, subscribe, notification graphics before the end (round 4) | A long-form's `cta` scene before the bridge, said naturally; replaced by row 32 (the last scene, after the bridge) | `write-video-script`, `render-video` | check: `check_script.py` (cta place, actions, cue words, banned phrases); `render.py` cta graphics |
| 27 | Description: what the video is about and the takeaways (round 4) | `about` (2-4 sentences) and 3-5 takeaways after the hook | `package-video` | check: `package.py` (ABOUT, TAKEAWAYS) |
| 28 | Short starts abruptly; curiosity in 3 s; flow interest, challenge, why, takeaway, drive to the long video (round 4, #39) | A Short opens on a hook within 3 s, has each beat with a bridging sentence, and drives to the full breakdown | `plan-shorts`, `write-video-script` | check: `check_script.py` (hook, beats, drive, no title slide before the kit); checklist: plan-shorts Done when |
| 29 | Transition well from one slide to another: "now that we have seen..., let us now..." (round 5) | Every scene after the first opens on a sentence bridging from the one before, Shorts too | `write-video-script`, `plan-shorts` | check: `check_script.py` (TRANSITIONS cue in the first sentence of each scene after scene 1); checklist: producer gate 2 and 3 |
| 30 | Always check grammar: "Review code an AI wrote" is incorrect (round 5) | Every on-screen line and narrated sentence is grammatical, natural English; the writer's grammar pass covers every line | `write-video-script`, `plan-shorts` | check: `check_script.py` (doubled words, sentence capitals, dangling line ends, REDUCED relatives); checklist: write-video-script step 5 and its `YouTube: grammar` line, producer gate 2 and 3 |
| 31 | Remove the naming of people in narration (round 5) | Narration never names a person; the description's References credit the concept and its source | `write-video-script`, `package-video` | check: `check_script.py` (`channel.yaml` `narration_avoid_names`, validated by `youtube_channel.py`); checklist: producer gate 2 and 3 |
| 32 | Like, share, subscribe at the end, and shorter (round 5) | A long-form ends on its `cta` after the bridge, at most two sentences and about 8 s; a Short's cta, if any, last and about 4 s | `write-video-script`, `plan-shorts` | check: `check_script.py` (cta last, CTA_SENTENCES, CTA_SECONDS); checklist: producer gate 2 and 3 |

`scan-video-ideas`, `research-video`, and `narrate-video` have no owner feedback rows yet; they keep their own checks and the Gate 1 and Gate 2 lists.

## Adding a row

- At a gate, feedback the owner calls a common rule ("for all content") becomes a row: the feedback, the rule, the step, and how it is enforced.
- The producer proposes the row and the component change it needs in the retrospective (workflow step 8), filed on the owner's yes as a work request; this file and the components change only through the factory (D-038).
- A rule replaced by a later review keeps its row, naming the newer rule, as rows 15, 22, and 26 do.
