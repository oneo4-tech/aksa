# Test cases: {{client}} {{engagement}}

{{one sentence: what these cases cover, taken from the scope in docs/test-strategy.md}}

- Client: {{client}}
- Engagement: {{engagement}}
- Strategy: docs/test-strategy.md
- Case count: {{number of cases}}

## Sources

Name where the cases come from: the strategy's scope and the ids every case must trace to. A case that cites none of these ids is deleted.

- Scope: {{the in-scope endpoints, pages, and flows from docs/test-strategy.md}}
- Requirements: {{AC1, AC2, ... in brief.md order}}
- Risks: {{R1, R2, ... in docs/test-strategy.md order}}

## Design techniques

Give one row per technique, naming what it was applied to and the cases it produced, or write `Not applicable` and the reason the material gives no input.

| Technique | Applied to | Case IDs |
|---|---|---|
| Equivalence partitioning | {{inputs, fields, or behaviours and their valid and invalid classes}} | {{TC-001, TC-002}} |
| Boundary values | {{each range, length, count, or order and its edges}} | {{TC-003}} |
| Decision table | {{condition combinations and the outcomes they decide}} | {{TC-004}} |
| State transition | {{object, its states, and its allowed and rejected events}} | {{TC-005}} |

## Test cases

Write one `###` section per case in id order. Each section carries the technique, the ids it covers, preconditions, numbered steps, and one observable expected result.

### TC-001: {{short title}}

- Technique: {{equivalence partitioning, boundary values, decision table, or state transition}}
- Covers: {{AC1, R2}}
- Preconditions: {{starting state, data, and account, or `none`}}

1. {{one action, naming the data or input it uses}}
2. {{next action}}

**Expected result:** {{the observable outcome, with the exact value or state where the material gives one}}

## Coverage

Map every id from Sources to the cases that cover it. An id with no case gets `none` and the gap or the out-of-scope reason, so a missing case is visible.

| ID | Source | Case IDs |
|---|---|---|
| AC1 | {{brief acceptance criterion, in its words}} | {{TC-001, TC-003}} |
| R1 | {{strategy risk, in its words}} | {{TC-002 or none}} |
