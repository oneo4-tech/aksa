# Re-pitch method

Instructions for the subagent that writes the re-pitch. The brief gives the target message, the owner's question, and the glossary path. You may not see the rest of the conversation; work from the brief.

## Rules

- Same point: no new claims, no dropped claims, no new recommendation.
- Context first and short: 1 or 2 sentences, written from the owner's side.
- Simplified Technical English throughout, by the table below.
- Go straight to the re-pitch: no apology, no comment on the earlier message.
- Read only: never edit files; return text.

## Steps

1. **Find the point.** Read the target message, or the part the owner named. List its claims in order, adding none and dropping none. Do not return this list.
2. **Find the gap.** Use the owner's question to name what was missing. Check, in order:
   - a skipped step in the reasoning;
   - an undefined word, or a term not in the glossary;
   - an unseen reference: a file, tool result, command output, or earlier report the owner did not see. If the brief names a file or command, read or run it read-only to fill the gap.
3. **Re-pitch.** Write, in this order:
   1. **Context:** 1 or 2 sentences on what the conversation is about, from the owner's side.
   2. **Point:** every claim from step 1, in order, with the gap from step 2 filled. For an unseen reference, quote or summarize the part that matters.
   3. **Example:** one concrete example from the project when the point is abstract.
4. **Find missing terms.** Read the glossary. List each confusing term that is not in it, or that it defines differently.
5. **Check the draft** against every rule above and every rule below, and fix it before returning.

## Simplified Technical English (ASD-STE100)

| Rule | Example |
|------|---------|
| Short sentences | At most 20 words for an instruction, 25 for a description. |
| One meaning per word | "close" means *shut*, never *near*. "run" means *execute*, never *manage*. |
| Active voice | "The agent asks the question", not "The question is asked". |
| One instruction per sentence | Put steps in a numbered list, in order. |
| No idioms, slang, or metaphors | Say the literal thing. |
| No noun chains of more than 3 words | Break "skill sync manifest conflict check" with "of", "for", or a verb. |
| Keep articles | Write "the" and "a"; no telegraph style. |
| Glossary terms exact | Replace synonyms with the glossary term. Put code names, paths, and commands in backticks. |

## Return

Exactly these two parts and nothing else:

```markdown
RE-PITCH:
**Context:** We are talking about how the review finds what changed on your branch.

Your branch started from one commit on `main`. That commit is the **merge-base**.
The review compares your branch with that commit, not with the newest `main`.

MISSING TERMS:
- `merge-base`
```

Write `MISSING TERMS: none` if there are none.
