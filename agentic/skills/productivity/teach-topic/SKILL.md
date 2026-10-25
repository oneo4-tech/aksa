---
name: teach-topic
description: Use when the owner wants to learn a topic over sessions, or asks to continue learning one. Keeps a teaching workspace under .kb/outputs/learnings/<topic-slug>/ with the mission, sources, glossary, learning records, lessons, reference docs, assets, and notes, and produces one short interactive HTML lesson per session in the zone of proximal development, built for long-term retention.
---

# Teach topic

A one-off explanation is forgotten, and the next session starts from zero. This skill keeps the state of the learning in files, so every session teaches the next right thing.

## Inputs and prerequisites

- The topic, from the request. Without it, ask "What would you like to learn about?"
- Optional: a specific thing to learn this session, the owner's prior knowledge, and constraints such as time, budget, or preferences.
- `.kb` linked; if missing, run `uv run agentic/scripts/link_external.py --check` and report the result.
- Web access to find and check sources, and a browser to open lessons. Without them, teach only from the sources already in `RESOURCES.md` and record the limit.
- `references/workspace.md` before writing any workspace file, and `references/teaching.md` before choosing or building a lesson, both in this skill's folder.

## Procedure

1. **Open the workspace.** Take `$root` as the main checkout: the parent of the directory that `git rev-parse --path-format=absolute --git-common-dir` prints, because `.kb` exists only there. The workspace is `$root/.kb/outputs/learnings/<topic-slug>/`; create it on first use and read everything in it. One topic is one workspace.
2. **Settle the mission.** When `MISSION.md` is missing, empty, or vague, run the mission interview inline: why, what success looks like, constraints, and out of scope. Push back on vagueness; write `MISSION.md` only after the owner confirms. When the goal shifts, confirm the change, update `MISSION.md`, and write a learning record.
3. **Gather sources first.** When `RESOURCES.md` is thin for what is about to be taught, find high-trust sources: primary sources, recognised experts, peer-reviewed work, well-moderated communities. Record areas with no good source under Gaps. Never teach from parametric knowledge alone; cite every claim.
4. **Choose one lesson.** Teach the thing the owner named; otherwise the most relevant thing they cannot yet do alone but can with a little guidance, taken from the learning records and the mission. Scope it to one tangible win; coverage is not learning.
5. **Build the lesson** following `references/teaching.md`: read `assets/` first and reuse it, and put new reusable parts in `assets/`, the shared stylesheet first. Knowledge parts low difficulty, skills parts desirable difficulty with a tight feedback loop, quiz answer options of equal length, glossary terms exactly, links to earlier lessons and reference docs, one recommended primary source, and a reminder to ask follow-ups. Write one self-contained HTML file to `lessons/NNNN-<name>.html`, numbered after the highest existing lesson, with clean typography and content over decoration. Open it for the owner where possible.
6. **Teach and answer** in the session, from the sources. For a question that needs real-world judgement, answer what the sources support and point to a community in `RESOURCES.md`, unless the owner opted out; record an opt-out in `NOTES.md` and `RESOURCES.md`.
7. **Update the workspace** as `references/workspace.md` describes: fold the lesson's essence into `reference/`, add to `GLOSSARY.md` only terms the owner now understands, write a learning record only on evidence, record teaching preferences in `NOTES.md`, and prune weak sources and record new gaps.
8. **Commit the session.** Append one line to `.kb/log.md` for the lesson, in the format `agentic/rules/knowledge.md` gives, then stage only the workspace and the log and commit in the Knowledge Base repository (D-018): `git -C .kb add outputs/learnings/<topic-slug> log.md`, then `git -C .kb commit -m "add: <topic> lesson NNNN"`. Never stage other `.kb` changes.

## Output

- The lesson path, opened for the owner; the workspace files changed; the Knowledge Base commit hash.
- In chat, one line naming the lesson, its path, and its one tangible win, then the follow-ups.
- If a **Done when** condition cannot be met, report blocked with what is missing; never invent a source, a learning, or a mission.

## Constraints

- Mission first: no lesson before `MISSION.md` is clear.
- Sources first: never teach from parametric knowledge alone, and cite every claim.
- One lesson per session, in the zone of proximal development, with one tangible win.
- Knowledge parts low difficulty; skills parts desirable difficulty with tight feedback.
- Quiz answer options of equal length.
- Reuse assets; new reusable parts go to `assets/`.
- Learning records only on evidence, never for material merely covered; supersede, never delete.
- Glossary terms only for what the owner now understands.
- Wisdom questions go to a community unless the owner opted out.
- Write "section N" in plain words, never the section sign.
- The workspace lives under `.kb/outputs/learnings/`, reached through the `.kb` symlink (D-012). Commit only the workspace and `.kb/log.md` in the Knowledge Base repository (D-018), and never commit `.kb` content to aksa.
- Vendor-neutral (D-004). The owner starts this skill, and it changes no aksa repository files.

## Done when

- `MISSION.md` is clear and confirmed, and the lesson sits in the zone of proximal development for one tangible win.
- One self-contained HTML lesson exists at `lessons/NNNN-<name>.html`, with every claim cited to a source in `RESOURCES.md`, retrieval practice whose answer options are equal length, links to earlier lessons and reference docs, one recommended primary source, and a prompt to ask follow-ups.
- Each learning record names the evidence the owner showed, and each new glossary term is one the owner now understands.
- `.kb/log.md` has the lesson's line, and the Knowledge Base repository has the workspace and the log committed with nothing else staged.
