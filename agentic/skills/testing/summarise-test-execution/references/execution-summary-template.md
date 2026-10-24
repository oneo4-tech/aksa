# Execution summary: {{client}} {{engagement}}

{{one sentence: what ran in this execution and what this summary recommends, taken from the evidence}}

- Client: {{client}}
- Engagement: {{engagement}}
- Environment: {{environment}}
- Evidence read: {{each evidence file, `README.md` first when it exists, then the real result files}}
- Prepared: {{date the summary was written}}

## Results by suite

One row per suite the evidence reports and one `not run` row per surface with no result, with counts exactly as the evidence states them.

| Suite | Evidence | Total | Passed | Failed | Errors | Skipped | Command and date |
|---|---|---|---|---|---|---|---|
| {{api, ui, or the suite name the evidence gives}} | {{evidence/<file>, never README.md alone}} | {{n or not stated}} | {{n or not stated}} | {{n or not stated}} | {{n or not stated}} | {{n or not stated}} | {{the command and date the evidence states, or not stated}} |

## Defects

One row per file in `docs/bugs/`, linked from this document with `bugs/<id>.md`, with the severity and priority it records and its status in this execution; write `None` when the evidence shows no defect and no file exists.

| ID | Defect | Severity | Priority | Bug file | Status in this execution | Trace |
|---|---|---|---|---|---|---|
| {{BUG-001}} | {{short title from the file}} | {{critical, high, medium, or low}} | {{P1, P2, P3, or P4}} | [{{BUG-001}}]({{bugs/BUG-001.md}}) | {{open, fixed, or not observed, with the evidence file}} | {{the TC-<nnn> or R<n> id the file gives}} |

## Coverage

Map every acceptance criterion and risk to the cases that cover it and the result the evidence shows, with one verdict per id; name below the tables any result that maps to no case.

### Acceptance criteria

One row per `AC<n>` in the brief's `## Acceptance criteria`, in order, with the cases that cover it and the result the evidence shows.

| ID | Acceptance criterion | Cases | Result | Verdict |
|---|---|---|---|---|
| {{AC1}} | {{the criterion in the brief's words}} | {{TC-001, TC-003, or none}} | {{the evidence file and what it shows, or not run}} | {{covered, partial, not run, or not covered}} |

### Risks

One row per `R<n>` in `docs/test-strategy.md` `## Risks`, or the brief's `## Known risks` when no strategy exists, naming the file the ids come from.

| ID | Risk | Cases | Result | Verdict |
|---|---|---|---|---|
| {{R1}} | {{the risk in the strategy's words}} | {{TC-002, or none}} | {{the evidence file and what it shows, or not run}} | {{covered, partial, not run, or not covered}} |

## Residual risks

One line per gap that still threatens the client, such as an id not `covered`, an open or not observed defect, a suite or count not run or not stated, an out-of-scope area, or an environment limit, with its impact and what would close it; write `None` when no gap exists.

- {{residual risk}}: {{impact on the client}}; closed by {{a case, a fix, or an owner action}}.

## Recommendation

Exactly `Go` or `No-go`, naming the rows that decide it and what would change it; a `Go` needs every acceptance criterion and high risk `covered` and no open or unobserved critical or high defect.

`{{Go or No-go}}`: {{one line naming the tables and ids that decide it, and what would change it}}.
