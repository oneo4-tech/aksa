# Script structures

Three structures for a long-form video (five to ten minutes), and one for a Short (thirty to sixty seconds). Times are shares of a long-form video of about seven and a half minutes; scale them to the length the research supports. Every long-form opens on an intro of who it is for and what the viewer will do; every structure then opens on the problem within five seconds, makes the topic clear by fifteen, gives each concept its reason before it, answers the title's promise at the climax, hands the viewer's AI agent the video's kit in a "Take it to your agent" beat that says what the agent then does for them, bridges to the next step with one comment question, (a long-form) ends on a short like, share, subscribe, and notification cta, and every video ends by thanking the viewer. Every scene after the first opens on a sentence bridging from the one before, every line on screen and every narrated sentence is grammatical English, and narration never names a person. Everything on screen enters when the narrator reaches it, never before, no screen is ever blank for more than a second, and no text sits over other text or code.

## The intro (every long-form; never a Short)

- **Scene 1 is an `intro` scene,** before the cold open: the `heading` (such as "Is this challenge for you?"), two or three `roles` lines naming who the video is for (such as "Developers who let AI write their tests", "Testers who review AI-written code"), the `activity`, one line of what the viewer will do (such as "Spot the bug in two AI-written unit tests"), and the `stake`, one line of why it matters (such as "They pass in CI, and would still pass if checkout overcharged").
- **Create interest:** `say` asks the audience a question they recognise, names each role and the activity in plain words, and ends on the stake, such as "Do you let an AI assistant write your unit tests? ... Today you spot the bug in two AI-written unit tests."
- **[checked]** a long-form whose scene 1 is not an `intro`, an intro elsewhere or in a Short, and an intro whose `say` shares no key word with a `roles` line or the `activity`; the interest it creates is judged at gate 2.
- A Short has no intro: its first three seconds are the split's hook, a curiosity line (see "Short").

## The cold open (every structure, Shorts too)

- **Show the real artifact:** right after a long-form's intro (scene 2), or as a Short's first scene, a code challenge (`challenge-first`, and every Short) opens on a `split` scene, the code under test on the left and its tests on the right, so the viewer has both and can find the bug; an incident story or myth buster may open on a `code`, `terminal`, or `points` scene with the code, output, or failing case. Never a title slide or an abstract slogan such as "Zero protection".
- **Screen and voice agree:** the on-screen text says what the narration says at that moment; the viewer never reads one thing and hears another.
- **A concrete stake first:** the first sentence (in a Short, the one after its hook) says, in plain words, what breaks and who pays, such as "Here, this discount code charges customers more, and both tests stay green."
- **An explicit challenge:** say what the viewer must do, such as "Find the line that lets this bug through."
- `check_script.py` refuses a code challenge or Short whose cold open is not `split`, a `title` cold open, and a `points` or `terminal` cold open whose `visual` words are mostly not in its `say`; the stake and the challenge are judged at gate 2.

## Scene rules (every structure, Shorts too)

`check_script.py` refuses each rule marked **[checked]**; gate 2 judges the rest.

