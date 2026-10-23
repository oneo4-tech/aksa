# PROTOTYPE: backlog research strategy

Research: `.kb/outputs/research/2026-10-23-testing-backlog-research.md`.

## Goal

A steady backlog of video ideas that are timely, rooted in how testers think (Rapid Software Testing as the lens), provable on screen, and distinct from vendor tutorials. The agent proposes; the owner approves at gate 1.

## 1. Sources (scanned weekly by the agent)

| Stream | What to watch | Why it feeds the channel |
|---|---|---|
| RST canon | rapid-software-testing.com, satisfice.com blog, developsense.com blog and its AI Experiments category, LLM syndromes page, the book *Taking Testing Seriously* | The channel's lens: testing vs checking, oracles, HTSM, safety language, deep vs shallow |
| Tool releases | Playwright, Cypress, pytest, Selenium release notes; GitHub Copilot changelog | Timely hooks: new AI and agent features to examine with a tester's eye |
| AI risk and standards | OWASP Top 10 for LLM Apps, NIST AI 100-1 and 600-1, ISTQB CT-AI and CT-GenAI | The "testing AI systems" pillar |
| LLM eval practice | Anthropic, OpenAI, Google eval docs | Where "evals" and testing meet, and what checks miss |
| Audience signals | Comments on the channel's videos; Studio analytics after launch; YouTube Data API search for competing videos (needs a Google Cloud API key, see below) | What people ask and what is already covered |
| Owner's field notes | Bugs and stories from real work (anonymised) | Incident-story videos no one else can make |

## 2. The RST lens (every idea must pass)

Each idea names at least one RST concept and the question a tester asks that the mainstream take skips:

- Testing vs checking: is this a test or a check, and what does it miss?
- Oracles (FEW HICCUPPS): how would we recognise a problem here?
- HTSM (SFDIPOT, quality criteria): which product element or quality is untested?
- Deep vs shallow: does this find elusive bugs or only easy ones?
- Safety language and test framing: what can we honestly claim?
- LLM syndromes and consistency: how does this AI behave badly, and how often?

Attribution rule: RST concepts are credited to James Bach and Michael Bolton with links in the description; the channel explains and applies them in its own words, never claims endorsement, and links the book and classes.

## 3. Idea card (one GitHub issue at `youtube-stage:idea`)

Title (challenge style), pillar, RST concept, the mainstream claim, the tester's question, proof/demo, format (long, Short, series), freshness hook and date, sources, risks (rights, real people, accuracy), score.

## 4. Score (1-5 each, agent proposes, owner adjusts)

| Factor | Weight | Meaning |
|---|---|---|
| Lens depth | 3 | How strongly the RST question reframes the topic |
| Proof | 3 | Can a demo show it on screen in under 2 minutes |
| Freshness | 2 | Tied to a release or change in the last 90 days |
| Audience pull | 2 | Search demand and comment signals (hypothesis until data) |
| Distinctness | 2 | Unlike existing videos, including our own |
| Effort (inverse) | 1 | 5 = easy to produce |

Max 65. Ideas under 40 stay parked.

## 5. Cadence

- Weekly (agent, about 30 minutes): scan sources, draft up to 5 idea cards, score, flag hooks expiring soon.
- Weekly (owner, about 10 minutes): gate 1 on the top cards; pick 1 long-form and 2 Shorts.
- Monthly: retire stale ideas, rebalance pillars, compare scores with real views.

## 6. Optional setup for audience pull

The current AI Studio key cannot call the YouTube Data API (it requires a Google Cloud API key with the API enabled). search.list allows 100 calls a day and returns no view counts; videos.list returns view counts. With a Cloud key, the agent can list the top competing videos and their views for each idea.
