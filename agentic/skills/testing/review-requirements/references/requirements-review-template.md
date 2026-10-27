# Requirements review: {{client}} {{engagement}}

{{one sentence: what was reviewed and what the review found, from the brief and the api_spec when one is named}}

- Client: {{client}}
- Engagement: {{engagement}}
- Brief: brief.md
- API specification: {{api_spec path inside the engagement folder, or none named}}
- Reviewed: {{date}}
- Sources reviewed: {{AC1: the criterion in the brief's words; AC2: ...; one per acceptance criterion in the brief, in order}}

## Ambiguities

One row per place where two people could build different behaviour from the same words, with the question that settles it and a severity.

| ID | Where | Statement | Why it is ambiguous | Question for the client | Severity |
|---|---|---|---|---|---|
| A1 | {{brief section, item, or api_spec operation}} | {{the words as written}} | {{the two readings it allows}} | {{one question whose answer removes this row}} | {{blocker, high, medium, or low}} |

## Missing acceptance criteria

One row per in-scope endpoint, page, flow, risk, or api_spec operation with no criterion that would fail when it breaks.

| ID | Where | Missing criterion for | Why it is needed | Question for the client | Severity |
|---|---|---|---|---|---|
| M1 | {{brief section or api_spec operation}} | {{the endpoint, page, flow, or risk with no criterion}} | {{what would go unnoticed without it}} | {{one question whose answer gives the result that will be accepted}} | {{blocker, high, medium, or low}} |

## Untestable statements

One row per statement that no test could pass or fail as written.

| ID | Where | Statement | Why it cannot be tested | Question for the client | Severity |
|---|---|---|---|---|---|
| U1 | {{brief section, item, or api_spec operation}} | {{the words as written}} | {{no observable result, no threshold, unavailable data or environment, an excluded third party, or a result only after the engagement}} | {{one question whose answer makes it testable or removes it}} | {{blocker, high, medium, or low}} |

## Review summary

The counts per section, the findings that block the engagement with the question that clears each one, and the severity scale used above.

- Ambiguities: {{n}}
- Missing acceptance criteria: {{n}}
- Untestable statements: {{n}}
- Blockers: {{A1, M2, or none, each with the question that clears it}}
- Severity scale: blocker means the exit criteria and cases cannot be written; high means the answer changes scope, cost, or the exit criteria; medium means one flow or case cannot be written; low means wording only.
