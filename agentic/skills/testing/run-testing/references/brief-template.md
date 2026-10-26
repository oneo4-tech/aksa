---
# The client or product this engagement tests.
client: Acme Analytics
# Must equal the folder name under .projects/testing/.
engagement: acme-checkout
# One or both of api, ui.
surfaces: [api, ui]
# Required when ui is in surfaces.
ui_base_url: https://app.acme.test
# Required when api is in surfaces.
api_base_url: https://api.acme.test
# Optional: a path inside this engagement folder, uncomment once the file exists.
# api_spec: specs/openapi.yaml
# Where the tests run, such as staging or a client test tenant.
environment: staging
# Optional: variable names only; their values live in this folder's .env.
credentials_env: [ACME_API_TOKEN]
# Optional: the optional workflows this engagement runs with the core steps; every other optional step is out.
# Core workflows always run and cannot be listed here. Unknown names are refused.
# workflows: [write-contract-tests, audit-accessibility, test-mobile-app]
# Optional: the unit for effort estimates, hours or days.
# effort_unit: days
# Optional: the CI platform for the pipeline. Only github-actions is supported.
# ci_platform: github-actions
# Optional: the accessibility standard to audit against, WCAG 2.1 or WCAG 2.2 at A, AA, or AAA.
# accessibility_standard: WCAG 2.2 AA
# Optional: one target per flow or endpoint.
# performance_targets:
#   product-list: p95 under 500 ms
# Optional: the devices mobile web tests emulate.
# mobile_devices: [Pixel 7, iPhone 14]
# Optional: milestone dates as YYYY-MM-DD.
# key_dates:
#   code-freeze: "2026-11-01"
---

## Background

Why the client engaged us and what the product does. Example: Acme sells subscriptions and wants its checkout tested before a pricing change.

## Scope

What this engagement tests, such as the checkout API and the payment page. Name the endpoints, pages, and flows in scope.

## Out of scope

What is explicitly not tested. Example: the admin console and third-party payment provider internals.

## Known risks

What could go wrong, in the client's words. Example: a pricing change may break cart totals for annual plans.

## Acceptance criteria

What a successful engagement looks like. Example: every checkout path has a passing API and UI test, and no open defect is above medium severity.

## Notes

- Replace every example with the engagement's facts; `engagement` must equal this file's folder name.
- The commented fields are optional and stay inert until the engagement needs them. Uncomment one only with a real value: `check` refuses a field with no value or the wrong type, an unknown or core name in `workflows`, and a selection that needs `api_spec`, `api` or `ui` in `surfaces`, `performance_targets`, or `mobile_devices`.
- `workflows` lists optional steps only, such as `write-contract-tests` or `test-mobile-app`; the core steps always run, and a workflow named on the command line runs alone.
- `credentials_env` lists variable names only. Their values live in this engagement's `.env`, never in this brief, a document, a test, or a commit.
