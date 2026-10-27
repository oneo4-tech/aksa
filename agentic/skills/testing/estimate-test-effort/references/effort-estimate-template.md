# Effort estimate: {{client}} {{engagement}}

{{one sentence: what this estimate covers and which unit it uses, from the brief's effort_unit or the hours default}}

- Client: {{client}}
- Engagement: {{engagement}}
- Unit: {{hours or days}}{{when the brief has no effort_unit: hours (default; the brief names no effort_unit)}}
- Strategy: docs/test-strategy.md
- Plan: docs/test-plan.md
- Prepared: {{date}}

## Basis

State the unit and its source, the rule behind each range, the confidence scale, and what the estimate leaves out.

- Unit: {{hours or days}} from {{the brief's effort_unit field, or the default because the field is absent}}.
- Range rule: low is the work when every assumption holds and one pass is enough; high adds one rework pass and the time to confirm each open assumption.
- Confidence: high when the plan and strategy scope the workflow fully and every input exists; medium when one assumption is unconfirmed; low when a key assumption is unconfirmed or a needed input is absent.
- Excludes: {{client review time, environment procurement, and work outside the brief's Scope, or the exclusions that apply}}.
- Not a price and not a delivery date.

## Workflow estimates

One row per workflow in the plan's `## Deliverables`, in the plan's order, with the assumptions it rests on, a low, a high, and a confidence.

| Workflow | Scope included | Assumptions | Low | High | Confidence |
|---|---|---|---|---|---|
| {{workflow from docs/test-plan.md Deliverables}} | {{the endpoints, pages, flows, or cases it covers, from the strategy's Scope and Approach}} | {{each input that exists, the count used, one pass, and each Q<n> it depends on}} | {{number in the unit}} | {{number in the unit, above the low}} | {{high, medium, or low}} |

## Not estimated

One row per workflow the inputs do not size, with the reason and what would make it estimable; no number, and `None` when every workflow is estimated.

| Workflow | Why it cannot be estimated | What would make it estimable |
|---|---|---|
| {{workflow from the plan or a deliverable with no workflow named}} | {{the missing scope, artifact, input, or answer, by its Q<n> id}} | {{the answer, input, or plan change it needs}} |

## Totals

The sum of the estimated rows only, with every excluded workflow named.

| Total low | Total high | Workflows excluded |
|---|---|---|
| {{sum of the Low column}} | {{sum of the High column}} | {{the workflows in Not estimated, or none}} |

The total is an estimate in {{hours or days}}, not a price and not a delivery date.
