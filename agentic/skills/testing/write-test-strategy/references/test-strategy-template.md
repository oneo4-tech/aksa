# Test strategy: {{client}} {{engagement}}

{{one sentence: what this engagement tests and why, from the brief's `## Background`}}

- Client: {{client}}
- Engagement: {{engagement}}
- Environment: {{environment}}
- Surfaces: {{api, ui, or both}}

## Scope

State what is tested and what is not, naming the endpoints, pages, and flows from the brief's `## Scope` and `## Out of scope`.

- In scope: {{endpoints, pages, and flows}}
- Out of scope: {{what is excluded}}

## Risks

Rank the brief's `## Known risks` by impact on the acceptance criteria, highest first, with an id the Approach section uses.

| ID | Risk | Impact | Likelihood | Basis |
|---|---|---|---|---|
| R1 | {{risk in the brief's words}} | {{high, medium, or low}} | {{high, medium, or low}} | {{the brief sentence or scope item it comes from}} |

## Approach

Give one approach per risk id: the test level, the technique, and the artifact that will show the risk is covered.

- **R1**: {{API, UI, or manual}} testing with {{technique}}; covered by {{artifact, such as docs/test-cases.md, the API or UI tests, or a bug report}}.

## Environments

Name each environment the tests run in, with the base URL from the brief's frontmatter and the credential variable names it needs; never a value.

- {{environment}}: {{ui_base_url and api_base_url, or "no URL"}}; credentials from {{credentials_env variable names, or "none"}}.

## Entry and exit criteria

State what must be true before testing starts, then one exit criterion for each brief acceptance criterion.

- Entry: {{environment reachable, test data and accounts ready, credential variables present in .env}}
- Exit: {{one line per brief acceptance criterion}}

## Open questions

List what the brief leaves open, with who can answer it and what it blocks, or `None`.

- {{question}}. Answered by: {{client contact or owner}}. Blocks: {{what it delays}}.
