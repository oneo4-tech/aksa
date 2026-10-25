# Teaching

The rules behind a lesson. Read before choosing or building one.

## Terms

- **Teaching workspace:** the folder for one topic that remembers the mission, sources, lessons, and what the owner has learned. One mission per workspace.
- **Mission:** why the owner is learning this; the concrete real-world goal. It grounds every teaching decision.
- **Zone of proximal development (ZPD):** what the owner cannot yet do alone but can with a little guidance, challenged just enough.
- **Parametric knowledge:** what a model memorised in training. It can be outdated or confidently wrong, and a learner cannot spot the errors. Never teach from it alone.
- **Fluency:** in-the-moment recall. It feels like mastery and fades.
- **Storage strength:** long-term retention. This is the goal.
- **Desirable difficulty:** effort that builds storage strength: retrieval practice (recalling rather than rereading), spacing (practice spread over time), and interleaving (mixing related topics, for skills only).
- **Learning record:** a decision-grade note about what the owner now knows. The records set the floor of the ZPD.

## The three needs

Every topic mixes three needs, in different proportions; theoretical physics leans on knowledge, yoga on skills.

- **Knowledge** comes from high-trust sources, listed in `RESOURCES.md`.
- **Skills** come from interactive lessons with a feedback loop.
- **Wisdom** is real-world judgement, from communities.

## Why the rules matter

- **Sources first:** parametric knowledge can be outdated or confidently wrong, and a learner cannot spot the errors. Citations make every claim checkable, so the owner can verify a lesson later without trusting the teacher.
- **Fluency is an illusion:** recall right after reading is short-term availability. Only effortful recall, spread over time, builds storage strength.
- **Coverage is not learning:** counting covered material would push lessons past what the owner can do. Choose from what the learning records show the owner knows.
- **Equal-length quiz answers:** format cues, such as the longest answer being the right one, turn recall into test-taking.

## Building the lesson

1. **Read `assets/` first** and build from the components already there. Anything new and reusable becomes a component in `assets/`, never inline code a later lesson would duplicate. The shared stylesheet is the first component every workspace earns, so the lessons look like one course.
2. **Knowledge parts: difficulty is the enemy.** Difficulty eats the working memory needed to understand. Include only what this lesson's skill needs, teach it first, take it from `RESOURCES.md`, and cite it throughout.
3. **Skills parts: difficulty is the tool.** Effortful retrieval builds storage strength. Use interactive quizzes, light in-browser tasks, or guided real-world steps, each with a tight feedback loop that is immediate and ideally automatic.
4. **Quiz answer options are all the same length**, in words and where possible in characters, so formatting gives no clue.
5. **Use glossary terms exactly** once `GLOSSARY.md` exists, so the owner meets one name per idea.
6. **Link** to earlier lessons and reference docs with relative anchors.
7. **Recommend one primary source** to read or watch next, from `RESOURCES.md`.
8. **Remind the owner to ask follow-up questions** in the session; the lesson is a starting point, not the whole of the teaching.
9. **Write cross-references in plain words**, never with the section sign: "section 5", "sections 3 to 5", "lesson 0007, section 4". Name the document when citing another file.

Write the lesson as one self-contained HTML file in `lessons/NNNN-<name>.html`, numbered after the highest existing lesson, with clean typography and content over decoration. Open it for the owner where possible.
