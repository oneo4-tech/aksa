# Test plan: {{client}} {{engagement}}

{{one sentence: what this plan schedules and for which scope, from the brief and the strategy}}

- Client: {{client}}
- Engagement: {{engagement}}
- Environment: {{environment}}
- Strategy: docs/test-strategy.md
- Prepared: {{date}}

## Schedule

One row per key date in the brief and per milestone the strategy and the workflow list imply; a date comes from the brief or is an open question, never an estimate.

| Milestone | Date | Basis |
|---|---|---|
| {{milestone name, such as code-freeze, environment access, execution start, exit review}} | {{the brief's key_dates value, or Q1}} | {{the key_dates field it comes from, or the open question that asks for it}} |

## Roles

One row per role the plan needs; name no person the brief does not give.

| Role | Filled by | Responsibilities | Source |
|---|---|---|---|
| {{test lead, client contact, environment owner, defect owner}} | {{owner, client, or Q1}} | {{what this role does in the plan}} | {{the brief or strategy line, or the open question}} |

## Environments

One row per environment from the strategy, with the brief's base URLs and credential variable names, never their values.

| Environment | Base URLs | Credentials variables | Access owner | Test data readiness |
|---|---|---|---|---|
| {{environment}} | {{ui_base_url and api_base_url from the brief}} | {{names from credentials_env, or none}} | {{owner, client, or Q1}} | {{ready, the source, or Q1}} |

## Deliverables

One row per workflow the engagement runs, in the step table's order: the core steps whose surface applies and the optional workflows the brief selects.

| Workflow | Artifact |
|---|---|
| {{workflow name from the step table}} | {{the artifact path the step table gives}} |

## Entry and exit criteria

State what must be true before testing starts, then one exit criterion per brief acceptance criterion.

### Entry criteria

| Criterion | Confirmed by | Milestone | Source |
|---|---|---|---|
| {{what must be ready, such as environment access and credential variables in .env}} | {{owner or client}} | {{milestone from the schedule}} | {{the strategy entry criterion it comes from}} |

### Exit criteria

| ID | Criterion | Confirmed by | Milestone |
|---|---|---|---|
| {{AC1}} | {{the brief acceptance criterion in its words}} | {{owner or client}} | {{milestone from the schedule}} |

## Risks to the plan

One row per risk to delivering this plan, with a cause the plan shows; the product risks stay in the strategy.

| ID | Risk to the plan | Cause | Impact | Likelihood | Response |
|---|---|---|---|---|---|
| P1 | {{what could delay or weaken the plan}} | {{the open question, unconfirmed date, or dependency it comes from}} | {{high, medium, or low}} | {{high, medium, or low}} | {{what the owner does about it}} |

## Open questions

One row per value the brief, the strategy, and the step table do not give, with who can answer it and what it affects; write `None` when every value is known.

| ID | Missing value | Question | Answered by | Affects |
|---|---|---|---|---|
| Q1 | {{the date, name, count, or owner the plan needs}} | {{what to ask the client or owner}} | {{client contact or owner}} | {{the milestone, role, environment, or deliverable that waits on it}} |
