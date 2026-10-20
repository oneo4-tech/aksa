---
name: research-topic
description: Use when the owner asks to research, investigate, or gather facts on a topic. Probes what is known and unknown, searching the Knowledge Base first and primary web sources only for gaps, and writes cited foundations, paradigms, and hypotheses to .kb/outputs/research/.
---

# Research topic

## Inputs and prerequisites

- The topic or question, from the request. If it is too broad to answer with evidence, propose a narrower scope with the questions in step 1.
- `.kb` linked; if missing, run `uv run agentic/scripts/link_external.py --check` and report the result.
- Web search and page fetch tools. Without them, research the Knowledge Base only and record the limit.
- Output shape: `references/research-template.md`; web brief: `references/web-search-brief.md`, both in this skill's folder.

## Procedure

1. **Frame the questions.** Rewrite the topic as numbered, atomic, factual questions covering what is established, which approaches exist, and what is unknown. "Should we use X?" becomes "What does X guarantee about Y?" and "Which versions of X support Z?". Propose a lowercase hyphenated slug. Confirm both with the owner; when the owner is not present, proceed and list them under "Decisions for the owner" (`AGENTS.md`).
2. **Search the Knowledge Base first.** Run `get-kb` for each question. Record each wiki page used and each page read with nothing relevant, and mark every question answered, partly answered, or unanswered.
3. **Search the web for gaps only.** For questions not fully answered, fill `references/web-search-brief.md` with the slug and those questions word for word. Give it to a sub-agent with web tools when the runtime offers one; otherwise follow it inline.
4. **Verify every web claim.** Each needs URL, source type, version, locator, and quote. Fetch the page to confirm the quote and version yourself, and drop any source outside the allowed list. If search or fetch is blocked, record it under `limits` and leave the question in the gaps.
5. **Analyse.** From verified facts only:
   - **Foundations:** established facts and concepts the topic rests on.
   - **Paradigms:** prevailing approaches or models, with the tradeoffs the sources state.
   - **Hypotheses:** testable propositions about what remains unknown, each based on named foundations or paradigms and stating what would confirm or refute it.
   - **Gaps and contradictions:** unanswered questions and sources that disagree.
6. **Write the output.** Copy the template to `.kb/outputs/research/<YYYY-MM-DD>-<slug>.md` and fill every placeholder. Register each source once (`[K1]` for a wiki page, `[W1]` for a web source) and cite it from every foundation and paradigm. Then check the file against **Done when** and fix every miss.
7. **Record it.** Append `- <date> add outputs/research/<file>: <topic>` to `.kb/log.md` and commit in the Knowledge Base repository (D-018).

## Output

The output file path, the counts of foundations, paradigms, hypotheses, and gaps, and any limits. List the foundations worth making trusted knowledge; the owner decides whether to capture them with `add-kb`. If a **Done when** condition cannot be met, report blocked with the condition and the reason.

## Constraints

- **Allowed web sources:** official documentation, source code repositories, language or protocol specifications, official release notes and changelogs. Nothing else.
- **Banned:** blog posts, tutorials, forums, Q&A sites, opinion pieces, vendor marketing, AI-generated summaries, and your own unsupported knowledge.
- Knowledge Base first, web only for gaps. Cite only `wiki/` pages; `inbox/`, `raw/`, and `outputs/` are not trusted (D-017), including earlier research outputs.
- Facts, not decisions: no recommendations or rankings outside a quoted source. Hypotheses are labelled inferences, never findings.
- Never fill a gap from memory. Never put aksa-internal text, file paths, or secrets in a search query, and never write `.env` values to the output.
- Research outputs stay untrusted until promoted through `add-kb` and `review-kb`. Facts about aksa come from `get-memory`, not this skill (D-015).

## Done when

- Every source is a `wiki/` page or a web page you fetched whose type is on the allowed list; every registered source is cited.
- Every foundation and paradigm cites a registered source, and every question is answered by one or listed under gaps.
- Every hypothesis names the foundations or paradigms it rests on and how to verify it.
- No placeholder, em dash, opinion word outside a quote, or `.env` value remains in the file.
- `.kb/log.md` has the `add` line, and the Knowledge Base repository has the output committed.
