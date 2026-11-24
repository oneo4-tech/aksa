# Software Factory

The **Software Factory** is the mandatory process for all tracked changes to aksa. It ensures traceability, review gates, and owner control.

## Stages & Gates

| Stage | Label | Gate | Owner Action |
|-------|-------|------|--------------|
| **Triage** | `stage:triage` | — | Route to concept/define or close |
| **Concept** | `stage:concept` | **G0** | Approve feasibility verdict |
| **Define** | `stage:define` | **G1** | Approve requirement + acceptance criteria |
| **Spec** | `stage:spec` | **G2** | Approve spec (approach, interfaces, tests) |
| **Plan** | `stage:plan` | **G3** | Approve task checklist + integration branch |
| **Build** | `stage:build` | — | Verify each task (auto via `verify-task`) |
| **Ship** | `stage:ship` | — | Review & merge PR |

## Labels

Factory issues use structured labels:

### Stage Labels
- `stage:triage` → `stage:concept` → `stage:define` → `stage:spec` → `stage:plan` → `stage:build` → `stage:ship`

### Type Labels
- `type:feature` — new capability
- `type:enhancement` — improve existing
- `type:fix` — defect fix
- `type:chore` — maintenance, docs, refactor

### Size Labels
- `size:small` — one branch/PR, no spec or plan
- `size:large` — spec, plan, integration branch

### Special Labels
- `needs:owner` — factory waiting for owner decision
- `claimed` — a session is actively working on it
- `kind:factory` — marks a factory issue, added on intake

## Running a Factory Run

### As Owner (CLI)
```bash
# Start/resume a run
uv run python -m agentic.scripts.factory_issue status

# Or use the run-factory skill (via agent)
```

### As Agent (Skills)
The factory skills handle each stage:
- `triage-request` — route or close
- `define-concept` — settle decisions, feasibility (G0)
- `define-requirement` — write requirement (G1)
- `define-spec` — design spec (G2)
- `plan-tasks` — task checklist (G3)
- `implement-task` — build task test-first
- `verify-task` — independent review
- `ship-change` — merge PR
- `release-version` — tag release + changelog

## Factory Issue

The factory issue is the **single source of truth** for a run. It contains:
- Stage label (current state)
- Type + size labels
- Checklist (for build stage)
- Links to PRs, decisions, specs
- `needs:owner` when blocked

Managed by `agentic/scripts/factory_issue.py` (only writer of labels/body).

## Small vs Large Runs

| Aspect | Small (`size:small`) | Large (`size:large`) |
|--------|---------------------|---------------------|
| Spec | Skipped | Required (G2) |
| Plan | Skipped | Required (G3) |
| Branch | Single feature branch | Integration branch + task branches |
| PR | One PR | One PR per task → integration PR |
| Timeline | Hours–days | Days–weeks |

## Gates Detail

### G0: Concept Feasibility
- Open decisions settled (options, trade-offs, recommendation)
- Prototype/spike if needed (`build-prototype` skill)
- Verdict: `feasible` / `not-feasible` / `defer`

### G1: Requirement Approved
- Problem, outcome, acceptance criteria (each with test)
- Out of scope, constraints documented
- Type + size confirmed

### G2: Spec Approved
- Approach narrative
- Interfaces designed twice (alternatives compared)
- Test for each acceptance criterion
- Planning notes

### G3: Plan Approved
- Task checklist (vertical slices, checkable, one session each)
- Every acceptance criterion covered
- Integration branch created

## Verification

Each task in `build` stage:
1. `implement-task` writes failing test → implementation → passes
2. `verify-task` runs independent reviewer on diff
3. Blocking findings → one fix + one confirm pass
4. Pass → land on delivery branch, tick checklist

## Release

When `stage:ship` PR merged:
1. `release-version` proposes next SemVer (from PR labels since last tag)
2. Writes `CHANGELOG.md` section
3. Creates release PR → owner merges → tags + GitHub release