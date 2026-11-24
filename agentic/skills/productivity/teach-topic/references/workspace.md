# Teaching workspace

Formats and rules for the teaching workspace. Read before writing any of its files.

## Path

```bash
root="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
workspace="$root/.kb/outputs/learnings/<topic-slug>"
```

`.kb` is a symlink that exists only in the main checkout, which is why the root comes from the common git directory and not from the current worktree. Create `outputs/learnings/` and the topic folder on first use. One topic is one workspace; two unrelated topics are two workspaces. Reach it through the `.kb` symlink (D-012).

| File or folder | Holds |
|---|---|
| `MISSION.md` | Why the owner is learning this; grounds every teaching decision |
| `RESOURCES.md` | Curated high-trust sources (knowledge) and communities (wisdom) |
| `GLOSSARY.md` | The workspace's canonical terms |
| `NOTES.md` | Teaching preferences and working notes, free-form |
| `lessons/NNNN-<name>.html` | The main output: one short, self-contained lesson per tightly scoped thing |
| `reference/*.html` | Compressed essentials for quick lookup: cheat sheets, syntax, algorithms, routines; they print well |
| `learning-records/NNNN-<slug>.md` | What the owner now knows; sets the zone of proximal development |
| `assets/*` | Reusable components: shared stylesheet, quiz widgets, simulators, diagram helpers |

## `MISSION.md`

```markdown
# Mission: {Topic}

## Why
{1-3 sentences: the concrete real-world goal; what changes when the owner has this skill. Not "to understand X".}

## Success looks like
- {A specific, observable thing the owner will be able to do}

## Constraints
- {Time, budget, commitments, learning preferences}

## Out of scope
- {Adjacent topics not worth chasing now; this protects the zone of proximal development}
```

- One mission per workspace.
- Concrete over abstract: "ship a Rust CLI to my team", not "learn Rust".
- Push back on vagueness; a bad mission is worse than none.
- Revise when reality shifts, and write a learning record about the change.
- One screen at most. Longer is a plan, not a compass.

## Learning records

`learning-records/NNNN-<slug>.md`, numbered from the highest existing record. Create the folder with the first record.

```markdown
# {Short title of what was learned or established}

{1-3 sentences: what is now known, or which prior knowledge was established, and why it matters for future sessions.}
```

Optional sections, only when valuable: **Status** (`active` or `superseded by LR-NNNN`), **Evidence** (how the owner showed it), **Implications** (what it unlocks or rules out).

Write one when:

- the owner showed genuine understanding of something non-trivial;
- the owner disclosed prior knowledge; record the depth;
- a misconception was corrected, which predicts future stumbling blocks;
- the mission shifted; cross-link it and update `MISSION.md`.

Not for material merely covered, for terms already in the glossary, or for activity logs. Supersede, never delete.

## `RESOURCES.md`

```markdown
# {Topic} Resources

## Knowledge
- [Book, article, or course title](link)
  What it covers. Use for: when to reach for it.

## Wisdom (Communities)
- [Community](link)
  Why it is high-signal. Use for: what to ask there.

## Gaps
- {Area with no good source yet}
```

- High-trust only: primary sources, recognised experts, peer-reviewed work, well-moderated communities. No marketing dressed as education.
- Annotate every entry with what it covers and when to use it.
- Group by Knowledge and Wisdom; every source a lesson cites must appear here.
- Gaps lists areas with no good source, and drives future searches.
- Prune ruthlessly: five sharp sources beat thirty mediocre ones.
- Record a community opt-out here, and in `NOTES.md`, when the owner makes one.

## `GLOSSARY.md`

```markdown
# {Topic} Glossary

{One or two sentences on the topic.}

## Terms

**Idempotency**:
The property that repeating an operation leaves the same end state as doing it once.
_Avoid_: repeatability, retry safety
```

- Add a term only once the owner understands it. The glossary records compressed knowledge; it is not a dictionary to learn from.
- Be opinionated: one term, with the rest listed as aliases to avoid.
- One or two sentences on what the term is.
- Use glossary terms inside definitions.
- Group under subheadings when clusters emerge.
- Flag ambiguities: "in this workspace, 'set' always means a working set".
- Revise in place as understanding deepens.

## `NOTES.md`

Free-form. The teaching preferences the owner stated or showed, such as pace, examples they liked, and formats they rejected, plus working notes for the next session. Not a learning record.
