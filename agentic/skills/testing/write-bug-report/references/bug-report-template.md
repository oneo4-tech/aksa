# BUG-001: {{short title: the broken behaviour and where it happens}}

{{one sentence: what goes wrong, where, and who it affects, in the client's terms}}

## Severity

`{{critical, high, medium, or low}}`: {{one line naming the user, flow, data, or acceptance criterion the impact falls on}}

## Priority

`{{P1, P2, P3, or P4}}`: {{one line naming what it blocks and how soon it must be fixed}}

## Environment

{{the environment value from the brief's frontmatter}}, {{the surface, api or ui}}, {{the base URL the defect was found on, from the brief or evidence/README.md}}{{with fixture evidence: ; fixture evidence, not a run against <environment>}}

## Steps to reproduce

1. {{one action, in order, naming the page, endpoint, input, and data the evidence shows}}
2. {{next action}}

## Expected result

{{the outcome the test case, the brief's acceptance criterion, or the evidence states, in one observable sentence}}

## Actual result

{{the outcome the evidence shows, quoting its exact message, status, or value, with a credential or token value replaced by its variable name or `[redacted]`}}

## Evidence

One line per evidence file, as `evidence/{{file name}}` relative to the engagement folder: {{what the file shows for this defect, such as the failing test, its line, and the run it came from, or `fixture evidence, not a run against <environment>` when evidence/README.md or the owner says it is fixture data}}

## Impact

{{who or what the defect affects and what they cannot do: the user, the flow, the data at risk, and the acceptance criterion it blocks}}

## Traceability

{{TC-001 in docs/test-cases.md, with the AC<n> or R<n> ids in its Covers; or R1 in docs/test-strategy.md or the brief's ## Known risks section, naming the file the id comes from}}
