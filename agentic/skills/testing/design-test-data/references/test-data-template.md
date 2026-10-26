# Test data: {{client}} {{engagement}}

{{one sentence: what these fixtures supply and which cases they serve, taken from docs/test-cases.md}}

- Client: {{client}}
- Engagement: {{engagement}}
- Environment: {{environment from brief.md}}
- Cases: docs/test-cases.md
- Prepared: {{date}}

## Sources

Name where the data comes from: the brief, the cases, what already exists in the environment, and the synthetic patterns used. A data set that cites none of these is deleted.

- Brief: {{the `## Scope` and `## Acceptance criteria` statements that fix values or states}}
- Cases: {{every TC-<nnn> whose steps or preconditions name data}}
- Environment: {{what already exists in the environment, such as a product the catalogue holds, or `none`}}
- Synthetic values: {{the reserved patterns used, such as example.com addresses, `Test` names, tc-<nnn>- ids, and 192.0.2.x addresses}}

## Data sets

Write one `###` section per data set in id order. A data set is one input or state the cases share, with one fixture file except a credential or existing environment value, which has none.

### DS-001: {{short name}}

- Cases: {{TC-001, TC-003}}
- Source: {{the case step, expected result, precondition, or brief statement the values come from; say whether the value is synthetic or already in the environment}}
- Fixture: {{data/ds-001-<name>.json or .csv}} {{for a credential or environment value: none, and the reason}}
- Values: {{the values, or the `credentials_env` variable names only, never a value}}
- Edge cases: {{each boundary, empty, duplicate, missing, invalid, or maximum value the cases need, with its case id}} {{or `none stated` and the reason the cases give no boundary}}
- Cleanup: {{the delete or reset step the cases give, or `none` and why}}

## Fixture files

| File | Format | Data set | Records | Notes |
|---|---|---|---|---|
| {{data/ds-001-<name>.json}} | {{JSON or CSV}} | {{DS-001}} | {{count}} | {{one line on the shape or the reserved values}} |

## Coverage

Map every case in `docs/test-cases.md` to its data sets. A case that sends no data gets `none` and the reason, so nothing is silently left out.

| Case | Data sets |
|---|---|
| {{TC-001}} | {{DS-001 or none: the case sends no data}} |