- **Reveal in the code:** a reveal about code is a `code` or `split` scene with `marks` on the lines it names, each with a short `note` (it sits in free space beside its line, so a short line and a short note fit, on a Short's narrow code too) and the `at` word of `say` where it lights up; never a `points` slide quoting code **[checked]**: a points line with a bracket, `=`, a backtick, or a dot between identifiers.
- **Compare side by side:** a comparison (a heading with "versus" or "vs" **[checked]**, or narration comparing two named things) is a `compare` scene: each side a heading and items, first what it is, then at least one example **[checked: two items a side]**, such as a check `assert total_cents == 1080` against the test question "what if the tax client times out?".
- **The reason before the concept:** before a concept (a comparison such as checking versus testing, or a new term such as mutation testing), say why the video needs it, in the concept scene's first sentence or the previous scene's last, such as "So why do these tests pass when they prove nothing?" or "So how do we know, quickly, whether a test can fail?" **[checked: a `compare` scene, and a `points` scene whose heading is a bare term of one to four words with a word not said before, needs a reason cue (why, so, because, to know, how do we, how can) in that sentence]**. Other headings, such as a code scene's "Bug two: it checks the type", name what is shown and need no reason; gate 2 judges the rest.
- **The narrator names a term first:** each heading term is said in that scene's `say` or earlier **[checked]**, and the renderer shows the heading from its leading key word as the narrator says it; a term such as "mutation testing" never reaches the screen before the voice introduces it.
- **Show what changed:** a step that changes the code, such as a mutation, shows the line before and after (the demo prints both, or a `code` scene marks the mutated line); the viewer never hears about a change they cannot see.
- **Real-world examples:** code, values, and examples are what a viewer would ship: a checkout, coupon, pricing, or payment service, prices in integer cents with a currency, a tax or payment client worth mocking; never a toy function such as `add(a, b)`.
- **Cue words:** every `at` (a mark's, a kit file's), `link_at`, and `takeaways_at` is a word of the scene's `say` **[checked]**.
- **Bridge every scene:** each scene after the first opens its `say` with a sentence that links back to the scene before or points ahead, such as "Now that we have seen the bug, let us look at the fix." or "So why does this matter?"; it also names what the new scene shows, so the screen is never blank **[checked: the first sentence of every scene after scene 1, Shorts too, has a transition cue: now that, now, next, so, but, here, with that, let us, let's, we have seen, first, then, finally, one more, before, after, also, because, instead, or again]**; whether the bridge truly links the two scenes is judged at gate 2.
- **Grammatical, natural English:** every on-screen line (heading, visual lines, split labels, mark notes, roles, activity, stake, compare headings and items, kit use lines, takeaways, the cta heading) and every narrated sentence is a grammatical English phrase or sentence: full noun phrases with the articles English needs, no reduced relative clause such as "Review code an AI wrote" (write "Review code written by AI"), and no telegraphic fragment except a short label such as "The tests". The writer reads every line in a grammar pass before running `check_script.py` (`SKILL.md` step 5) **[checked, conservatively: a doubled word such as "the the"; a narrated sentence not starting with a capital letter; an on-screen line ending on an article, conjunction, "of", or a possessive; and the reduced relative "<code noun> a(n) <noun> wrote, made, built, generated, or created"]**; everything else, such as a missing article or an unnatural phrase, is the grammar pass's and gate 2's.
- **No names in narration:** narration never names a person (an author, researcher, or creator, such as the people behind a testing concept); it explains the concept in our own words, and the description's References credit the concept and its source (`package-video`) **[checked: a `say` naming a person in `channel.yaml` `narration_avoid_names`, whole words in any case; list each name as it may be said, such as a surname alone]**. On-screen text names no person either, judged at gate 2.
- **Never a blank screen:** no slide or screen stays empty for more than a second. Every scene has a `heading` and something to show by kind **[checked: the fields are required]**, and its first sentence names what is shown, so its visual elements start with its first words; never open a scene's `say` with a pause (`//`) or a long lead-in. The renderer times each element from the words and refuses a drawn scene with nothing shown in its first second.
- **Narrate items in order, by their leading words:** every on-screen element (heading, point, title word, compare heading and item, intro role, activity, and stake, split label, repo or kit file, takeaway, mark, cta action) enters at its leading key word (its first word of three letters or more that is not a word such as "the" or "not"), said after the item before it, else at another of its key words; never before. So say the items in their listed order, each with its leading word, and say that word only when the item should appear; a compare's two headings enter together, at the later of their words. `render-video` refuses an item none of whose words is heard, and lists each element's cue against the words said in `render/alignment.md` for gate 3, which judges any item that waits long after its words.
- **Filler or transition scenes:** when a beat has nothing to show yet, never show content early: add a `title` scene before it, such as a question in the centre ("What did the AI skip?"), or open the next scene's `say` on its heading's words. A cold open is never a filler, and a Short has no `title` scene before its kit **[checked]**, so a Short opens each scene on its heading's words.
- **Nothing over text or code** (every video, row 36): no heading, on-screen line, mark note, or arrow covers another or a code character, on the video's own layout. `render-video` refuses such a scene, and a mark with no free space for its note, naming the scene and both elements; the fix is a shorter line, note, or heading, or the scene split in two.
- **Explain each terminal step:** a `terminal` scene's `say` gives each demo step one sentence, in the tape's order, saying what the command does and why, with the leading word of the step's `# comment` (`build-video-demo` writes the comments from these sentences); output the viewer must read gets its own sentence, said as it appears. `build-video-demo`'s `record.py` starts each step as its sentence starts and refuses a step whose words are never heard; whether each sentence explains what and why is judged at gate 2.

## Introduce the AI kit (every long-form)

Before the first scene that uses the AI kit (a `terminal` scene whose heading or `say` names the kit, or the `kit` scene), a `repo` scene introduces it **[checked]**: the GitHub `repo` (`owner/name`, the channel's `demos.repo`), the `path` of the kit's folder (`<n>-<slug>/ai-kit`), and one to eight `files` lines (such as `AGENTS.md`, `skills/<skill>/SKILL.md`, `scripts/<name>`), drawn as a GitHub folder card; `link_at` (default `description`) is the word at which it says where the link is **[checked: a word of say; once `demo.json` exists, the folder is the demo's]**. `say` says the kit is yours, what problem it is for, that it is on GitHub, and that the link is in the description, such as "Now I have built an AI kit for exactly this problem. It is on my GitHub, and the link is in the description."

A Short has no repo card: its kit scene's link is the introduction.

## Take it to your agent (every structure, Shorts too)

A long-form's scene before the bridge, or a Short's scene just before its closing scene, is a `kit` scene (a closing cta not counted); `check_script.py` refuses a long-form without one in its last two scenes, a Short without one just before its closing scene, the old `"kit": true` flag, and the old `link` and `snippet` fields.

- **The same GitHub card:** the kit scene replays the repo card's GitHub animation: the `repo` (`owner/name`) and `path` (`<n>-<slug>/ai-kit`) as the repo card, and one to eight `files`, each `{path, use, at}`: the file in `ai-kit/` (such as `AGENTS.md`, `skills/<skill>/SKILL.md`, `scripts/<name>`), one line on how the viewer uses it and its benefit (such as "Paste it so your agent flags self-mocking tests"), and the `at` word where that line appears; the link at `link_at` (default `description`); then two to four `takeaways` from `takeaways_at` **[checked: count, cue words, and, once `demo.json` exists, the card's folder is the demo's `ai-kit/` and each file is in it]**.
- **State the benefit** (row 37): `say` and each file's `use` line say what the viewer's agent then does for them and the result for the viewer, such as "Your agent then flags every test that mocks the code it checks, so you review only real tests.", never only file names **[checked: a BENEFIT cue in `say` and each `use` line: your agent, asks, catches, flags, checks, finds, writes, helps, so you, or for you]**; whether it is a real benefit is judged at gate 2.
- **Explain, never repeat:** `say` walks the files in order, saying what each is for, how the viewer uses it in their own project (paste the rules, copy the skill, run the script on a test file), and what their agent then does, says the link is in the description, and names the takeaways. No `use` line or takeaway repeats a line an earlier scene showed (its on-screen text, compare items, or mark notes) **[checked: word for word]**; the takeaways are what the viewer keeps, said in new words. `build-video-demo` builds each file the card lists.

## Like, share, subscribe (every long-form; a Short may)

- **A `cta` scene** with the `heading` and `actions` (`like`, `share`, `subscribe`, `notify`) shows each action's graphic as the narrator names it. A long-form ends on one, its very last scene, after the bridge and its comment question, showing all four **[checked]**; a Short may end on one naming `subscribe`, as its last scene **[checked]**. A cta is never earlier **[checked]**.
- **Short and natural:** `say` is at most two sentences, about eight seconds at the channel's pace in a long-form and about four in a Short (estimated as the length) **[checked]**, opens on a bridge like every scene, and names each action's cue word (like, share, subscribe, notification or bell) **[checked]**, such as "Before you go, like and share this with a tester. // Subscribe, and turn on the bell for notifications." (a Short: "Next, subscribe for a new challenge every week."). Never a banned phrase such as "smash that like button" or "make sure to subscribe" **[checked]**.

## Thank the viewer (every video, Shorts too)

The last scene's `say` thanks the viewer **[checked: thank you or thanks]**: a long-form's inside its `cta`, within its two sentences and about eight seconds, such as "Before you go, thank you for watching. // Like and share this with a tester, subscribe, and turn on the bell for notifications."; a Short's in its closing cta, within about four seconds ("Before you go, thanks for watching, and subscribe for a new challenge every week."), or without one in its last scene ("Thanks for watching."). The thank-you addresses the viewer, never "thanks to the mock", judged at gate 2.

## Choosing

| Structure | `structure` value | Fits an idea that is | Watch for |
|---|---|---|---|
| Challenge first | `challenge-first` | a puzzle the viewer can try to solve, such as a spot-the-bug | repetitive if every video uses it |
| Incident story | `incident-story` | a failure with stakes: what broke, who noticed, why the checks missed it | label it a constructed scenario unless it is real and cited |
| Myth buster | `myth-buster` | a common belief the video tests like a tester | needs a real, reproducible experiment, from the demo |

## Challenge first (`challenge-first`)

| Beat | Share | Content |
|---|---|---|
| Intro | first 15 s | An `intro` scene: who it is for, the activity, and the stake. |
| Cold open | next 10 s | The code under test and its tests side by side (`split`), the stake in the first sentence, and the challenge: "spot the bug". |
| Pause prompt | to 40 s | The same split on screen, with a prompt to pause and look. |
| Context | to 1 min | What the code under test should do. |
| Reveals | about a third | Each problem in turn, one per scene group, as `marks` on the lines in the code or split. |
| Proof | about a sixth | The demo run that shows the problem, each code change shown before and after (the title's promise kept). |
| Fix | about a sixth | The better version, and why each part can fail for one reason. |
| Principle | about a tenth | The tester's question the case teaches. |
| Introduce the kit | about 10 s | A `repo` scene: the kit on GitHub, its files, and "the link is in the description". |
| Take it to your agent | about 25 s | A `kit` scene: the same GitHub card, each file and how to use it, the link, and the takeaways, each as it is said. |
| Bridge | about 25 s | One comment question and the next challenge. |
| Like, share, subscribe | last 8 s | A `cta` scene, the last: each action's graphic as it is said, and a thank-you to the viewer, in two sentences. |

## Incident story (`incident-story`)

| Beat | Share | Content |
|---|---|---|
| Intro | first 15 s | An `intro` scene: who it is for, the activity, and the stake. |
| Cold open | next 12 s | The evidence of the incident on screen (the log, output, or code), its stakes in one line. |
| Stakes | to 45 s | What broke, who noticed, why the checks did not. |
| Investigation | about a third | Walk the evidence like a tester: what does each check really check? |
| Root cause | about a fifth | The cause, shown on screen (the title's promise kept). |
| Proof | about a seventh | Reproduce it with the demo. |
| Fix and guardrail | about a fifth | The fix, and the check that stops it coming back. |
| Introduce the kit | about 10 s | A `repo` scene: the kit on GitHub, its files, and "the link is in the description". |
| Take it to your agent | about 25 s | A `kit` scene: the same GitHub card, each file and how to use it, the link, and the takeaways, each as it is said. |
| Lesson and bridge | about 40 s | The human question that was skipped, one comment question, the next video. |
| Like, share, subscribe | last 8 s | A `cta` scene, the last: each action's graphic as it is said, and a thank-you to the viewer, in two sentences. |

## Myth buster (`myth-buster`)

| Beat | Share | Content |
|---|---|---|
| Intro | first 15 s | An `intro` scene: who it is for, the activity, and the stake. |
| Claim | next 10 s | The belief, shown in a real artifact (a quote, code, or output), and the promise to test it. |
| Method | to 50 s | The experiment, set up so the viewer could repeat it. |
| Run | about a third | The demo run, step by step. |
| Results | about a fifth | What held and what did not, on screen. |
| Why | about a fifth | The patterns behind the results. |
| Verdict | about a tenth | A nuanced verdict and a checklist the viewer can apply (the title's promise kept). |
| Introduce the kit | about 10 s | A `repo` scene: the kit on GitHub, its files, and "the link is in the description". |
| Take it to your agent | about 25 s | A `kit` scene: the same GitHub card, each file and how to use it, the link, and the takeaways, each as it is said. |
| Bridge | about 20 s | "So which claim should I test next?" and the next video. |
| Like, share, subscribe | last 8 s | A `cta` scene, the last: each action's graphic as it is said, and a thank-you to the viewer, in two sentences. |

## Short (`challenge-first`)

A Short is a standalone challenge, thirty to sixty seconds, that makes sense without its long-form video. It never starts abruptly and never jumps: it flows problem, resolution, kit, and closing (row 37), each beat joined to the next by one bridging sentence: every scene after the first opens on a transition cue **[checked]**, as in "Scene rules". `check_script.py` refuses a missing or misplaced beat, naming it and its scene **[checked]**.

| Beat | Time | Content |
|---|---|---|
| Problem | to 20 s | No intro: scene 1 is a `split` of the code and its tests with a `hook`, two to eight words of curiosity, such as "This test has never failed", said in the first sentence of `say`, at most three seconds **[checked]**, and the bug's line marked (`marks`) at its word **[checked]**. A question or surprise the viewer wants answered, never a slogan. The code is large enough for a phone, never a slide of code. Bridge: "So how do you catch it?" |
| Resolution | to 30 s | A quick resolution concept: a scene after the problem and before the kit saying how to fix or catch the bug **[checked: a cue: fix, catch, instead, should, check, or so that]**; a `code` scene with the fix marked, or a short `points` scene; never a bare `title` slide **[checked: no `title` scene before the kit]**. Bridge: "So take it to your agent." |
| Take it to your agent | to 45 s | A `kit` scene, just before the closing scene **[checked]**: the same GitHub card, one or two files, each with how to use it and what the viewer's agent then does for them **[checked: benefit cue]**, and the takeaways. Its card introduces the kit, so no repo card. |
| Links and full video | last 10 s | The closing scene, the last or the one before a closing cta: `say` names where the links are (the kit and code in the description) **[checked: link, links, or description]** and the full video or breakdown and what more it shows, such as "Now the links to the kit and the code are in the description. Watch the full video for a second bug and the fix." **[checked]**. With no cta it is the last scene and thanks the viewer **[checked]**. |
| Like, share, subscribe | last 4 s | Optional: a closing `cta` naming `subscribe`, at most about four seconds, the last scene, thanking the viewer **[checked]**. |

One text layer speaks at a time (row 35), as the captions already speak the narration:

- **Short lines:** every on-screen line (the heading, visual lines, split labels, mark notes, compare headings and items, kit use lines and takeaways) has at most eight words **[checked: SHORT_LINE_WORDS]**.
- **A label, never the sentence:** an on-screen line is a short label, never a sentence `say` reads word for word; the hook is the one exception, said aloud. `render-video` keeps the burned captions blank while big spoken text (the hook, a `title` visual, a point) shows, and never shows a caption group repeating two or more consecutive words of an on-screen text shown then; that a visual does not simply repeat `say` is judged at gate 2.
- **The hook stands alone:** it takes the heading band above the split, clear of the code, and the heading enters in that band only once the hook has faded (`render-video`).
