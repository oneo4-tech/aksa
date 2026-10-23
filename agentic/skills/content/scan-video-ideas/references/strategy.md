# Backlog strategy

Read at the weekly scan's first step and when drafting any idea card. Ideas are timely, rooted in how testers think, provable on screen, and distinct from vendor tutorials. The agent proposes; the owner picks what to file and passes gate 1.

## Sources

| Stream | What to watch | Why it feeds the channel |
|---|---|---|
| RST canon | rapid-software-testing.com, satisfice.com blog, developsense.com blog and its AI experiments, the LLM syndromes page, the book *Taking Testing Seriously* | The lens: testing vs checking, oracles, HTSM, safety language, deep vs shallow |
| Tool releases | Playwright, Cypress, pytest, Selenium release notes; the GitHub Copilot changelog | Timely hooks: new AI and agent features examined with a tester's eye |
| AI risk and standards | OWASP Top 10 for LLM Applications, NIST AI 100-1 and 600-1, ISTQB CT-AI and CT-GenAI | The testing-AI-systems pillar |
| LLM eval practice | Anthropic, OpenAI, and Google eval documentation | Where evals and testing meet, and what checks miss |
| Audience signals | Comments on the channel's videos; the competition research of `scripts/competition.py` | What people ask and what is already covered |
| Owner's field notes | Bugs and stories from real work, anonymised | Incident stories no one else can make; without real notes, label the scenario as constructed |

## The RST lens

Every idea names at least one Rapid Software Testing concept and the question a tester asks that the mainstream take skips:

- Testing vs checking: is this a test or a check, and what does it miss?
- Oracles (FEW HICCUPPS): how would we recognise a problem here?
- HTSM (SFDIPOT, quality criteria): which product element or quality is untested?
- Deep vs shallow testing: does this find elusive bugs or only easy ones?
- Safety language and test framing: what can we honestly claim?
- LLM syndromes and consistency: how does this AI behave badly, and how often?

Attribution: Rapid Software Testing and its concepts are James Bach's and Michael Bolton's, credited with links in each video's description. The channel explains and applies them in its own words, never claims their endorsement, and links the book and classes.

## Scoring guide

Each factor 1-5; the agent proposes, the owner adjusts. Weights and the park line are in `scripts/competition.py`.

| Factor | Card key | 5 means |
|---|---|---|
| Lens depth | `lens` | The RST question fully reframes the topic |
| Proof | `proof` | A demo shows it on screen in under 2 minutes |
| Freshness | `freshness` | Tied to a release or change in the last 90 days |
| Audience pull | `audience_pull` | Clear search demand or comment signals; a hypothesis until analytics exist |
| Distinctness | `distinctness` | Unlike the closest videos found, including the channel's own |
| Effort (inverse) | `effort` | Easy to produce |
